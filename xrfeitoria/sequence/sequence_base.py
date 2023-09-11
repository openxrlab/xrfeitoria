from abc import ABC, abstractmethod
from typing import Dict, List, Literal, Optional, Tuple, Union

from loguru import logger

from .. import _tls
from ..actor.actor_base import ActorBase
from ..camera.camera_base import CameraBase
from ..data_structure.constants import EngineEnum, PathLike, Vector
from ..object.object_utils import ObjectUtilsBase
from ..renderer.renderer_base import RendererBase
from ..utils import Validator

try:
    from ..data_structure.models import SequenceTransformKey, TransformKeys, RenderPass  # isort:skip
except ModuleNotFoundError:
    SequenceTransformKey = TransformKeys = RenderPass = None


class SequenceBase(ABC):
    """Base sequence class."""

    name: str = None

    _actor = ActorBase
    _camera = CameraBase
    _object_utils = ObjectUtilsBase
    _renderer = RendererBase
    __platform__: EngineEnum = _tls.cache.get('platform', None)

    @classmethod
    def _new(
        cls,
        seq_name: str,
        level: Union[str, List[str]],
        seq_fps: int = 60,
        seq_length: int = 1,
        replace: bool = False,
        **kwargs,
    ) -> None:
        """Create a new sequence.

        Args:
            seq_name (str): Name of the sequence.
            level (List[str], optional): Levels to link to the sequence. Defaults to [].
            seq_fps (int, optional): Frame per second of the new sequence. Defaults to 60.
            seq_length (int, optional): Frame length of the new sequence. Defaults to 60.
            replace (bool, optional): Replace the exist same-name sequence. Defaults to False.
        """
        if cls.__platform__ == EngineEnum.unreal:
            Validator.validate_argument_type(level, str)
        else:
            Validator.validate_argument_type(level, [str, List])
        cls._new_seq_in_engine(
            seq_name=seq_name, level=level, seq_fps=seq_fps, seq_length=seq_length, replace=replace, **kwargs
        )
        cls.name = seq_name
        # TODO: info sequence infos like path, name, corresponding level, etc.
        logger.info(f'>>>> [cyan]Created[/cyan] sequence "{cls.name}" >>>>')

    @classmethod
    def _open(cls, seq_name: str) -> None:
        """Open an exist sequence.

        Args:
            seq_name (str): Name of the sequence.
        """
        cls._open_seq_in_engine(seq_name=seq_name)
        cls.name = seq_name
        logger.info(f'>>>> [cyan]Opened[/cyan] sequence "{cls.name}" >>>>')

    @classmethod
    def close(cls) -> None:
        """Close the opened sequence."""
        cls._close_seq_in_engine()
        logger.info(f'<<<< [red]Closed[/red] sequence "{cls.name}" <<<<')
        cls.name = None

    @classmethod
    def save(cls) -> None:
        """Save the sequence."""
        cls._save_seq_in_engine()
        logger.info(f'++++ [cyan]Saved[/cyan] sequence "{cls.name}" ++++')

    @classmethod
    def show(cls) -> None:
        """Show the sequence in the engine."""
        cls._show_seq_in_engine()

    # ------ spawn actor and camera ------ #

    @classmethod
    def spawn_camera(
        cls,
        location: 'Vector',
        rotation: 'Vector',
        fov: float = 90.0,
        camera_name: Optional[str] = None,
    ) -> CameraBase:
        """Spawn a new camera in the sequence.

        Args:
            location (Vector): Location of the camera.
            rotation (Vector): Rotation of the camera.
            fov (float in (0.0, 180.0), optional): Field of view of the camera len. Defaults to 90.0. (unit: degrees)
            camera_name (str, optional): Name of the camera. Defaults to None.
        """
        if camera_name is None:
            camera_name = cls._object_utils.generate_obj_name(obj_type='camera')
        transform_keys = SequenceTransformKey(frame=0, location=location, rotation=rotation, interpolation='CONSTANT')
        cls._spawn_camera_in_engine(
            transform_keys=transform_keys.model_dump(),
            fov=fov,
            camera_name=camera_name,
        )
        logger.info(f'[cyan]Spawned[/cyan] camera "{camera_name}" in sequence "{cls.name}"')
        return cls._camera(name=camera_name)

    @classmethod
    def spawn_camera_with_keys(
        cls,
        transform_keys: 'TransformKeys',
        fov: float = 90.0,
        camera_name: str = None,
    ) -> CameraBase:
        """Spawn a new camera with keyframes in the sequence.

        Args:
            transform_keys (TransformKeys): Keyframes of transform (location, rotation, and scale).
            fov (float in (0.0, 180.0), optional): Field of view of the camera len. Defaults to 90.0. (unit: degrees)
            camera_name (str, optional): Name of the camera. Defaults to 'Camera'.
        """
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        if camera_name is None:
            camera_name = cls._object_utils.generate_obj_name(obj_type='camera')
        cls._spawn_camera_in_engine(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )
        logger.info(
            f'[cyan]Spawned[/cyan] camera "{camera_name}" with {len(transform_keys)} keys in sequence "{cls.name}"'
        )
        return cls._camera(name=camera_name)

    @classmethod
    def use_camera(cls, camera: 'CameraBase') -> None:
        """Use a level camera in the sequence.

        Args:
            camera_name (str): Name of the camera.
        """
        cls._use_camera_in_engine(camera_name=camera.name)
        logger.info(f'[cyan]Used[/cyan] level camera "{camera.name}" in "{cls.name}"')

    @classmethod
    def spawn_shape(
        cls,
        type: 'Literal["plane", "cube", "sphere", "cylinder", "cone"]',
        shape_name: str = None,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
        **kwargs,
    ) -> ActorBase:
        """Spawn a shape in the sequence.

        Args:
            type (str): Type of new spawn shape. One of ["plane", "cube", "sphere", "cylinder", "cone"]
            shape_name (str): Name of the new added shape. Defaults to None.
            location (Vector, optional): Location of the shape. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the shape. Defaults to (0, 0, 0).
            scale (Vector, optional): Scale of the shape. Defaults to (1, 1, 1).
            stencil_value (int in [0, 255], optional): Stencil value of the shape. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            ShapeBlender or ShapeUnreal: New added shape.
        """
        transform_keys = SequenceTransformKey(
            frame=0, location=location, rotation=rotation, scale=scale, interpolation='CONSTANT'
        )
        if shape_name is None:
            shape_name = cls._object_utils.generate_obj_name(obj_type=type)
        cls._spawn_shape_in_engine(
            type=type,
            transform_keys=transform_keys.model_dump(),
            shape_name=shape_name,
            stencil_value=stencil_value,
            **kwargs,
        )
        logger.info(f'[cyan]Spawned[/cyan] {type.capitalize()} "{shape_name}" in sequence "{cls.name}"')
        return cls._actor(name=shape_name)

    @classmethod
    def spawn_shape_with_keys(
        cls,
        transform_keys: 'TransformKeys',
        type: 'Literal["plane", "cube", "sphere", "cylinder", "cone"]',
        shape_name: str = None,
        stencil_value: int = 1,
        **kwargs,
    ) -> ActorBase:
        """Spawn a shape with keyframes in the sequence.

        Args:
            shape_name (str): Name of the new added shape.
            type (str): Type of new spawn shape. One of ["plane", "cube", "sphere", "cylinder", "cone"]
            transform_keys (TransformKeys): Keyframes of transform (location, rotation, and scale).
            stencil_value (int in [0, 255], optional): Stencil value of the cone. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            ShapeBlender or ShapeUnreal: New added shape.
        """
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        if shape_name is None:
            shape_name = cls._object_utils.generate_obj_name(obj_type=type)
        cls._spawn_shape_in_engine(
            type=type,
            transform_keys=transform_keys,
            shape_name=shape_name,
            stencil_value=stencil_value,
            **kwargs,
        )
        logger.info(
            f"[cyan]Spawned[/cyan] {type.capitalize()} '{shape_name}' "
            f"with {len(transform_keys)} keys in sequence '{cls.name}'."
        )
        return cls._actor(name=shape_name)

    @classmethod
    def add_to_renderer(
        cls,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: List[RenderPass],
        **kwargs,
    ):
        """Add a rendering job with specific settings.

        Args:
            output_path (PathLike): Output path of the rendered images.
            resolution (Tuple[int, int]): Resolution of the rendered images.
            render_passes (List[RenderPass]): Render passes.
            kwargs: Other engine specific arguments.
        """
        cls._renderer.add_job(
            sequence_name=cls.name,
            output_path=output_path,
            resolution=resolution,
            render_passes=render_passes,
            **kwargs,
        )
        logger.info(
            f'[cyan]Added[/cyan] sequence "{cls.name}" to [bold]`Renderer`[/bold] '
            f'(jobs to render: {len(cls._renderer.render_queue)})'
        )
        # return render_job

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    @abstractmethod
    def _spawn_camera_in_engine(
        transform_keys: 'Union[List[Dict], Dict]',
        fov: float = 90.0,
        camera_name: str = 'Camera',
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _spawn_shape_in_engine(
        type: 'Literal["plane", "cube", "sphere", "cylinder", "cone"]',
        transform_keys: 'Union[List[Dict], Dict]',
        shape_name: str = 'Shape',
        stencil_value: int = 1,
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _use_camera_in_engine(camera_name: str) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _new_seq_in_engine(
        level: Union[str, List[str]],
        seq_name: str = 'Sequence',
        seq_fps: int = 60,
        seq_length: int = 60,
        replace: bool = False,
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _open_seq_in_engine(*args, **kwargs) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _close_seq_in_engine() -> None:
        pass

    @staticmethod
    @abstractmethod
    def _save_seq_in_engine() -> None:
        pass

    @staticmethod
    @abstractmethod
    def _show_seq_in_engine() -> None:
        pass
