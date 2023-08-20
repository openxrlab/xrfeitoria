from abc import ABC, abstractmethod
from typing import Optional

from ..constants import Vector
from ..object import ObjectBase, ObjectUtilsBase
from ..utils import Validator


class ActorBase(ABC, ObjectBase):
    _object_utils = ObjectUtilsBase

    @classmethod
    def import_actor_from_file(
        cls,
        path: str,
        name: Optional[str] = None,
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        scale: "Vector" = (1, 1, 1),
    ) -> "ActorBase":
        cls._object_utils.validate_new_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_vector(scale, 3)

        cls._object_utils.import_actor_from_file(path, name)
        actor = cls(name)
        actor.set_transform(location, rotation, scale)
        return actor

    @classmethod
    def spawn_from_engine_path(
        cls,
        engine_path: str,
        name: Optional[str] = None,
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        scale: "Vector" = (1, 1, 1),
    ) -> "ActorBase":
        Validator.validate_argument_type(engine_path, str)
        cls._object_utils.validate_new_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_vector(scale, 3)

        cls._object_utils.validate_new_name(name)
        _name = cls._spawn_actor_in_engine(engine_path, name=name, location=location, rotation=rotation, scale=scale)
        return cls(_name)

    def setup_animation(self, anim_asset_path: str, action_name: "Optional[str]" = None) -> None:
        Validator.validate_argument_type(anim_asset_path, str)
        self._object_utils._import_animation_from_file_in_engine(anim_asset_path, self.name, action_name)

    ###########################
    ###  private functions  ###
    ###########################

    @staticmethod
    @abstractmethod
    def _spawn_actor_in_engine(
        engine_path: str,
        name: "Optional[str]" = None,
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        scale: "Vector" = (1, 1, 1),
    ) -> str:
        pass
