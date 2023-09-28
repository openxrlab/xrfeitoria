from abc import ABC
from typing import List, Optional, Tuple, Union

from ..data_structure.constants import EngineEnum, PathLike, Vector
from ..data_structure.models import RenderPass, TransformKeys

class SequenceBase(ABC):
    name: str
    __platform__: EngineEnum
    @classmethod
    def _new(
        cls,
        seq_name: str,
        level: Union[str, List[str]],
        seq_fps: int = ...,
        seq_length: int = ...,
        replace: bool = ...,
        **kwargs,
    ) -> None: ...
    @classmethod
    def _open(cls, seq_name: str) -> None: ...
    @classmethod
    def close(cls) -> None: ...
    @classmethod
    def save(cls) -> None: ...
    @classmethod
    def show(cls) -> None: ...
    @classmethod
    def import_actor(
        cls,
        file_path: PathLike,
        actor_name: Optional[str] = ...,
        location: Vector = ...,
        rotation: Vector = ...,
        scale: Vector = ...,
        stencil_value: int = ...,
    ) -> ...: ...
    @classmethod
    def spawn_camera(cls, location: Vector, rotation: Vector, fov: float = ..., camera_name: str = ...) -> ...: ...
    @classmethod
    def spawn_camera_with_keys(
        cls,
        transform_keys: TransformKeys,
        fov: float = ...,
        camera_name: str = ...,
    ) -> ...: ...
    def use_camera(
        cls, camera, location: Optional[Vector] = ..., rotation: Optional[Vector] = ..., fov: float = ...
    ) -> None: ...
    @classmethod
    def use_camera_with_keys(cls, camera, transform_keys: TransformKeys, fov: float = ...) -> None: ...
    @classmethod
    def use_actor(
        cls,
        actor,
        location: Optional[Vector] = ...,
        rotation: Optional[Vector] = ...,
        scale: Optional[Vector] = ...,
        stencil_value: int = ...,
        anim_asset_path: Optional[str] = ...,
    ) -> None: ...
    @classmethod
    def use_actor_with_keys(
        cls,
        actor,
        transform_keys: TransformKeys,
        stencil_value: int = ...,
        anim_asset_path: Optional[str] = ...,
    ) -> None: ...
    @classmethod
    def spawn_shape(
        cls,
        shape_type: str,
        location: Vector = ...,
        rotation: Vector = ...,
        scale: Vector = ...,
        shape_name: str = ...,
        stencil_value: int = ...,
        **kwargs,
    ) -> ...: ...
    @classmethod
    def spawn_shape_with_keys(
        cls,
        transform_keys: TransformKeys,
        shape_type: str,
        shape_name: str = ...,
        stencil_value: int = ...,
        **kwargs,
    ) -> ...: ...
    @classmethod
    def add_to_renderer(
        cls, output_path: PathLike, resolution: Tuple[int, int], render_passes: List[RenderPass], **kwargs
    ): ...
