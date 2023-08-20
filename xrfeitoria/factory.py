from typing import Optional

from .constants import PathLike


class XRFetoriaBlender:
    def __init__(
        self,
        engine_exec: Optional[PathLike] = None,
        project_path: Optional[PathLike] = None,
        background: bool = True,
        replace_plugin: bool = False,
        new_process: bool = True,
    ) -> None:
        from .constants import RenderLayerEnumBlender

        from .object import ObjectUtilsBlender  # isort:skip
        from .camera import CameraBlender  # isort:skip
        from .actor import ActorBlender  # isort:skip
        from .actor import MeshBlender
        from .renderer import RendererBlender  # isort:skip
        from .sequence.sequence_blender import new_sequence_blender, open_sequence_blender  # isort:skip
        from .utils.runner import BlenderRPCRunner  # isort:skip
        from .utils import blender_functions

        self.RenderLayerEnum = RenderLayerEnumBlender
        self.ObjectUtils = ObjectUtilsBlender
        self.Camera = CameraBlender
        self.Actor = ActorBlender
        self.Mesh = MeshBlender
        self.Renderer = RendererBlender
        self.new_seq = new_sequence_blender
        self.open_seq = open_sequence_blender
        self.utils = blender_functions
        self._rpc_runner = BlenderRPCRunner(
            engine_exec=engine_exec,
            project_path=project_path,
            replace_plugin=replace_plugin,
            background=background,
            new_process=new_process,
        )
        # TODO; check this
        self.scene_name = "Scene"


class XRFeitoriaUnreal:
    def __init__(
        self,
        engine_exec: Optional[PathLike] = None,
        project_path: Optional[PathLike] = None,
        background: bool = True,
        replace_plugin: bool = False,
        new_process: bool = True,
    ) -> None:
        from .constants import RenderLayerEnumUnreal

        from .object import ObjectUtilsUnreal  # isort:skip
        from .camera import CameraUnreal  # isort:skip
        from .actor import ActorUnreal  # isort:skip
        from .renderer import RendererUnreal  # isort:skip
        from .sequence import new_sequence_unreal, open_sequence_unreal, get_sequence_path  # isort:skip
        from .utils.runner import UnrealRPCRunner  # isort:skip

        self.RenderLayerEnum = RenderLayerEnumUnreal
        self.ObjectUtils = ObjectUtilsUnreal
        self.Camera = CameraUnreal
        self.Actor = ActorUnreal
        self.Renderer = RendererUnreal
        self.new_seq = new_sequence_unreal
        self.open_seq = open_sequence_unreal
        self.get_seq_path = get_sequence_path
        self._rpc_runner = UnrealRPCRunner(
            engine_exec=engine_exec,
            project_path=project_path,
            replace_plugin=replace_plugin,
            background=background,
            new_process=new_process,
        )
