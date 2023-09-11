from ..data_structure.constants import Vector
from ..object.object_utils import ObjectUtilsUnreal
from ..rpc import remote_unreal
from .camera_base import CameraBase

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in src/XRFeitoriaUnreal/Content/Python
except ModuleNotFoundError:
    pass


@remote_unreal(dec_class=True, suffix='_in_engine')
class CameraUnreal(CameraBase):
    """Camera class for Unreal."""

    _object_utils = ObjectUtilsUnreal

    def look_at(self, target: Vector) -> None:
        """Set the camera to look at the target.

        Args:
            target (Vector): [x, y, z] coordinates of the target, in units of meters.
        """
        target = [x * 100.0 for x in target]  # convert to cm
        super().look_at(target)

    # ----- Getter ----- #

    @staticmethod
    def _get_KRT_in_engine(name: str):
        raise NotImplementedError

    @staticmethod
    def _get_fov_in_engine(name):
        camera: unreal.CameraActor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        return camera.camera_component.field_of_view

    # ----- Setter ----- #

    @staticmethod
    def _set_KRT_in_engine(name, K, R, T):
        raise NotImplementedError

    @staticmethod
    def _set_camera_fov_in_engine(name, fov):
        camera: unreal.CameraActor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        camera.camera_component.field_of_view = fov

    @staticmethod
    def _spawn_in_engine(
        camera_name,
        location: 'Vector' = (0, 0, 0),
        rotation: 'Vector' = (0, 0, 0),
        fov: float = 90,
    ):
        camera: unreal.CameraActor = XRFeitoriaUnrealFactory.utils_actor.spawn_actor_from_class(
            unreal.CameraActor, location, rotation
        )
        camera.camera_component.field_of_view = fov
        camera.set_actor_label(camera_name)
        return camera.get_actor_label()

    @staticmethod
    def _look_at_in_engine(name, target: 'Vector'):
        camera: unreal.CameraActor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = camera.get_actor_location()
        target = unreal.Vector(x=target[0], y=target[1], z=target[2])

        forward = target - location
        z = unreal.Vector(0, 0, -1)
        right = forward.cross(z)
        up = forward.cross(right)
        rotation = unreal.MathLibrary.make_rotation_from_axes(forward, right, up)
        camera.set_actor_rotation(rotation, False)
