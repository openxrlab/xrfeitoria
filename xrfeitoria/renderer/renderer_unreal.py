import json
import shutil
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from ..data_structure.constants import PathLike, RenderOutputEnumUnreal, actor_info_type
from ..rpc import remote_unreal
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
except ModuleNotFoundError:
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
        console_variables: Dict[str, float] = {},
        anti_aliasing: 'Optional[RenderJob.AntiAliasSetting]' = None,
        export_vertices: bool = False,
        export_skeleton: bool = False,
    ) -> None:
        """Add a rendering job to the renderer queue.

        Args:
            map_path (str): Path to the map file.
            sequence_path (str): Path to the sequence file.
            output_path (PathLike): Path to the output folder.
            resolution (Tuple[int, int]): Resolution of the output image.
            render_passes (List[RenderPass]): Render passes to render.
            file_name_format (str, optional): File name format of the output image. Defaults to ``{sequence_name}/{render_pass}/{camera_name}/{frame_number}``.
            console_variables (Dict[str, float], optional): Console variables to set. Defaults to {}.
                Ref to :ref:`FAQ-console-variables` for details.
            anti_aliasing (Optional[RenderJob.AntiAliasSetting], optional): Anti aliasing setting. Defaults to None.
            export_vertices (bool, optional): Whether to export vertices. Defaults to False.
            export_skeleton (bool, optional): Whether to export skeleton. Defaults to False.
        """
        if anti_aliasing is None:
            anti_aliasing = RenderJob.AntiAliasSetting()

        job = RenderJob(
            map_path=map_path,
            sequence_path=sequence_path,
            output_path=Path(output_path).resolve(),
            resolution=resolution,
            render_passes=render_passes,
            file_name_format=file_name_format,
            console_variables=console_variables,
            anti_aliasing=anti_aliasing,
            export_vertices=export_vertices,
            export_skeleton=export_skeleton,
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
        the Unreal Engine, rendering the scene, and then waiting for the engine to send
        a message indicating that the rendering is complete. If the engine crashes
        during the rendering process, an error message is logged and the program exits
        with an error code.

        After the rendering is complete, the renderer will perform post-processing in
        the output_path, including converting camera parameters, vertices, and
        actor_infos.
        """
        if len(cls.render_queue) == 0:
            logger.warning(
                '[bold red]Skip rendering[/bold red], no render job in the queue. \n'
                ':bulb: Please add a job first via: \n'
                '>>> with xf_runner.Sequence.open(sequence_name=...) as seq:\n'
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
                logger.info(f'\[unreal] {data}')
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
                exit(1)

        # cls.clear()
        server.close()

        # post process, including: convert cam params.
        cls._post_process()

    @classmethod
    def _post_process(cls) -> None:
        import numpy as np  # isort:skip
        from ..camera.camera_parameter import CameraParameter  # isort:skip

        def convert_camera(camera_file: Path) -> None:
            """Convert camera parameters from `.dat` to `.json` with `xrprimer`.

            Args:
                camera_file (Path): Path to the camera file.
            """
            cam_param = CameraParameter.from_bin(camera_file)
            cam_param.dump(camera_file.with_suffix('.json').as_posix())
            camera_file.unlink()

        def convert_vertices(folder: Path) -> None:
            """Convert vertices from `.bin` to `.npz`. Merge all vertices files into one
            `.npz` file.

            Args:
                folder (Path): Path to the folder containing vertices files.
            """
            # Get all vertices files in the folder and sort them
            vertices_files = sorted(folder.glob('*.dat'))
            # Read all vertices files into a list
            vertices = [
                np.frombuffer(vertices_file.read_bytes(), np.float32).reshape(-1, 3) for vertices_file in vertices_files
            ]
            if not vertices:
                return

            # Stack all vertices into one array with shape (frame, verts, 3)
            vertices = np.stack(vertices)
            # Convert convention from unreal to opencv, [x, y, z] -> [y, -z, x]
            vertices = np.stack([vertices[:, :, 1], -vertices[:, :, 2], vertices[:, :, 0]], axis=-1)
            vertices /= 100  # convert from cm to m

            # Save the vertices in a compressed `.npz` file
            np.savez_compressed(folder.with_suffix('.npz'), verts=vertices, faces=None)
            # Remove the folder
            shutil.rmtree(folder)

        def convert_actor_infos(folder: Path) -> None:
            """Convert stencil value from `.dat` to `.json`.

            Args:
                folder (Path): Path to the folder contains ``actor_infos``.
            """
            # Get all stencil value files in the folder and sort them
            actor_info_files = sorted(folder.glob('*.dat'))
            # Read all actor info files into a list
            actor_infos: List[actor_info_type] = []
            for actor_info_file in actor_info_files:
                stencil_value = np.frombuffer(actor_info_file.read_bytes(), np.float32)
                stencil_value = int(stencil_value)
                mask_color = unreal_functions.get_mask_color(stencil_value)
                actor_infos.append({'actor_name': actor_info_file.stem, 'mask_color': mask_color})

            if not actor_infos:
                return

            # Save the actor infos in a `.json` file
            with (folder.parent / f'{folder.name}.json').open('w') as f:
                json.dump(actor_infos, f, indent=4)

            # Remove the folder
            shutil.rmtree(folder)

        for job in cls.render_queue:
            seq_name = job.sequence_path.split('/')[-1]
            seq_path = Path(job.output_path).resolve() / seq_name

            # 1. convert camera parameters from `.bat` to `.json` with xrprimer
            # glob camera files in {seq_path}/{cam_param_dir}/*
            camera_files = sorted(seq_path.glob(f'{RenderOutputEnumUnreal.camera_params.value}/*.dat'))
            for camera_file in camera_files:
                convert_camera(camera_file)

            # 2. convert actor infos from `.dat` to `.json`
            convert_actor_infos(folder=seq_path / RenderOutputEnumUnreal.actor_infos.value)

            # 3. convert vertices from `.bin` to `.npz`
            if job.export_vertices:
                # glob actors in {seq_path}/vertices/*
                actor_folders = sorted(seq_path.glob(f'{RenderOutputEnumUnreal.vertices.value}/*'))
                for actor_folder in actor_folders:
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
