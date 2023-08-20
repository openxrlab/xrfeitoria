from typing import Optional

from ..constants import Vector
from ..object import ObjectUtilsUnreal
from ..rpc import remote_class_unreal
from ..utils import Validator
from . import ActorBase

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in XRFeitoriaUnreal/Content/Python
except ModuleNotFoundError:
    pass


@remote_class_unreal
class ActorUnreal(ActorBase):
    _object_utils = ObjectUtilsUnreal

    @staticmethod
    def _import_actor_from_file_in_engine(path: str) -> None:
        pass

    @staticmethod
    def _spawn_actor_in_engine(
        engine_path: str,
        name: str,
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        scale: "Vector" = (1, 1, 1),
    ) -> str:
        _object = unreal.load_asset(engine_path)
        # location = [loc * 100.0 for loc in location]  # convert from meters to centimeters
        _actor = XRFeitoriaUnrealFactory.utils_actor.spawn_actor_from_object(_object, location, rotation, scale)
        _actor.set_actor_label(name)
        return _actor.get_actor_label()
