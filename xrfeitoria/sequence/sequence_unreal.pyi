from typing import Dict, List, Optional, Tuple

from ..actor.actor_unreal import ActorUnreal as ActorUnreal
from ..camera.camera_unreal import CameraUnreal as CameraUnreal
from ..data_structure.constants import PathLike as PathLike
from ..data_structure.constants import Vector as Vector
from ..data_structure.models import RenderJobUnreal as RenderJobUnreal
from ..data_structure.models import RenderPass as RenderPass
from ..data_structure.models import TransformKeys as TransformKeys
from ..object.object_utils import ObjectUtilsUnreal as ObjectUtilsUnreal
from ..renderer.renderer_unreal import RendererUnreal as RendererUnreal
from ..rpc import remote_unreal as remote_unreal
from ..utils.functions import unreal_functions as unreal_functions
from .sequence_base import SequenceBase as SequenceBase

class SequenceUnreal(SequenceBase):
    @classmethod
    def add_to_renderer(
        cls,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: List[RenderPass],
        file_name_format: str = ...,
        console_variables: Dict[str, float] = ...,
        anti_aliasing: 'Optional[RenderJobUnreal.AntiAliasSetting]' = ...,
        export_vertices: bool = ...,
        export_skeleton: bool = ...,
    ) -> None: ...
    @classmethod
    def spawn_camera(
        cls, location: Vector, rotation: Vector, fov: float = ..., camera_name: str = ...
    ) -> CameraUnreal: ...
    @classmethod
    def spawn_actor(
        cls,
        actor_asset_path: str,
        location: Vector,
        rotation: Vector,
        scale: Optional[Vector] = ...,
        actor_name: Optional[str] = ...,
        stencil_value: int = ...,
        anim_asset_path: Optional[str] = ...,
    ) -> ActorUnreal: ...
    @classmethod
    def spawn_actor_with_keys(
        cls,
        actor_asset_path: str,
        transform_keys: TransformKeys,
        actor_name: Optional[str] = ...,
        stencil_value: int = ...,
        anim_asset_path: Optional[str] = ...,
    ) -> ActorUnreal: ...
    @classmethod
    def use_camera(
        cls, camera: CameraUnreal, location: Optional[Vector] = ..., rotation: Optional[Vector] = ..., fov: float = ...
    ) -> None: ...
    @classmethod
    def use_camera_with_keys(
        cls, camera: CameraUnreal, transform_keys: TransformKeys, fov: float = ...
    ) -> CameraUnreal: ...
    @classmethod
    def use_actor(
        cls,
        actor: ActorUnreal,
        location: Optional[Vector] = ...,
        rotation: Optional[Vector] = ...,
        scale: Optional[Vector] = ...,
        stencil_value: int = ...,
        anim_asset_path: Optional[str] = ...,
    ) -> None: ...
    @classmethod
    def use_actor_with_keys(
        cls,
        actor: ActorUnreal,
        transform_keys: TransformKeys,
        stencil_value: int = ...,
        anim_asset_path: Optional[str] = ...,
    ) -> None: ...
    @classmethod
    def get_map_path(cls) -> str: ...
    @classmethod
    def get_seq_path(cls) -> str: ...
