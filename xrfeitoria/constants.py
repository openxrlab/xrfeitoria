from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from pydantic import BaseModel

##### Enum Constants #####


class EnumBase(str, Enum):
    @classmethod
    def get(cls, name_or_value: str) -> "EnumBase":
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
            raise ValueError(f"{name_or_value} is not supported in {cls.__name__}")


class PlatformEnum(Enum):
    null = 0
    unreal = 1
    blender = 2


class ImportFileFormatEnum(EnumBase):
    fbx = "fbx"
    obj = "obj"
    abc = "abc"
    # TODO: Add more


class ImageFileFormatEnum(EnumBase):
    png = "PNG"
    bmp = "BMP"
    jpg = "JPEG"
    jpeg = "JPEG"
    exr = "OPEN_EXR"


class RenderLayerEnumBlender(EnumBase):
    """Render layer enum of Blender"""

    img = "Image"
    mask = "IndexOB"
    depth = "Depth"
    denoising_depth = "Denoising Depth"
    flow = "Vector"
    normal = "Normal"
    diffuse = "DiffCol"
    # TODO: add more


class RenderLayerEnumUnreal(EnumBase):
    """Render layer enum of Unreal"""

    img = "rgb"
    mask = "mask"
    depth = "depth"
    flow = "optical_flow"
    normal = "normal"
    diffuse = "diffuse"

    metallic = "metallic"
    roughness = "roughness"
    specular = "specular"
    tangent = "tangent"
    basecolor = "basecolor"


class InterpolationEnumUnreal(EnumBase):
    CUBIC = "AUTO"
    LINEAR = "LINEAR"
    CONSTANT = "CONSTANT"


class InterpolationEnumBlender(EnumBase):
    CUBIC = "BEZIER"
    LINEAR = "LINEAR"
    CONSTANT = "CONSTANT"


class RenderEngineEnumBlender(EnumBase):
    cycles = "CYCLES"
    eevee = "BLENDER_EEVEE"
    workbench = "BLENDER_WORKBENCH"


# class BlenderMeshTypeEnum(EnumBase):
#     plane = "plane"
#     cube = "cube"
#     uv_sphere = "uv_sphere"
#     ico_sphere = "ico_sphere"
#     cylinder = "cylinder"
#     cone = "cone"


##### Typing Constants #####

Vector = Tuple[float, float, float]
Transform = Tuple[Vector, Vector, Vector]
PathLike = TypeVar("PathLike", str, Path)


class RenderPass(BaseModel):
    """Render pass model"""

    render_layer: Union[RenderLayerEnumBlender, RenderLayerEnumUnreal, str]
    image_format: Union[ImageFileFormatEnum, str]

    def __init__(
        self,
        render_layer: Union[RenderLayerEnumBlender, RenderLayerEnumUnreal, str],
        image_format: Union[ImageFileFormatEnum, str],
    ) -> None:
        """
        Render pass for Unreal or Blender, which contains render layer and image format.

        Args:
            render_layer (Union[RenderLayerEnumBlender, RenderLayerEnumUnreal, str]):
                Render layer of Unreal or Blender. Should be one of the following enum, or the string of it:
                    `RenderLayerEnumBlender`: `img`, `mask`, `depth`, `denoising_depth`, `flow`, `normal`, `diffuse` \n
                    `RenderLayerEnumUnreal`: `img`, `mask`
            image_format (Union[ImageFileFormatEnum, str]):
                Image format of Unreal or Blender.  Should be element of the enum, or the string of it:
                    `ImageFileFormatEnum`: `png`, `bmp`, `jpg`, `jpeg`, `exr`
        """
        from . import __platform__

        assert __platform__.value, "xrfeitoria.init_blender() or xrfeitoria.init_unreal() must be called first"

        if isinstance(image_format, str):
            image_format = ImageFileFormatEnum.get(image_format.lower())

        if __platform__ == PlatformEnum.unreal:
            if isinstance(render_layer, str):
                render_layer = RenderLayerEnumUnreal.get(render_layer.lower())
            elif isinstance(render_layer, RenderEngineEnumBlender):
                raise ValueError("Unreal does not support Blender render layer")
            super().__init__(
                render_layer=render_layer,
                image_format=image_format,
            )

        elif __platform__ == PlatformEnum.blender:
            if isinstance(render_layer, str):
                render_layer = RenderLayerEnumBlender.get(render_layer.lower())
            elif isinstance(render_layer, RenderLayerEnumUnreal):
                raise ValueError("Blender does not support Unreal render layer")
            super().__init__(
                render_layer=render_layer,
                image_format=image_format,
            )

    class Config:
        use_enum_values = True


class RenderJobBlender(BaseModel):
    sequence_name: str

    output_path: str
    resolution: Tuple[int, int]
    render_passes: List[RenderPass]
    render_engine: Union[RenderEngineEnumBlender, str]
    render_samples: int
    hdr_map_path: Optional[str] = None
    transparent_background: bool = False
    arrange_file_structure: bool = True

    def __init__(self, render_engine: str, *args, **kwargs) -> None:
        if isinstance(render_engine, str):
            render_engine = RenderEngineEnumBlender.get(render_engine.lower())
        super().__init__(render_engine=render_engine, *args, **kwargs)


class RenderJobUnreal(BaseModel):
    class AntiAliasSetting(BaseModel):
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
    file_name_format: str = "{sequence_name}/{camera_name}/{render_pass}/{frame_number}"
    console_variables: Dict[str, float] = {}
    anti_aliasing: AntiAliasSetting = AntiAliasSetting()

    class Config:
        use_enum_values = True


class SequenceTransformKey(BaseModel):
    frame: int
    location: Vector
    rotation: Vector
    scale: Vector = (1, 1, 1)
    interpolation: Union[InterpolationEnumUnreal, InterpolationEnumBlender]

    def __init__(
        self, frame: int, location: Vector, rotation: Vector, scale: Vector = (1, 1, 1), interpolation: str = "CONSTANT"
    ) -> None:
        from . import __platform__

        assert __platform__.value, "xrfeitoria.init_blender() or xrfeitoria.init_unreal() must be called first"

        if __platform__ == PlatformEnum.unreal:
            if isinstance(interpolation, str):
                interpolation = InterpolationEnumUnreal.get(interpolation.upper())
            elif isinstance(interpolation, InterpolationEnumBlender):
                interpolation = InterpolationEnumUnreal.get(interpolation.name)
                interpolation = InterpolationEnumUnreal.get(interpolation.upper())
            elif isinstance(interpolation, InterpolationEnumBlender):
                interpolation = InterpolationEnumUnreal.get(interpolation.name)
            super().__init__(
                frame=frame,
                location=location,
                rotation=rotation,
                scale=scale,
                interpolation=interpolation,
            )
        elif __platform__ == PlatformEnum.blender:
            if isinstance(interpolation, str):
                interpolation = InterpolationEnumBlender.get(interpolation.upper())
            elif isinstance(interpolation, InterpolationEnumUnreal):
                interpolation = InterpolationEnumBlender.get(interpolation.name)
            super().__init__(
                frame=frame,
                location=location,
                rotation=rotation,
                scale=scale,
                interpolation=interpolation,
            )

    class Config:
        use_enum_values = True


##### Package Constants #####

platform = PlatformEnum.null
remote_function_suffix = "_in_engine"
plugin_name_blender = "XRFeitoriaBpy"
plugin_name_unreal = "XRFeitoriaUnreal"

__range_info__ = "Render Steps: start={}, end={}"
__regex_range_info__ = ".*" + __range_info__.format(r"(\d+)", r"(\d+)") + ".*"
__regex_frame_info__ = r".*Fra:(\d+).*"

##### Blender Constants #####

default_level_blender = 'XRFeitoria'

##### Unreal Constants #####

default_asset_path_unreal = f"/Game/{plugin_name_unreal}"
default_sequence_path_unreal = f"{default_asset_path_unreal}/Sequences"
