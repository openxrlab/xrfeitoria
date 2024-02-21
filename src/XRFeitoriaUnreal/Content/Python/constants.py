from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import unreal

######### Engine Constants #########


def get_plugin_path() -> Tuple[Path, Path, Path]:
    PROJECT_FILE = Path(unreal.Paths.get_project_file_path()).resolve()
    PROJECT_ROOT = PROJECT_FILE.parent
    PLUGIN_ROOT = PROJECT_ROOT / 'Plugins' / PLUGIN_NAME
    PLUGIN_PYTHON_ROOT = PLUGIN_ROOT / 'Content/Python'

    return PROJECT_ROOT, PLUGIN_ROOT, PLUGIN_PYTHON_ROOT


PLUGIN_NAME = 'XRFeitoriaUnreal'
MATERIAL_PATHS = {
    'depth': f'/{PLUGIN_NAME}/Materials/MRQ/PPM_depth_EXR',
    'mask': f'/{PLUGIN_NAME}/Materials/MRQ/PPM_mask_MRQ',
    'flow': f'/{PLUGIN_NAME}/Materials/PPM_velocity',
    'diffuse': f'/{PLUGIN_NAME}/Materials/PPM_diffusecolor',
    'normal': f'/{PLUGIN_NAME}/Materials/PPM_normal_map',
    'metallic': f'/{PLUGIN_NAME}/Materials/PPM_metallic',
    'roughness': f'/{PLUGIN_NAME}/Materials/PPM_roughness',
    'specular': f'/{PLUGIN_NAME}/Materials/PPM_specular',
    'tangent': f'/{PLUGIN_NAME}/Materials/PPM_tangent',
    'basecolor': f'/{PLUGIN_NAME}/Materials/PPM_basecolor',
}
SHAPE_PATHS = {
    'cube': '/Engine/BasicShapes/Cube',
    'sphere': '/Engine/BasicShapes/Sphere',
    'cylinder': '/Engine/BasicShapes/Cylinder',
    'cone': '/Engine/BasicShapes/Cone',
    'plane': '/Engine/BasicShapes/Plane',
}
PROJECT_ROOT, PLUGIN_ROOT, PLUGIN_PYTHON_ROOT = get_plugin_path()
ENGINE_MAJOR_VERSION = int(unreal.SystemLibrary.get_engine_version().split('.')[0])
ENGINE_MINOR_VERSION = int(unreal.SystemLibrary.get_engine_version().split('.')[1])
DEFAULT_PATH = f'/Game/{PLUGIN_NAME}'
DEFAULT_SEQUENCE_PATH = f'{DEFAULT_PATH}/Sequences'
DEFAULT_ASSET_PATH = f'{DEFAULT_PATH}/Assets'
DEFAULT_SEQUENCE_DATA_ASSET = f'/{PLUGIN_NAME}/DefaultSequenceData'
MRQ_JOB_UPPER = 200
data_asset_suffix = '_data'


class SubSystem:
    if ENGINE_MAJOR_VERSION == 5:
        EditorActorSub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        EditorLevelSub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        EditorSub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        EditorLevelSequenceSub = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
        EditorAssetSub = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
        MoviePipelineQueueSub = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    else:
        EditorActorSub = None
        EditorLevelSub = None
        EditorSub = None
        EditorLevelSequenceSub = None
        EditorAssetSub = None
        MoviePipelineQueueSub = None


######### Typing Constants #########

Vector = Tuple[float, float, float]
PathLike = Union[str, Path]


class EnumBase(str, Enum):
    @classmethod
    def get(cls, name_or_value: str) -> 'EnumBase':
        """Get enum member by name or value.

        Args:
            name_or_value (str): Name or value of the enum member.

        Returns:
            EnumBase: Self
        """
        try:
            return cls[name_or_value]
        except KeyError:
            for member in cls:
                if member.value == name_or_value:
                    return member
            raise ValueError(f'{name_or_value} is not supported in {cls.__name__}')


class InterpolationEnum(EnumBase):
    AUTO = 'AUTO'
    LINEAR = 'LINEAR'
    CONSTANT = 'CONSTANT'


class ImageFileFormatEnum(EnumBase):
    png = 'PNG'
    bmp = 'BMP'
    jpg = 'JPEG'
    jpeg = 'JPEG'
    exr = 'EXR'
    open_exr = 'EXR'


class UnrealRenderLayerEnum(EnumBase):
    """Render layer enum of Unreal."""

    img = 'img'
    mask = 'mask'
    depth = 'depth'
    flow = 'flow'
    normal = 'normal'
    diffuse = 'diffuse'

    metallic = 'metallic'
    roughness = 'roughness'
    specular = 'specular'
    tangent = 'tangent'
    basecolor = 'basecolor'

    vertices = 'vertices'
    skeleton = 'skeleton'
    actor_infos = 'actor_infos'
    camera_params = 'camera_params'
    audio = 'Audio'


@dataclass
class RenderPass:
    """Render pass model."""

    render_layer: UnrealRenderLayerEnum
    image_format: ImageFileFormatEnum

    def __post_init__(self):
        if isinstance(self.render_layer, str):
            self.render_layer = UnrealRenderLayerEnum.get(self.render_layer.lower())
        if isinstance(self.image_format, str):
            self.image_format = ImageFileFormatEnum.get(self.image_format.lower())


@dataclass
class SequenceTransformKey:
    frame: int
    location: Optional[Vector] = None
    rotation: Optional[Vector] = None
    scale: Optional[Vector] = None
    interpolation: InterpolationEnum = InterpolationEnum.CONSTANT

    def __post_init__(self):
        if not isinstance(self.frame, int):
            raise ValueError('Frame must be an integer')
        if self.location and (not isinstance(self.location, (tuple, list)) or len(self.location) != 3):
            raise ValueError('Location must be a tuple of 3 floats')
        if self.rotation and (not isinstance(self.rotation, (tuple, list)) or len(self.rotation) != 3):
            raise ValueError('Rotation must be a tuple of 3 floats')
        if self.scale and (not isinstance(self.scale, (tuple, list)) or len(self.scale) != 3):
            raise ValueError('Scale must be a tuple of 3 floats')
        if isinstance(self.interpolation, str):
            self.interpolation = InterpolationEnum.get(self.interpolation.upper())

        if self.location:
            # convert meters to centimeters
            self.location = [loc * 100.0 for loc in self.location]


@dataclass
class RenderJobUnreal:
    @dataclass
    class AntiAliasSetting:
        enable: bool = False
        override_anti_aliasing: bool = False
        spatial_samples: int = 8
        temporal_samples: int = 8
        warmup_frames: int = 0
        render_warmup_frame: bool = False

    map_path: str
    sequence_path: str

    output_path: str
    resolution: Tuple[int, int]
    render_passes: List[RenderPass]
    file_name_format: str = '{sequence_name}/{render_pass}/{camera_name}/{frame_number}'
    console_variables: Dict[str, float] = field(default_factory=dict)
    anti_aliasing: AntiAliasSetting = AntiAliasSetting()
    export_audio: bool = False

    def __post_init__(self):
        self.render_passes = [RenderPass(**rp) for rp in self.render_passes]
        self.anti_aliasing = self.AntiAliasSetting(**self.anti_aliasing)


TransformKeys = Union[List[SequenceTransformKey], SequenceTransformKey]
MotionFrame = Dict[str, Dict[str, Union[float, List[float]]]]
