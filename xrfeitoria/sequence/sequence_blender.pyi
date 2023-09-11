from pathlib import Path as Path
from typing import List, Literal, Optional, Tuple, Union

from ..actor.actor_blender import ActorBlender
from ..camera.camera_blender import CameraBlender
from ..data_structure.constants import PathLike, RenderEngineEnumBlender, Vector
from ..data_structure.models import RenderPass, TransformKeys
from .sequence_base import SequenceBase

class SequenceBlender(SequenceBase):
    @classmethod
    def use_camera(cls, camera: CameraBlender): ...
    @classmethod
    def import_actor(
        cls,
        file_path: PathLike,
        actor_name: Optional[str] = ...,
        location: Vector = ...,
        rotation: Vector = ...,
        scale: Vector = ...,
        stencil_value: int = ...,
    ) -> ActorBlender: ...
    @classmethod
    def import_actor_with_keys(
        cls,
        file_path: PathLike,
        transform_keys: TransformKeys,
        actor_name: str = ...,
        stencil_value: int = ...,
    ) -> ActorBlender: ...
    @classmethod
    def spawn_camera(
        cls, location: Vector, rotation: Vector, fov: float = ..., camera_name: str = ...
    ) -> CameraBlender: ...
    @classmethod
    def spawn_camera_with_keys(
        cls,
        transform_keys: TransformKeys,
        fov: float = ...,
        camera_name: str = ...,
    ) -> CameraBlender: ...
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
    ) -> ActorBlender: ...
    @classmethod
    def spawn_shape_with_keys(
        cls,
        transform_keys: TransformKeys,
        shape_type: str,
        shape_name: str = ...,
        stencil_value: int = ...,
        **kwargs,
    ) -> ActorBlender: ...
    @classmethod
    def add_to_renderer(
        cls,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: 'List[RenderPass]',
        render_engine: Union[RenderEngineEnumBlender, Literal['cycles', 'eevee', 'workbench']] = 'cycles',
        render_samples: int = 128,
        transparent_background: bool = False,
        arrange_file_structure: bool = True,
    ): ...
