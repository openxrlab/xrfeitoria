from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Type, TypeVar, Union

import bpy

default_level_blender = 'XRFeitoria'

Tuple3 = Tuple[float, float, float]
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


class DeviceTypeEnum(EnumBase):
    """Device type enum."""

    cuda = 'CUDA'
    optix = 'OPTIX'


class ImportFileFormatEnum(EnumBase):
    fbx = 'fbx'
    obj = 'obj'
    abc = 'abc'
    # TODO: Add more


class ImageFileFormatEnum(EnumBase):
    png = 'PNG'
    bmp = 'BMP'
    jpg = 'JPEG'
    jpeg = 'JPEG'
    exr = 'OPEN_EXR'
    open_exr = 'OPEN_EXR'


class RenderEngineEnum(EnumBase):
    cycles = 'CYCLES'
    eevee = 'BLENDER_EEVEE'
    workbench = 'BLENDER_WORKBENCH'


class RenderMethodEnum(EnumBase):
    default = 0
    multiview_in_step = 1
    singleview_in_step = 2


class RenderLayerEnum(EnumBase):
    """Render layer enum."""

    img = 'Image'
    mask = 'IndexOB'
    depth = 'Depth'
    denoising_depth = 'Denoising Depth'
    flow = 'Vector'
    normal = 'Normal'
    diffuse = 'DiffCol'
    # TODO: add more


class BSDFNodeLinkEnum(EnumBase):
    """Shader node link enum."""

    diffuse = 'Base Color'
    normal = 'Normal'
    roughness = 'Roughness'
    # TODO: Add more
    # specular = 'specular'
    # metallic = 'metallic'
    # emission = 'emission'
    # alpha = 'alpha'
    # ambient_occlusion = 'ambient_occlusion'


# class RenderPassesData(BaseModel):
#     render_layer: RenderLayerEnum
#     image_format: ImageFileFormatEnum


# class CameraParams(BaseModel):
#     K: Tuple[Tuple3, Tuple3, Tuple3]
#     R: Tuple[Tuple3, Tuple3, Tuple3]
#     T: Tuple3
