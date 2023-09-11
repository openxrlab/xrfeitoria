from enum import Enum
from pathlib import Path
from typing import Optional, Tuple, TypedDict, Union

##### Typing Constants #####

Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]
Transform = Tuple[Vector, Vector, Vector]
PathLike = Union[str, Path]
actor_info_type = TypedDict('actor_info', {'actor_name': str, 'mask_color': Tuple[int, int, int]})

##### Path Constants #####

tmp_dir = Path.home() / '.tmp' / 'XRFeitoria'
tmp_dir.mkdir(parents=True, exist_ok=True)
actor_infos = 'actor_infos'
cam_param_dir = 'camera_params'

config_dir = Path.home() / '.config' / 'XRFeitoria'
config_dir.mkdir(parents=True, exist_ok=True)
config_path = config_dir / 'config.ini'
ConfigDict = TypedDict('ConfigDict', {'blender_exec': Optional[Path], 'unreal_exec': Optional[Path]})

##### Package Constants #####

plugin_name_blender = 'XRFeitoriaBpy'
plugin_name_unreal = 'XRFeitoriaUnreal'
xf_obj_name = '[XF]{obj_type}-{obj_idx:03d}'

##### Blender Constants #####

default_level_blender = 'XRFeitoria'

##### Unreal Constants #####

default_asset_path_unreal = f'/Game/{plugin_name_unreal}'
default_sequence_path_unreal = f'{default_asset_path_unreal}/Sequences'

##### Enum Constants #####


class EnumBase(str, Enum):
    """Base class for all enums, which can be accessed by name or value."""

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


class EngineEnum(Enum):
    """Render engine enum."""

    unreal = 1
    blender = 2


class ImportFileFormatEnum(EnumBase):
    """Import file format enum."""

    fbx = 'fbx'
    obj = 'obj'
    abc = 'abc'
    ply = 'ply'
    stl = 'stl'
    # TODO: Add more


class ImageFileFormatEnum(EnumBase):
    """Image file format enum."""

    png = 'PNG'
    bmp = 'BMP'
    jpg = 'JPEG'
    jpeg = 'JPEG'
    exr = 'OPEN_EXR'


class RenderOutputEnumBlender(EnumBase):
    """Render layer enum of Blender."""

    img = 'Image'
    mask = 'IndexOB'
    depth = 'Depth'
    denoising_depth = 'Denoising Depth'
    flow = 'Vector'
    normal = 'Normal'
    diffuse = 'DiffCol'

    actor_infos = f'{actor_infos}.json'
    camera_params = cam_param_dir
    # TODO: add more


class RenderOutputEnumUnreal(EnumBase):
    """Render layer enum of Unreal."""

    img = 'img'
    mask = 'mask'
    depth = 'depth'
    flow = 'optical_flow'
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
    camera_params = cam_param_dir


class InterpolationEnumUnreal(EnumBase):
    """Keyframe interpolation enum of Unreal."""

    AUTO = 'AUTO'
    LINEAR = 'LINEAR'
    CONSTANT = 'CONSTANT'


class InterpolationEnumBlender(EnumBase):
    """Keyframe interpolation enum of Blender."""

    AUTO = 'BEZIER'
    LINEAR = 'LINEAR'
    CONSTANT = 'CONSTANT'


class RenderEngineEnumBlender(EnumBase):
    """Render engine enum of Blender."""

    cycles = 'CYCLES'
    eevee = 'BLENDER_EEVEE'
    workbench = 'BLENDER_WORKBENCH'


class ShapeTypeEnumBlender(EnumBase):
    """Shape type enum of Blender."""

    cone = 'cone'
    cube = 'cube'
    cylinder = 'cylinder'
    plane = 'plane'
    sphere = 'uv_sphere'
    uv_sphere = 'uv_sphere'
    ico_sphere = 'ico_sphere'


class ShapeTypeEnumUnreal(EnumBase):
    """Shape type enum of Unreal."""

    cone = 'cone'
    cube = 'cube'
    cylinder = 'cylinder'
    plane = 'plane'
    sphere = 'sphere'
