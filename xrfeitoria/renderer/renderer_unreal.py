import shutil
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from ..data_structure.constants import PathLike, RenderOutputEnumUnreal
from ..rpc import remote_unreal
from ..utils import ConverterUnreal
from ..utils.functions import unreal_functions
from .renderer_base import RendererBase, render_status

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory
except ModuleNotFoundError:
    pass

try:
    from ..data_structure.models import RenderJobUnreal as RenderJob
    from ..data_structure.models import RenderPass
except (ImportError, ModuleNotFoundError):
    pass


@remote_unreal(dec_class=True, suffix='_in_engine')
class RendererUnreal(RendererBase):
    """Renderer class for Unreal."""

    render_queue: 'List[RenderJob]' = []

    @classmethod
    def add_job(
        cls,
        map_path: str,
        sequence_path: str,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: 'List[RenderPass]',
        file_name_format: str = '{sequence_name}/{render_pass}/{camera_name}/{frame_number}',
        console_variables: Dict[str, float] = {'r.MotionBlurQuality': 0},
        anti_aliasing: 'Optional[RenderJob.AntiAliasSetting]' = None,
        export_audio: bool = False,
        export_transparent: bool = False,
    ) -> None:
        """Add a rendering job to the renderer queue.

        Args:
            map_path (str): Path to the map file.
            sequence_path (str): Path to the sequence file.
            output_path (PathLike): Path to the output folder.
            resolution (Tuple[int, int]): Resolution of the output image.
            render_passes (List[RenderPass]): Render passes to render.
            file_name_format (str, optional): File name format of the output image. Defaults to ``{sequence_name}/{render_pass}/{camera_name}/{frame_number}``.
            console_variables (Dict[str, float], optional): Console variables to set. Defaults to ``{'r.MotionBlurQuality': 0}``.
                Ref to :ref:`FAQ-console-variables` for details.
            anti_aliasing (Optional[RenderJobUnreal.AntiAliasSetting], optional): Anti aliasing setting. Defaults to None.
            export_audio (bool, optional): Whether to export audio. Defaults to False.
            export_transparent (bool, optional): Whether to export transparent images. Defaults to False. When enabled, it will reduce the performance.

        Note:
            The motion blur is turned off by default. If you want to turn it on, please set ``r.MotionBlurQuality`` to a non-zero value in ``console_variables``.
        """
        if anti_aliasing is None:
            anti_aliasing = RenderJob.AntiAliasSetting()

        # turn off motion blur by default
        if 'r.MotionBlurQuality' not in console_variables.keys():
            logger.warning(
                'Seems you gave a console variable dict in ``add_to_renderer(console_variables=...)``, '
                'and it replaces the default ``r.MotionBlurQuality`` setting, which would open the motion blur in rendering. '
                "If you want to turn off the motion blur the same as default, set ``console_variables={..., 'r.MotionBlurQuality': 0}``."
            )

        job = RenderJob(
            map_path=map_path,
            sequence_path=sequence_path,
            output_path=Path(output_path).resolve(),
            resolution=resolution,
            render_passes=render_passes,
            file_name_format=file_name_format,
            console_variables=console_variables,
            anti_aliasing=anti_aliasing,
            export_audio=export_audio,
            export_transparent=export_transparent,
        )
        cls._add_job_in_engine(job.model_dump(mode='json'))
        cls.render_queue.append(job)

    @classmethod
    def save_queue(cls, path: PathLike) -> None:
        """Saves the current render queue to a manifest file at the specified path.

        Args:
            path (PathLike): The path to save the manifest file to.
        """
        # save queue to manifest file
        manifest_file = Path(path)  # ext: .txt
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        cls._save_queue_in_engine(path)
        logger.info(f'Queue saved at {manifest_file} as a manifest file')

    @classmethod
    @render_status
    def render_jobs(cls) -> None:
        """Render all jobs in the renderer queue.

        This method starts the rendering process by setting up a socket connection with
        the Unreal Engine, rendering the all the render jobs, and then waiting for the
        engine to send a message indicating that the rendering is complete. If the
        engine crashes during the rendering process, an error message is logged and the
        program exits with an error code.

        After the rendering is complete, the renderer will perform post-processing in
        the output_path, including converting camera parameters, vertices, and
        actor_infos.

        Also, this method will clear the render queue after rendering.
        """
        if len(cls.render_queue) == 0:
            logger.warning(
                '[bold red]Skip rendering[/bold red], no render job in the queue. \n'
                ':bulb: Please add a job first via: \n'
                '>>> with xf_runner.sequence(sequence_name=...) as seq:\n'
                '...     seq.add_to_renderer(...)'
            )
            return
        # start render
        socket_port = cls._get_socket_port_in_engine()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', socket_port))
        server.listen(8)
        server.setblocking(False)

        cls._render_in_engine()
        conn, _ = server.accept()
        while True:
            try:
                data_size = conn.recv(4)
                data_size = int.from_bytes(data_size, 'little')
                # data_size = 1024
                data = conn.recv(data_size).decode()
                if not data:
                    break
                if 'Render completed. Success: True' in data:
                    break
                if 'Render completed. Success: False' in data:
                    logger.error('[red]Render Failed[/red]')
                    break
                logger.info(f'(engine) {data}')
            except BlockingIOError:
                pass
            except ConnectionResetError:
                from .. import _tls

                error_txt = '[red]Unreal Engine crashed![/red]'

                project_path = _tls.cache.get('unreal_project_path')
                if project_path is not None:
                    log_path = Path(project_path).parent / 'Saved/Logs/Pipeline.log'
                    if log_path.exists():
                        error_txt += f' Check unreal log: "{log_path.as_posix()}"'

                logger.error(error_txt)
                break

        # cls.clear()
        server.close()

        cls._post_process()

        # clear render queue
        cls.clear()

    @classmethod
    def _post_process(cls) -> None:
        """Post-processes the rendered output by:
            - converting camera parameters: from `.dat` to `.json`
            - convert actor infos: from `.dat` to `.json`
            - convert vertices: from `.dat` to `.npz`
            - convert skeleton: from `.dat` to `.npz`

        This method is called after rendering is complete.
        """
        import numpy as np  # isort:skip
        from rich import get_console  # isort:skip
        from rich.spinner import Spinner  # isort:skip
        from ..camera.camera_parameter import CameraParameter  # isort:skip

        def convert_camera(camera_file: Path) -> None:
            """Convert camera parameters from `.dat` to `.json` with `xrprimer`.

            Args:
                camera_file (Path): Path to the camera file.
            """
            cam_param = CameraParameter.from_bin(camera_file)
            cam_param.dump(camera_file.with_suffix('.json').as_posix())
            camera_file.unlink()

        def convert_actor_infos(folder: Path) -> None:
            """Convert stencil value from `.dat` to `.npz`. Merge all actor info files
            into one.

            actor_info files are in the format of:
            ```
            {
                'location': np.ndarray,  # shape: (frame, 3)
                'rotation': np.ndarray,  # shape: (frame, 3, 3)
                'stencil_value': np.ndarray,  # shape: (frame,)
                'mask_color': np.ndarray,  # shape: (frame, 3)
            }
            ```

            Args:
                folder (Path): Path to the folder containing actor info files.
            """
            # Get all files in the folder and sort them
            actor_info_files = sorted(folder.glob('*.dat'))
            if not actor_info_files:
                return
            # Read all actor info files into a list
            location = []
            rotation = []
            stencil_value = []
            mask_color = []
            for actor_info_file in actor_info_files:
                with open(actor_info_file, 'rb') as f:
                    dat = np.frombuffer(f.read(), np.float32).reshape(8)
                location.append(ConverterUnreal.location_from_ue(dat[:3]))
                rotation.append(ConverterUnreal.quat_from_ue(dat[3:7]))
                stencil_value.append(int(dat[7]))
                mask_color.append(unreal_functions.get_mask_color(int(dat[7])))

            location = np.stack(location)  # shape: (frame, 3)
            rotation = np.stack(rotation)  # shape: (frame, 3, 3)
            stencil_value = np.array(stencil_value)  # shape: (frame,)
            mask_color = np.array(mask_color)  # shape: (frame, 3)

            # Save the actor infos in a compressed `.npz` file
            np.savez_compressed(
                file=folder.with_suffix('.npz'),
                location=location,
                rotation=rotation,
                stencil_value=stencil_value,
                mask_color=mask_color,
            )
            # Remove the folder
            shutil.rmtree(folder)

        def convert_vertices(folder: Path) -> None:
            """Convert vertices from `.dat` to `.npz`. Merge all vertices files into one
            `.npz` file with structure of: {'verts': np.ndarray, 'faces': None}

            Args:
                folder (Path): Path to the folder containing vertices files.
            """
            # Get all vertices files in the folder and sort them
            vertices_files = sorted(folder.glob('*.dat'))
            if not vertices_files:
                return
            # Read all vertices files into an ndarray, shape: (frame, vertex, 3)
            vertices = np.stack(
                [
                    np.frombuffer(vertices_file.read_bytes(), np.float32).reshape(-1, 3)
                    for vertices_file in vertices_files
                ]
            )
            # Convert from ue camera space to opencv camera space convention
            vertices = ConverterUnreal.location_from_ue(vertices)
            # Save the vertices in a compressed `.npz` file
            np.savez_compressed(folder.with_suffix('.npz'), verts=vertices, faces=None)
            # Remove the folder
            shutil.rmtree(folder)

        console = get_console()
        try:
            spinner: Spinner = console._live.renderable
        except AttributeError:
            status = console.status('[bold green]:rocket: Rendering...[/bold green]')
            status.start()
            spinner: Spinner = status.renderable

        for idx, job in enumerate(cls.render_queue):
            seq_name = job.sequence_path.split('/')[-1]
            seq_path = Path(job.output_path).resolve() / seq_name
            file_name_format = job.file_name_format  # TODO: use this to rename the files
            if file_name_format != '{sequence_name}/{render_pass}/{camera_name}/{frame_number}':  # XXX: hard-coded
                logger.warning(
                    'The `file_name_format` in renderer is not the default value, which may cause some issues in post-processing. '
                )

            text = f'job {idx + 1}/{len(cls.render_queue)}: seq_name="{seq_name}", post-processing...'
            spinner.update(text=text)

            # 1. convert camera parameters from `.bat` to `.json` with xrprimer
            # TODO: remove warmup-frames?
            for camera_file in sorted(seq_path.glob(f'{RenderOutputEnumUnreal.camera_params.value}/*/*.dat')):
                convert_camera(camera_file)

            # 2. convert actor infos from `.dat` to `.json`
            for actor_info_folder in sorted(seq_path.glob(f'{RenderOutputEnumUnreal.actor_infos.value}/*')):
                convert_actor_infos(actor_info_folder)

            # 3. convert vertices from `.dat` to `.npz`
            for actor_folder in sorted(seq_path.glob(f'{RenderOutputEnumUnreal.vertices.value}/*')):
                convert_vertices(actor_folder)

            # 4. convert skeleton from `.dat` to `.json`
            for actor_folder in sorted(seq_path.glob(f'{RenderOutputEnumUnreal.skeleton.value}/*')):
                convert_vertices(actor_folder)

    @staticmethod
    def _add_job_in_engine(job: 'Dict[str, Any]') -> None:
        _job = XRFeitoriaUnrealFactory.constants.RenderJobUnreal(**job)
        XRFeitoriaUnrealFactory.CustomMoviePipeline.add_job_to_queue(_job)

    @staticmethod
    def _render_in_engine() -> None:
        """Render the scene with default settings.

        Returns:
            int: The port used to communicate with the engine
        """
        XRFeitoriaUnrealFactory.CustomMoviePipeline.render_queue()

    @staticmethod
    def _get_socket_port_in_engine() -> int:
        return XRFeitoriaUnrealFactory.CustomMoviePipeline.socket_port

    @staticmethod
    def _clear_queue_in_engine() -> None:
        XRFeitoriaUnrealFactory.CustomMoviePipeline.clear_queue()

    @staticmethod
    def _save_queue_in_engine(path: str) -> None:
        XRFeitoriaUnrealFactory.CustomMoviePipeline.save_queue(path)
