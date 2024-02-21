import socket
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from ..data_structure.constants import PathLike
from ..rpc import remote_unreal
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

        # clear render queue
        cls.clear()

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
