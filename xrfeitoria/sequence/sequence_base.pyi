from abc import ABC
from typing import List, Literal, Optional, Tuple, Union

from ..actor.actor_base import ActorBase
from ..camera.camera_base import CameraBase
from ..data_structure.constants import EngineEnum, PathLike, Vector
from ..data_structure.models import RenderPass, TransformKeys

class SequenceBase(ABC):
    name: str
    __platform__: EngineEnum
    @classmethod
    def _new(
        cls,
        seq_name: str,
        level: Optional[str] = None,
        seq_fps: int = 60,
        seq_length: int = 1,
        replace: bool = False,
        **kwargs,
    ) -> None: ...
    @classmethod
    def _open(cls, seq_name: str) -> None: ...
    @classmethod
    def close(cls) -> None: ...
    @classmethod
    def import_actor(
        cls,
        file_path: PathLike,
        actor_name: Optional[str] = None,
        location: Vector = None,
        rotation: Vector = None,
        scale: Vector = None,
        stencil_value: int = 1,
    ) -> ActorBase: ...
    @classmethod
    def spawn_camera(
        cls, location: Vector = None, rotation: Vector = None, fov: float = 90.0, camera_name: Optional[str] = None
    ) -> CameraBase: ...
    @classmethod
    def spawn_camera_with_keys(
        cls,
        transform_keys: TransformKeys,
        fov: float = 90.0,
        camera_name: str = None,
    ) -> CameraBase: ...
    @classmethod
    def use_camera(
        cls,
        camera: CameraBase,
        location: Optional[Vector] = None,
        rotation: Optional[Vector] = None,
        fov: float = None,
    ) -> None: ...
    @classmethod
    def use_camera_with_keys(
        cls,
        camera: CameraBase,
        transform_keys: TransformKeys,
        fov: float = None,
    ) -> None: ...
    @classmethod
    def use_actor(
        cls,
        actor: ActorBase,
        location: Optional[Vector] = None,
        rotation: Optional[Vector] = None,
        scale: Optional[Vector] = None,
        stencil_value: int = None,
        anim_asset_path: Optional[str] = None,
    ) -> None: ...
    @classmethod
    def use_actor_with_keys(
        cls,
        actor: ActorBase,
        transform_keys: TransformKeys,
        stencil_value: int = None,
        anim_asset_path: Optional[str] = None,
    ) -> None: ...
    @classmethod
    def spawn_shape(
        cls,
        type: Literal['plane', 'cube', 'sphere', 'cylinder', 'cone'],
        shape_name: str = None,
        location: Vector = None,
        rotation: Vector = None,
        scale: Vector = None,
        stencil_value: int = 1,
        **kwargs,
    ) -> ActorBase: ...
    @classmethod
    def spawn_shape_with_keys(
        cls,
        transform_keys: TransformKeys,
        type: Literal['plane', 'cube', 'sphere', 'cylinder', 'cone'],
        shape_name: str = None,
        stencil_value: int = 1,
        **kwargs,
    ) -> ActorBase: ...
    @classmethod
    def add_to_renderer(
        cls,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: List[RenderPass],
        **kwargs,
    ): ...
