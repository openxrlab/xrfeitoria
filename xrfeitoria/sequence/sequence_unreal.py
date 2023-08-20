from contextlib import contextmanager
from typing import Dict, Generator, List, Optional, Union

from loguru import logger

from ..constants import SequenceTransformKey, Vector, default_sequence_path_unreal
from ..rpc import remote_class_unreal
from ..utils import unreal_functions
from .sequence_base import SequenceBase

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in XRFeitoriaUnreal/Content/Python
except ModuleNotFoundError:
    pass


def get_sequence_path(
    map_path: str,
    seq_name: str,
    seq_dir: "Optional[str]" = None,
) -> bool:
    if seq_dir is None:
        seq_dir = default_sequence_path_unreal
    seq_path = f"{seq_dir}/{seq_name}"
    unreal_functions._check_asset_in_engine(map_path)
    unreal_functions._check_asset_in_engine(seq_path)
    return seq_path


@contextmanager
def open_sequence_unreal(
    map_path: str,
    seq_name: str,
    seq_dir: "Optional[str]" = None,
) -> "Generator[SequenceUnreal, None, None]":
    if seq_dir is None:
        seq_dir = default_sequence_path_unreal
    SequenceUnreal.open_seq(
        map_path=map_path,
        seq_name=seq_name,
        seq_dir=seq_dir,
    )
    logger.info(f"opened sequence at engine path: {seq_dir}/{seq_name}")
    yield SequenceUnreal
    SequenceUnreal.save_seq()
    SequenceUnreal.close_seq()


@contextmanager
def new_sequence_unreal(
    map_path: str,
    seq_name: str,
    seq_dir: "Optional[str]" = None,
    seq_fps: "Optional[float]" = None,
    seq_length: "Optional[int]" = None,
    replace: bool = False,
) -> "Generator[SequenceUnreal, None, None]":
    if seq_dir is None:
        seq_dir = default_sequence_path_unreal
    SequenceUnreal.new_seq(
        map_path=map_path,
        seq_name=seq_name,
        seq_dir=seq_dir,
        seq_fps=seq_fps,
        seq_length=seq_length,
        replace=replace,
    )
    logger.info(f"created new sequence at engine path: {seq_dir}/{seq_name}")
    yield SequenceUnreal
    SequenceUnreal.save_seq()
    SequenceUnreal.close_seq()


@remote_class_unreal
class SequenceUnreal(SequenceBase):
    @classmethod
    def control_camera(
        cls,
        camera_name: str,
        location: "Vector",
        rotation: "Vector",
        fov: float = 90.0,
    ) -> None:
        transform_keys = dict(frame=0, location=location, rotation=rotation)
        cls._add_camera_in_engine(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )

    @classmethod
    def control_camera_with_keys(
        cls,
        camera_name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        fov: float = 90.0,
    ):
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        cls._add_camera_in_engine(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )

    @classmethod
    def control_actor(
        cls,
        actor_name: str,
        location: "Vector",
        rotation: "Vector",
        actor_stencil_value: int = 1,
        anim_asset_path: "Optional[str]" = None,
    ) -> None:
        transform_keys = dict(frame=0, location=location, rotation=rotation)
        cls._add_actor_in_engine(
            actor_name=actor_name,
            transform_keys=transform_keys,
            actor_stencil_value=actor_stencil_value,
            anim_asset_path=anim_asset_path,
        )

    @classmethod
    def control_actor_with_keys(
        cls,
        actor_name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        actor_stencil_value: int = 1,
        anim_asset_path: "Optional[str]" = None,
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        cls._add_actor_in_engine(
            actor_name=actor_name,
            transform_keys=transform_keys,
            actor_stencil_value=actor_stencil_value,
            anim_asset_path=anim_asset_path,
        )

    @classmethod
    def get_map_path(cls) -> str:
        return cls._get_map_path_in_engine()

    @classmethod
    def get_seq_path(cls) -> str:
        return cls._get_seq_path_in_engine()

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _get_map_path_in_engine() -> str:
        return XRFeitoriaUnrealFactory.Sequence.map_path

    @staticmethod
    def _get_seq_path_in_engine() -> str:
        return XRFeitoriaUnrealFactory.Sequence.sequence_path

    @staticmethod
    def _new_seq_in_engine(
        map_path: str,
        seq_name: str,
        seq_dir: "Optional[str]" = None,
        seq_fps: "Optional[float]" = None,
        seq_length: "Optional[int]" = None,
        replace: bool = False,
    ) -> None:
        XRFeitoriaUnrealFactory.Sequence.new(
            map_path=map_path,
            seq_name=seq_name,
            seq_dir=seq_dir,
            seq_fps=seq_fps,
            seq_length=seq_length,
            replace=replace,
        )

    @staticmethod
    def _open_seq_in_engine(
        map_path: str,
        seq_name: str,
        seq_dir: "Optional[str]" = None,
    ) -> None:
        XRFeitoriaUnrealFactory.Sequence.open(
            map_path=map_path,
            seq_name=seq_name,
            seq_dir=seq_dir,
        )

    @staticmethod
    def _save_seq_in_engine() -> None:
        XRFeitoriaUnrealFactory.Sequence.save()

    @staticmethod
    def _close_seq_in_engine() -> None:
        XRFeitoriaUnrealFactory.Sequence.close()

    @staticmethod
    def _show_seq_in_engine() -> None:
        XRFeitoriaUnrealFactory.Sequence.show()

    # ------ add actor and camera -------- #

    @staticmethod
    def _add_camera_in_engine(
        transform_keys: "Union[List[Dict], Dict]",
        fov: float = 90.0,
        camera_name: str = "Camera",
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        XRFeitoriaUnrealFactory.Sequence.add_camera(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )

    @staticmethod
    def _add_actor_in_engine(
        actor_name: str,
        transform_keys: "Union[List[Dict], Dict]",
        actor_stencil_value: int = 1,
        anim_asset_path: "Optional[str]" = None,
    ):
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        XRFeitoriaUnrealFactory.Sequence.add_actor(
            actor_name=actor_name,
            transform_keys=transform_keys,
            actor_stencil_value=actor_stencil_value,
            animation_asset=anim_asset_path,
        )

    # ------ spawn actor and camera ------ #

    @staticmethod
    def _spawn_camera_in_engine(
        transform_keys: "Union[List[Dict], Dict]",
        fov: float = 90.0,
        camera_name: str = "Camera",
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        XRFeitoriaUnrealFactory.Sequence.spawn_camera(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )

    @staticmethod
    def _spawn_actor_in_engine(
        actor_asset_path: str,
        transform_keys: "Union[List[Dict], Dict]",
        anim_asset_path: "Optional[str]" = None,
        actor_name: str = "Actor",
        actor_stencil_value: int = 1,
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        XRFeitoriaUnrealFactory.Sequence.spawn_actor(
            actor=actor_asset_path,
            animation_asset=anim_asset_path,
            actor_name=actor_name,
            transform_keys=transform_keys,
            actor_stencil_value=actor_stencil_value,
        )

    # cls._add_camera_in_engine(camera_name=camera_name)
