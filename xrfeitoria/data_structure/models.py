from typing import Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field

from .. import _tls
from .constants import (
    EngineEnum,
    ImageFileFormatEnum,
    InterpolationEnumBlender,
    InterpolationEnumUnreal,
    PathLike,
    RenderEngineEnumBlender,
    RenderOutputEnumBlender,
    RenderOutputEnumUnreal,
    Vector,
)

__all__ = ['RenderPass', 'RenderJobBlender', 'RenderJobUnreal', 'SequenceTransformKey']


class RenderPass(BaseModel):
    """Render pass model contains render layer and image format.

    Supported render layer and image format:

        .. tabs::
            .. tab:: RenderLayerBlender

                :class:`~xrfeitoria.data_structure.constants.RenderOutputEnumBlender`:

                    - img
                    - mask
                    - depth
                    - flow
                    - normal
                    - diffuse
                    - denoising_depth

            .. tab:: RenderLayerUnreal

                :class:`~xrfeitoria.data_structure.constants.RenderOutputEnumUnreal`:

                    - img
                    - mask
                    - depth
                    - flow
                    - normal
                    - diffuse
                    - metallic
                    - roughness
                    - specular
                    - tangent
                    - basecolor

            .. tab:: ImageFormat

                :class:`~xrfeitoria.data_structure.constants.ImageFileFormatEnum`:

                    - png
                    - bmp
                    - jpg
                    - exr

    Used in:
        - :class:`~xrfeitoria.data_structure.models.RenderJobBlender`
        - :class:`~xrfeitoria.data_structure.models.RenderJobUnreal`
        - :meth:`Renderer.add_job <xrfeitoria.renderer.renderer_base.RendererBase.add_job>`
        - :meth:`Sequence.add_to_renderer <xrfeitoria.sequence.sequence_base.SequenceBase.add_to_renderer>`
        - ...

    Examples:

        .. tabs::
            .. tab:: define

                .. code-block:: python
                    :linenos:

                    from xrfeitoria.data_structure.models import RenderPass
                    RenderPass('img', 'png')
                    RenderPass('mask', 'exr')
                    RenderPass('normal', 'jpg')
                    ...

            .. tab:: RenderJobBlender

                .. code-block:: python
                    :linenos:
                    :emphasize-lines: 6

                    from xrfeitoria.data_structure.models import RenderJobBlender, RenderPass
                    RenderJobBlender(
                        sequence_name=...,
                        output_path=...,
                        resolution=...,
                        render_passes=[RenderPass('img', 'png')],
                    )

            .. tab:: RenderJobUnreal

                .. code-block:: python
                    :linenos:
                    :emphasize-lines: 7

                    from xrfeitoria.data_structure.models import RenderJobUnreal, RenderPass
                    RenderJobUnreal(
                        map_path=...,
                        sequence_path=...,
                        output_path=...,
                        resolution=...,
                        render_passes=[RenderPass('img', 'png')],
                    )

            .. tab:: seq.add_to_renderer

                .. code-block:: python
                    :linenos:
                    :emphasize-lines: 9

                    import xrfeitoria as xf
                    from xrfeitoria.data_structure.models import RenderPass

                    with xf.init_blender() as xf_runner:
                        seq = xf_runner.Sequence.new(seq_name='test'):
                            seq.add_to_renderer(
                                output_path=...,
                                resolution=...,
                                render_passes=[RenderPass('img', 'png')],
                            )

                        xf_runner.render()
    """

    render_layer: Union[RenderOutputEnumBlender, RenderOutputEnumUnreal] = Field(
        description='Render layer of the render pass.'
    )
    image_format: ImageFileFormatEnum = Field(description='Image format of the render pass.')

    def __init__(
        self,
        render_layer: Union[
            Literal['img', 'mask', 'depth', 'flow', 'normal', 'diffuse'],
            RenderOutputEnumBlender,
            RenderOutputEnumUnreal,
        ],
        image_format: Union[Literal['png', 'bmp', 'jpg', 'jpeg', 'exr'], ImageFileFormatEnum],
    ) -> None:
        """Render pass for Unreal or Blender, which contains render layer and image
        format.

        Args:
            render_layer (Union[RenderOutputEnumBlender, RenderOutputEnumUnreal, str]):
                Render layer of Unreal or Blender. Should be one of the following enum, or the string of it:
                    `RenderOutputEnumBlender`: `img`, `mask`, `depth`, `denoising_depth`, `flow`, `normal`, `diffuse` \n
                    `RenderOutputEnumUnreal`: `img`, `mask`, `depth`, `flow`, `normal`, `diffuse`,
                    `metallic`, `roughness`, `specular`, `tangent`, `basecolor`
            image_format (Union[ImageFileFormatEnum, str]):
                Image format of Unreal or Blender.  Should be element of the enum, or the string of it:
                    `ImageFileFormatEnum`: `png`, `bmp`, `jpg`, `jpeg`, `exr`
        """
        __platform__ = _tls.cache.get('platform', None)
        assert __platform__, 'xrfeitoria.init_blender() or xrfeitoria.init_unreal() must be called first'

        if isinstance(image_format, str):
            image_format = ImageFileFormatEnum.get(image_format.lower())

        if __platform__ == EngineEnum.unreal:
            if isinstance(render_layer, RenderOutputEnumUnreal):
                pass
            elif isinstance(render_layer, str):
                render_layer = RenderOutputEnumUnreal.get(render_layer.lower())
            elif isinstance(render_layer, RenderEngineEnumBlender):
                raise ValueError('Unreal does not support Blender render layer')
            super().__init__(
                render_layer=render_layer,
                image_format=image_format,
            )

        elif __platform__ == EngineEnum.blender:
            if isinstance(render_layer, RenderOutputEnumBlender):
                pass
            elif isinstance(render_layer, str):
                render_layer = RenderOutputEnumBlender.get(render_layer.lower())
            elif isinstance(render_layer, RenderOutputEnumUnreal):
                raise ValueError('Blender does not support Unreal render layer')
            super().__init__(
                render_layer=render_layer,
                image_format=image_format,
            )

    class Config:
        use_enum_values = True


class RenderJobBlender(BaseModel):
    """Render job model for Blender."""

    sequence_name: str = Field(description='Name of the sequence of the render job.')

    output_path: PathLike = Field(description='Output path of the render job.')
    resolution: Tuple[int, int] = Field(description='Resolution of the images rendered by the render job.')
    render_passes: List[RenderPass] = Field(description='Render passes of the render job.')
    render_engine: RenderEngineEnumBlender = Field(description='Render engine of the render job.')
    render_samples: int = Field(ge=1, description='Render samples of the render job.')
    transparent_background: bool = Field(default=False, description='Whether to render with transparent background.')
    arrange_file_structure: bool = Field(
        default=True, description='Whether to arrange file structure of the output images of the render job.'
    )

    class Config:
        use_enum_values = True


class RenderJobUnreal(BaseModel):
    """Render job model for Unreal."""

    class AntiAliasSetting(BaseModel):
        enable: bool = Field(default=False, description='Whether to enable anti aliasing.')
        override_anti_aliasing: bool = Field(default=False, description='Whether to override anti aliasing.')
        spatial_samples: int = Field(default=8, ge=1, description='Spatial samples of the anti aliasing.')
        temporal_samples: int = Field(default=8, ge=1, description='Temporal samples of the anti aliasing.')
        warmup_frames: int = Field(
            default=0,
            ge=0,
            description=(
                'Warmup frames in engine which would rendered before actual frame range. '
                'This is crucial when particle system (Niagara) is used.'
            ),
        )
        render_warmup_frame: bool = Field(
            default=False, description='Whether to render warmup frame of the anti aliasing.'
        )

    map_path: str = Field(description='Map path of the render job.')
    sequence_path: str = Field(description='Sequence path of the render job.')

    output_path: PathLike = Field(description='Output path of the render job.')
    resolution: Tuple[int, int] = Field(description='Resolution of the images rendered by the render job.')
    render_passes: List[RenderPass] = Field(description='Render passes of the render job.')
    file_name_format: str = Field(
        default='{sequence_name}/{render_pass}/{camera_name}/{frame_number}',
        description='File name format of the render job.',
    )
    console_variables: Dict[str, float] = Field(
        default={'r.MotionBlurQuality': 0},
        description='Additional console variables of the render job. Ref to :ref:`FAQ-console-variables` for details.',
    )
    anti_aliasing: AntiAliasSetting = Field(
        default=AntiAliasSetting(), description='Anti aliasing setting of the render job.'
    )
    export_audio: bool = Field(default=False, description='Whether to export audio of the render job.')

    class Config:
        use_enum_values = True


class SequenceTransformKey(BaseModel):
    """Transform key model for object (actor/camera) in sequence.

    Examples:

        .. tabs::

            .. tab:: define

                .. code-block:: python
                    :linenos:

                    from xrfeitoria.data_structure.models import SequenceTransformKey as SeqTransKey
                    key = SeqTransKey(
                        frame=0,
                        location=(0, 0, 0),
                        rotation=(0, 0, 0),
                        scale=(1, 1, 1),
                        interpolation='AUTO'
                    )

    Used in methods with suffix ``_with_keys``, such as
        - :meth:`Sequence.spawn_camera_with_keys <xrfeitoria.sequence.sequence_base.SequenceBase.spawn_camera_with_keys>`
        - :meth:`Sequence.spawn_shape_with_keys <xrfeitoria.sequence.sequence_base.SequenceBase.spawn_shape_with_keys>`
        - :meth:`SequenceUnreal.spawn_actor_with_keys <xrfeitoria.sequence.sequence_unreal.SequenceUnreal.spawn_actor_with_keys>`
        - :meth:`SequenceBlender.import_actor_with_keys <xrfeitoria.sequence.sequence_blender.SequenceBlender.import_actor_with_keys>`
        - :func:`ObjectUtils.set_transform_keys <xrfeitoria.object.object_utils.ObjectUtilsBlender.set_transform_keys>`
        - ...
    """

    frame: int = Field(description='Frame number of the transform key, unit: frame.')
    location: Optional[Vector] = Field(
        default=None, description='Location of the object in the transform key, unit: meter.'
    )
    rotation: Optional[Vector] = Field(
        default=None, description='Rotation of the object in the transform key, unit: degree.'
    )
    scale: Optional[Vector] = Field(default=None, description='Scale of the object in the transform key.')
    interpolation: Union[InterpolationEnumUnreal, InterpolationEnumBlender] = Field(
        description='Interpolation type of the transform key.'
    )

    def __init__(
        self,
        frame: int,
        location: Optional[Vector] = None,
        rotation: Optional[Vector] = None,
        scale: Optional[Vector] = None,
        interpolation: Literal['CONSTANT', 'AUTO', 'LINEAR'] = 'AUTO',
    ) -> None:
        """Transform key for Unreal or Blender, which contains frame, location,
        rotation, scale and interpolation type.

        Args:
            frame (int): Frame number of the transform key. unit: frame
            location (Vector): Location of the object in the transform key. unit: meter
            rotation (Vector): Rotation of the object in the transform key. unit: degree
            scale (Vector, optional): Scale of the object in the transform key.
            interpolation (Literal, optional): Interpolation type of the transform key.
                Should be one of the following enum, or the string of it: \n
                    `CONSTANT`: No interpolation \n
                    `AUTO`: Bezier interpolation with cubic bezier curves \n
                    `LINEAR`: Linear interpolation
        """
        __platform__ = _tls.cache.get('platform', None)
        assert __platform__, 'xrfeitoria.init_blender() or xrfeitoria.init_unreal() must be called first'

        if __platform__ == EngineEnum.unreal:
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
        elif __platform__ == EngineEnum.blender:
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


TransformKeys = Union[List[SequenceTransformKey], SequenceTransformKey]
