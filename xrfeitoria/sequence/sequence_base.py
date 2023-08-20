from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from ..constants import SequenceTransformKey, Vector


class SequenceBase(ABC):
    @classmethod
    def new_seq(cls, *args, **kwargs) -> None:
        cls._new_seq_in_engine(*args, **kwargs)

    @classmethod
    def open_seq(cls, *args, **kwargs) -> None:
        cls._open_seq_in_engine(*args, **kwargs)

    @classmethod
    def close_seq(cls) -> None:
        cls._close_seq_in_engine()

    @classmethod
    def save_seq(cls) -> None:
        cls._save_seq_in_engine()

    @classmethod
    def show(cls) -> None:
        cls._show_seq_in_engine()

    # ------ spawn actor and camera ------ #

    @classmethod
    def spawn_camera(
        cls,
        location: "Vector",
        rotation: "Vector",
        fov: float = 90.0,
        camera_name: str = "Camera",
    ) -> None:
        transform_keys = dict(frame=0, location=location, rotation=rotation)
        cls._spawn_camera_in_engine(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )

    @classmethod
    def spawn_camera_with_keys(
        cls,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        fov: float = 90.0,
        camera_name: str = "Camera",
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        cls._spawn_camera_in_engine(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )

    @classmethod
    def spawn_actor(
        cls,
        actor_asset_path: str,
        location: "Vector",
        rotation: "Vector",
        actor_name: str = "Actor",
        actor_stencil_value: int = 1,
        anim_asset_path: "Optional[str]" = None,
    ) -> None:
        transform_keys = dict(frame=0, location=location, rotation=rotation)
        cls._spawn_actor_in_engine(
            actor_asset_path=actor_asset_path,
            transform_keys=transform_keys,
            anim_asset_path=anim_asset_path,
            actor_name=actor_name,
            actor_stencil_value=actor_stencil_value,
        )

    @classmethod
    def spawn_actor_with_keys(
        cls,
        actor_asset_path: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        actor_name: str = "Actor",
        actor_stencil_value: int = 1,
        anim_asset_path: "Optional[str]" = None,
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        cls._spawn_actor_in_engine(
            actor_asset_path=actor_asset_path,
            transform_keys=transform_keys,
            anim_asset_path=anim_asset_path,
            actor_name=actor_name,
            actor_stencil_value=actor_stencil_value,
        )

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    @abstractmethod
    def _spawn_camera_in_engine(
        transform_keys: "Union[List[Dict], Dict]",
        fov: float = 90.0,
        camera_name: str = "Camera",
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _spawn_actor_in_engine(
        actor_asset_path: str,
        transform_keys: "Union[List[Dict], Dict]",
        anim_asset_path: "Optional[str]" = None,
        actor_name: str = "Actor",
        actor_stencil_value: int = 1,
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _new_seq_in_engine(*args, **kwargs) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _open_seq_in_engine(*args, **kwargs) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _close_seq_in_engine() -> None:
        pass

    @staticmethod
    @abstractmethod
    def _save_seq_in_engine() -> None:
        pass

    @staticmethod
    @abstractmethod
    def _show_seq_in_engine() -> None:
        pass
