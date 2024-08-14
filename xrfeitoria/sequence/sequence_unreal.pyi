from typing import Dict, List, Literal, Optional, Tuple, Union

from typing_extensions import TypedDict

from ..actor.actor_unreal import ActorUnreal
from ..camera.camera_unreal import CameraUnreal
from ..data_structure.constants import MotionFrame, PathLike, Vector
from ..data_structure.models import RenderJobUnreal, RenderPass, TransformKeys
from ..object.object_utils import ObjectUtilsUnreal
from ..renderer.renderer_unreal import RendererUnreal
from .sequence_base import SequenceBase

class dict_process_dir(TypedDict):
    camera_dir: str
    actor_infos_dir: str
    vertices_dir: str
    skeleton_dir: str

class SequenceUnreal(SequenceBase):
    _actor = ActorUnreal
    _camera = CameraUnreal
    _object_utils = ObjectUtilsUnreal
    _renderer = RendererUnreal
    @classmethod
    def save(cls) -> None: ...
    @classmethod
    def show(cls) -> None: ...
    @classmethod
    def add_to_renderer(
        cls,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: List[RenderPass],
        file_name_format: str = '{sequence_name}/{render_pass}/{camera_name}/{frame_number}',
        console_variables: Dict[str, float] = {'r.MotionBlurQuality': 0},
        anti_aliasing: Optional[RenderJobUnreal.AntiAliasSetting] = None,
        export_vertices: bool = False,
        export_skeleton: bool = False,
        export_audio: bool = False,
        export_transparent: bool = False,
    ) -> None: ...
    @classmethod
    def spawn_actor(
        cls,
        actor_asset_path: str,
        location: Optional[Vector] = None,
        rotation: Optional[Vector] = None,
        scale: Optional[Vector] = None,
        actor_name: Optional[str] = None,
        stencil_value: int = 1,
        anim_asset_path: Optional[str] = None,
        motion_data: Optional[List[MotionFrame]] = None,
    ) -> ActorUnreal: ...
    @classmethod
    def spawn_actor_with_keys(
        cls,
        actor_asset_path: str,
        transform_keys: TransformKeys,
        actor_name: Optional[str] = None,
        stencil_value: int = 1,
        anim_asset_path: Optional[str] = None,
        motion_data: Optional[List[MotionFrame]] = None,
    ) -> ActorUnreal: ...
    @classmethod
    def add_audio(
        cls, audio_asset_path: str, start_frame: Optional[int] = None, end_frame: Optional[int] = None
    ) -> None: ...
    @classmethod
    def get_map_path(cls) -> str: ...
    @classmethod
    def get_seq_path(cls) -> str: ...
    @classmethod
    def set_playback(cls, start_frame: Optional[int] = None, end_frame: Optional[int] = None) -> None: ...
    @classmethod
    def get_playback(cls) -> Tuple[int, int]: ...
    @classmethod
    def set_camera_cut_playback(cls, start_frame: Optional[int] = None, end_frame: Optional[int] = None) -> None: ...
    @classmethod
    def _open(cls, seq_name: str, seq_dir: Optional[str] = None) -> None: ...
    @classmethod
    def _preprocess_before_render(
        cls, save_dir: str, resolution: Tuple[int, int], export_vertices: bool, export_skeleton: bool
    ) -> None: ...
    @staticmethod
    def _get_default_seq_dir_in_engine() -> str: ...
    @staticmethod
    def _get_seq_info_in_engine(
        seq_name: str, seq_dir: Optional[str] = None, map_path: Optional[str] = None
    ) -> Tuple[str, str]: ...
    @staticmethod
    def _get_map_path_in_engine() -> str: ...
    @staticmethod
    def _get_seq_path_in_engine() -> str: ...
