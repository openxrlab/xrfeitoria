from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, Union

from loguru import logger
from typing_extensions import Self

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

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @classmethod
    def _new(
        cls,
        seq_name: str,
        level: Optional[str] = None,
        seq_fps: int = 60,
        seq_length: int = 1,
        replace: bool = False,
        **kwargs,
    ) -> None:
        """Create a new sequence.

        Args:
            seq_name (str): Name of the sequence.
            level (Optional[str], optional): Name of the level. Defaults to None.
            seq_fps (int, optional): Frame per second of the new sequence. Defaults to 60.
            seq_length (int, optional): Frame length of the new sequence. Defaults to 60.
            replace (bool, optional): Replace the exist same-name sequence. Defaults to False.
        """
        if level:
            Validator.validate_argument_type(level, str)
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

    # ------ import actor ------ #
    @classmethod
    def import_actor(
        cls,
        file_path: PathLike,
        actor_name: Optional[str] = None,
        location: 'Vector' = None,
        rotation: 'Vector' = None,
        scale: 'Vector' = None,
        stencil_value: int = 1,
    ) -> ActorBase:
        """Imports an actor from a file and adds it to the sequence.

        Args:
            file_path (PathLike): The path to the file containing the actor to import.
            actor_name (Optional[str], optional): The name to give the imported actor. If not provided, a name will be generated automatically. Defaults to None.
            location (Vector, optional): The initial location of the actor. Defaults to None.
            rotation (Vector, optional): The initial rotation of the actor. Defaults to None.
            scale (Vector, optional): The initial scale of the actor. Defaults to None.
            stencil_value (int, optional): The stencil value to use for the actor. Defaults to 1.

        Returns:
            ActorBase: The imported actor.
        """
        if actor_name is None:
            actor_name = cls._object_utils.generate_obj_name(obj_type='actor')
        # judge file path
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f'File "{file_path.as_posix()}" is not found')
        # set transform keys
        transform_keys = SequenceTransformKey(
            frame=0, location=location, rotation=rotation, scale=scale, interpolation='CONSTANT'
        )
        cls._import_actor_in_engine(
            file_path=file_path,
            actor_name=actor_name,
            transform_keys=transform_keys.model_dump(),
            stencil_value=stencil_value,
        )
        logger.info(f'[cyan]Imported[/cyan] actor "{actor_name}" in sequence "{cls.name}"')
        return cls._actor(name=actor_name)

    # ------ spawn actor and camera ------ #

    @classmethod
    def spawn_camera(
        cls,
        location: 'Vector' = None,
        rotation: 'Vector' = None,
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
    def spawn_shape(
        cls,
        type: 'Literal["plane", "cube", "sphere", "cylinder", "cone"]',
        shape_name: str = None,
        location: Vector = None,
        rotation: Vector = None,
        scale: Vector = None,
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

    # ------ use actor and camera ------ #
    @classmethod
    def use_camera(
        cls,
        camera: _camera,
        location: 'Optional[Vector]' = None,
        rotation: 'Optional[Vector]' = None,
        fov: float = None,
    ) -> None:
        """Use the specified level camera in the sequence. The location, rotation and
        fov set in this method are only used in the sequence. The location, rotation and
        fov of the camera in the level will be restored after the sequence is closed.

        Args:
            camera (CameraUnreal or CameraBlender): The camera to use in the sequence.
            location (Optional[Vector], optional): The location of the camera. Defaults to None. unit: meter.
            rotation (Optional[Vector], optional): The rotation of the camera. Defaults to None. unit: degree.
            fov (float, optional): The field of view of the camera. Defaults to None. unit: degree.
        """
        camera_name = camera.name
        location = camera.location if location is None else location
        rotation = camera.rotation if rotation is None else rotation
        fov = camera.fov if fov is None else fov

        transform_keys = SequenceTransformKey(frame=0, location=location, rotation=rotation, interpolation='CONSTANT')
        cls._use_camera_in_engine(
            transform_keys=transform_keys.model_dump(),
            fov=fov,
            camera_name=camera_name,
        )
        logger.info(f'[cyan]Used[/cyan] camera "{camera_name}" in sequence "{cls.name}"')

    @classmethod
    def use_camera_with_keys(
        cls,
        camera: _camera,
        transform_keys: 'TransformKeys',
        fov: float = None,
    ) -> None:
        """Use the specified level camera in the sequence. The transform_keys and fov
        set in this method are only used in the sequence. The location, rotation and fov
        of the camera in the level will be restored after the sequence is closed.

        Args:
            camera (CameraUnreal or CameraBlender): The camera to use.
            transform_keys (TransformKeys): The transform keys to use.
            fov (float, optional): The field of view to use. Defaults to None. unit: degree.
        """
        camera_name = camera.name
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        fov = camera.fov if fov is None else fov
        cls._use_camera_in_engine(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )
        logger.info(
            f'[cyan]Used[/cyan] camera "{camera_name}" with {len(transform_keys)} keys in sequence "{cls.name}"'
        )

    @classmethod
    def use_actor(
        cls,
        actor: _actor,
        location: 'Optional[Vector]' = None,
        rotation: 'Optional[Vector]' = None,
        scale: 'Optional[Vector]' = None,
        stencil_value: int = None,
        anim_asset_path: 'Optional[str]' = None,
    ) -> None:
        """Use the specified level actor in the sequence. The location, rotation, scale,
        stencil_value and anim_asset set in this method are only used in the sequence.
        These peoperties of the actor in the level will be restored after the sequence
        is closed.

        Args:
            actor (ActorUnreal or ActorBlender): The actor to add to the sequence.
            location (Optional[Vector]): The initial location of the actor. If None, the actor's current location is used. unit: meter.
            rotation (Optional[Vector]): The initial rotation of the actor. If None, the actor's current rotation is used. unit: degree.
            scale (Optional[Vector]): The initial scale of the actor. If None, the actor's current scale is used.
            stencil_value (int in [0, 255], optional): The stencil value to use for the spawned actor. Defaults to None.
                Ref to :ref:`FAQ-stencil-value` for details.
            anim_asset_path (Optional[str]): For blender, this argument is the name of an action(bpy.types.Action).
            For Unreal Engine, this argument is the engine path to the animation asset to use for the actor.
            Default to None. If None, the actor's current animation is used, else the specified animation is used.
        """
        actor_name = actor.name
        location = actor.location if location is None else location
        rotation = actor.rotation if rotation is None else rotation
        scale = actor.scale if scale is None else scale
        stencil_value = actor.stencil_value if stencil_value is None else stencil_value

        transform_keys = SequenceTransformKey(
            frame=0, location=location, rotation=rotation, scale=scale, interpolation='CONSTANT'
        )
        cls._use_actor_in_engine(
            actor_name=actor_name,
            transform_keys=transform_keys.model_dump(),
            stencil_value=stencil_value,
            anim_asset_path=anim_asset_path,
        )
        logger.info(f'[cyan]Used[/cyan] actor "{actor_name}" in sequence "{cls.name}"')

    @classmethod
    def use_actor_with_keys(
        cls,
        actor: _actor,
        transform_keys: 'TransformKeys',
        stencil_value: int = None,
        anim_asset_path: 'Optional[str]' = None,
    ) -> None:
        """Use the specified level actor in the sequence. The transform_keys,
        stencil_value and anim_asset set in this method are only used in the sequence.
        These peoperties of the actor in the level will be restored after the sequence
        is closed.

        Args:
            actor (ActorUnreal or ActorBlender): The actor to use in the sequence.
            transform_keys (Union[TransformKeys, List[TransformKeys]]): The transform keys to use with the actor.
            stencil_value (int in [0, 255], optional): The stencil value to use for the spawned actor. Defaults to None.
                Ref to :ref:`FAQ-stencil-value` for details.
            anim_asset_path (Optional[str]): For blender, this argument is the name of an action(bpy.types.Action).
            For Unreal Engine, this argument is the engine path to the animation asset to use for the actor.
            Default to None. If None, the actor's current animation is used, else the specified animation is used.
        """
        actor_name = actor.name
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        stencil_value = actor.stencil_value if stencil_value is None else stencil_value

        cls._use_actor_in_engine(
            actor_name=actor_name,
            transform_keys=transform_keys,
            stencil_value=stencil_value,
            anim_asset_path=anim_asset_path,
        )
        logger.info(f'[cyan]Used[/cyan] actor "{actor_name}" with {len(transform_keys)} keys in sequence "{cls.name}"')

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

    def __repr__(self) -> str:
        return f'<Sequence "{self.name}">'

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    @abstractmethod
    def _import_actor_in_engine(
        file_path: str,
        transform_keys: 'Union[List[Dict], Dict]',
        actor_name: str = 'Actor',
        stencil_value: int = 1,
    ) -> None:
        pass

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
