from typing import Literal, Optional

from loguru import logger

from ..data_structure.constants import ShapeTypeEnumUnreal, Vector
from ..object.object_utils import ObjectUtilsUnreal
from ..rpc import remote_unreal
from ..utils import Validator
from ..utils.functions import unreal_functions
from .actor_base import ActorBase

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in src/XRFeitoriaUnreal/Content/Python
except ModuleNotFoundError:
    pass


@remote_unreal(dec_class=True, suffix='_in_engine')
class ActorUnreal(ActorBase):
    """Actor class for Unreal Engine."""

    _object_utils = ObjectUtilsUnreal

    @classmethod
    def spawn_from_engine_path(
        cls,
        engine_path: str,
        name: Optional[str] = None,
        location: 'Vector' = (0, 0, 0),
        rotation: 'Vector' = (0, 0, 0),
        scale: 'Vector' = (1, 1, 1),
    ) -> 'ActorBase':
        """Spawns an actor in the engine and returns its corresponding actor.

        Args:
            engine_path (str): the path to the actor in the engine. For example, '/Game/Engine/BasicShapes/Cube'.
            name (str, optional): the name of the actor. Defaults to None, in which case a name will be generated.
            location (Vector, optional): the location of the actor. Units are in meters. Defaults to (0, 0, 0).
            rotation (Vector, optional): the rotation of the actor. Units are in degrees. Defaults to (0, 0, 0).
            scale (Vector, optional): the scale of the actor. Defaults to (1, 1, 1).

        Returns:
            ActorBase: the actor that was spawned
        """
        Validator.validate_argument_type(engine_path, str)
        if name is None:
            name = cls._object_utils.generate_obj_name(obj_type='actor')
        cls._object_utils.validate_new_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_vector(scale, 3)

        _name = cls._spawn_actor_in_engine(engine_path, name=name, location=location, rotation=rotation, scale=scale)
        logger.info(f'[cyan]Spawned[/cyan] actor "{_name}"')
        return cls(_name)

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################
    @staticmethod
    def _get_stencil_value_in_engine(actor_name: str) -> int:
        """Get stencil value of the actor in Unreal Engine.

        Args:
            actor_name (str): Name of the actor.

        Returns:
            int: Stencil value.
        """
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(actor_name)
        return XRFeitoriaUnrealFactory.utils_actor.get_stencil_value(actor)

    @staticmethod
    def _get_mask_color_in_engine(actor_name: str) -> 'Vector':
        """Get mask color of the actor in Unreal Engine.

        Args:
            actor_name (str): Name of the actor.

        Returns:
            Vector: Mask color. (r, g, b) in [0, 255].
        """
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(actor_name)
        return XRFeitoriaUnrealFactory.utils_actor.get_actor_mask_color(actor)

    @staticmethod
    def _set_stencil_value_in_engine(actor_name: str, value: int) -> int:
        """Set pass index of the actor in Unreal Engine.

        Args:
            actor_name (str): Name of the actor.
            value (int in [0, 255]): Pass index (stencil value).
        """
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(actor_name)
        XRFeitoriaUnrealFactory.utils_actor.set_stencil_value(actor, value)

    @staticmethod
    def _import_actor_from_file_in_engine(file_path: str, actor_name: str) -> None:
        """Imports an actor from a file in the Unreal Engine and spawns it in the world
        with a given name.

        Args:
            file_path (str): The path to the file of the actor to import.
            actor_name (str): The name to give to the spawned actor in the world.
        """
        actor_paths = XRFeitoriaUnrealFactory.utils.import_asset(file_path)
        actor_object = unreal.load_asset(actor_paths[0])
        actor = XRFeitoriaUnrealFactory.utils_actor.spawn_actor_from_object(actor_object=actor_object)
        actor.set_actor_label(actor_name)

    @staticmethod
    def _spawn_actor_in_engine(
        engine_path: str,
        name: str,
        location: 'Vector' = (0, 0, 0),
        rotation: 'Vector' = (0, 0, 0),
        scale: 'Vector' = (1, 1, 1),
    ) -> str:
        """Spawns an actor in the engine and returns its name.

        Args:
            engine_path (str): the path to the actor in the engine. For example, '/Game/Engine/BasicShapes/Cube'.
            name (str, optional): the name of the actor. Defaults to None, in which case a name will be generated.
            location (Vector, optional): the location of the actor. Units are in meters. Defaults to (0, 0, 0).
            rotation (Vector, optional): the rotation of the actor. Units are in degrees. Defaults to (0, 0, 0).
            scale (Vector, optional): the scale of the actor. Defaults to (1, 1, 1).

        Returns:
            str: the name of the actor that was spawned
        """
        unreal_functions.check_asset_in_engine(engine_path, raise_error=True)
        _object = unreal.load_asset(engine_path)
        # location = [loc * 100.0 for loc in location]  # convert from meters to centimeters
        _actor = XRFeitoriaUnrealFactory.utils_actor.spawn_actor_from_object(_object, location, rotation, scale)
        _actor.set_actor_label(name)
        return _actor.get_actor_label()

    @staticmethod
    def _import_animation_from_file_in_engine(animation_path: str, actor_name: str, action_name: str) -> None:
        # TODO: complete
        pass


@remote_unreal(dec_class=True, suffix='_in_engine')
class ShapeUnrealWrapper:
    """Wrapper class for shapes in Unreal Engine."""

    _object_utils = ObjectUtilsUnreal
    path_mapping = {
        ShapeTypeEnumUnreal.cube.value: '/Engine/BasicShapes/Cube',
        ShapeTypeEnumUnreal.sphere.value: '/Engine/BasicShapes/Sphere',
        ShapeTypeEnumUnreal.cylinder.value: '/Engine/BasicShapes/Cylinder',
        ShapeTypeEnumUnreal.cone.value: '/Engine/BasicShapes/Cone',
        ShapeTypeEnumUnreal.plane.value: '/Engine/BasicShapes/Plane',
    }

    @classmethod
    def spawn(
        cls,
        type: Literal['cube', 'sphere', 'cylinder', 'cone', 'plane'],
        name: Optional[str] = None,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
    ) -> 'ActorUnreal':
        """Spawns a shape in the engine and returns its corresponding actor.

        Args:
            mesh_type (Literal['cube', 'sphere', 'cylinder', 'cone', 'plane']): the type of the shape.
            name (Optional[str], optional): the name of the shape. Defaults to None.
            location (Vector, optional): the location of the shape. Units are in meters. Defaults to (0, 0, 0).
            rotation (Vector, optional): the rotation of the shape. Units are in degrees. Defaults to (0, 0, 0).
            scale (Vector, optional): the scale of the shape. Defaults to (1, 1, 1).
        """
        if name is None:
            name = cls._object_utils.generate_obj_name(obj_type=type)

        return ActorUnreal.spawn_from_engine_path(
            engine_path=cls.path_mapping[type],
            name=name,
            location=location,
            rotation=rotation,
            scale=scale,
        )
