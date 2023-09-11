from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from loguru import logger
from typing_extensions import Self

from ..data_structure.constants import PathLike, Vector
from ..object.object_base import ObjectBase
from ..object.object_utils import ObjectUtilsBase
from ..utils import Validator


class ActorBase(ABC, ObjectBase):
    """Base class for all actors in the world."""

    _object_utils = ObjectUtilsBase

    @property
    def stencil_value(self) -> int:
        """Get the stencil value of the actor."""
        return self._get_stencil_value_in_engine(self.name)

    @stencil_value.setter
    def stencil_value(self, value: int):
        """Set the stencil value of the actor.

        Args:
            value (int in [0, 255]): Stencil value.
        """
        self._set_stencil_value_in_engine(self.name, value)

    @property
    def mask_color(self) -> Vector:
        """Get the mask color of the actor.

        RGB values (int) in [0, 255].
        """
        return self._get_mask_color_in_engine(self.name)

    @classmethod
    def import_from_file(
        cls,
        file_path: PathLike,
        actor_name: Optional[str] = None,
        location: 'Vector' = None,
        rotation: 'Vector' = None,
        scale: 'Vector' = None,
        stencil_value: int = 1,
    ) -> Self:
        """Imports an actor from a file and returns its corresponding actor.

        For Blender, support files in types: fbx, obj, abc, ply, stl.

        Note:
            For fbx file, Blender only support binary format. ASCII format is not supported. (`Ref`_)

            .. _Ref: https://docs.blender.org/manual/en/3.6/addons/import_export/scene_fbx.html#id4

        Args:
            path (PathLike): the path to the actor file.
            name (str, optional): the name of the actor. Defaults to None.
            location (Vector, optional): the location of the actor. Defaults to None. unit: meter
            rotation (Vector, optional): the rotation of the actor. Defaults to None. unit: degree
            scale (Vector, optional): the scale of the actor. Defaults to None.
            stencil_value (int in [0, 255], optional): Stencil value of the actor. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            Self: the actor object.
        """
        if actor_name is None:
            actor_name = cls._object_utils.generate_obj_name(obj_type='actor')
        cls._object_utils.validate_new_name(actor_name)
        if location:
            Validator.validate_vector(location, 3)
        if rotation:
            Validator.validate_vector(rotation, 3)
        if scale:
            Validator.validate_vector(scale, 3)

        cls._import_actor_from_file_in_engine(file_path=file_path, actor_name=actor_name)
        actor = cls(actor_name)
        if location:
            actor.location = location
        if rotation:
            actor.rotation = rotation
        if scale:
            actor.scale = scale
        actor.stencil_value = stencil_value
        logger.info(f'[cyan]Imported[/cyan] actor "{actor_name}" from "{Path(file_path).as_posix()}"')
        return actor

    def setup_animation(self, animation_path: 'PathLike', action_name: 'Optional[str]' = None) -> None:
        """Load an animation from a file and setup for the actor.

        For Blender, support files in types: fbx, blend, json.

        Note:
            For fbx file, Blender only support binary format. ASCII format is not supported. (`Ref`_)

            .. _Ref: https://docs.blender.org/manual/en/3.6/addons/import_export/scene_fbx.html#id4

        Args:
            animation_path (PathLike): Animation file path.
            action_name (Optional[str], optional): Name of the action in the animation file. Only required when the file type is `.blend `. Defaults to None.
        """
        Validator.validate_argument_type(animation_path, [str, Path])
        self._import_animation_from_file_in_engine(
            animation_path=animation_path, actor_name=self.name, action_name=action_name
        )
        logger.info(
            f'[cyan]Imported[/cyan] animation '
            f'{action_name if action_name is not None else ""}'
            f'from "{animation_path}" and setup for actor "{self.name}"'
        )

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################
    @staticmethod
    @abstractmethod
    def _get_stencil_value_in_engine(actor_name: str) -> int:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_mask_color_in_engine(actor_name: str) -> 'Vector':
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _set_stencil_value_in_engine(actor_name: str, value: int) -> int:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _import_actor_from_file_in_engine(
        file_path: str,
        actor_name: str,
        stencil_value: int = 1,
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _import_animation_from_file_in_engine(animation_path: str, actor_name: str, action_name: str) -> None:
        raise NotImplementedError
