import datetime
import socket
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from loguru import logger

from ..constants import PathLike, RenderJobUnreal, RenderPass
from ..rpc import remote_class_unreal
from . import RendererBase

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory
except ModuleNotFoundError:
    pass


@remote_class_unreal
class RendererUnreal(RendererBase):
    render_queue: List[RenderJobUnreal] = []

    @classmethod
    def add_job(
        cls,
        map_path: str,
        sequence_path: str,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: List[RenderPass],
        file_name_format: str = "{sequence_name}/{camera_name}/{render_pass}/{frame_number}",
        console_variables: Dict[str, float] = {},
        anti_aliasing: RenderJobUnreal.AntiAliasSetting = RenderJobUnreal.AntiAliasSetting(),
    ) -> None:
        job = RenderJobUnreal(
            map_path=map_path,
            sequence_path=sequence_path,
            output_path=output_path,
            resolution=resolution,
            render_passes=render_passes,
            file_name_format=file_name_format,
            console_variables=console_variables,
            anti_aliasing=anti_aliasing,
        )
        cls._add_job_in_engine(job.model_dump())
        cls.render_queue.append(job)

    @classmethod
    def save_queue(cls, path: PathLike) -> None:
        # save queue to manifest file
        manifest_file = Path(path)  # ext: .txt
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        cls._save_queue_in_engine(path)
        logger.info(f"Queue saved at {manifest_file} as a manifest file.")

    @classmethod
    def clear(cls):
        cls._clear_queue_in_engine()
        cls.render_queue.clear()

    @classmethod
    def render_jobs(cls) -> None:
        # start render
        socket_port = cls._get_socket_port_in_engine()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", socket_port))
        server.listen(8)
        server.setblocking(False)

        cls._render_in_engine()
        conn, _ = server.accept()
        while True:
            try:
                data_size = conn.recv(4)
                data_size = int.from_bytes(data_size, "little")
                # data_size = 1024
                data = conn.recv(data_size).decode()
                if not data:
                    break
                if data == "Render completed. Success: True":
                    break
                logger.info(f"[Unreal] {data}")
            except BlockingIOError:
                pass

        # cls.clear()
        server.close()
        logger.info("Render completed.")

    @staticmethod
    def _add_job_in_engine(job: "Dict[str, Any]") -> None:
        _job = XRFeitoriaUnrealFactory.constants.RenderJobUnreal(**job)
        XRFeitoriaUnrealFactory.CustomMoviePipeline.add_job_to_queue(_job)

    @staticmethod
    def _render_in_engine() -> None:
        """
        Render the scene with default settings

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
