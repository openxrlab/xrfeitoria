from ..constants import Vector
from ..object import ObjectUtilsUnreal
from ..rpc import remote_class_unreal
from . import CameraBase

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in XRFeitoriaUnreal/Content/Python
except ModuleNotFoundError:
    pass


@remote_class_unreal
class CameraUnreal(CameraBase):
    _object_utils = ObjectUtilsUnreal

    # ----- Getter ----- #

    @staticmethod
    def _get_camera_KRT_in_engine(name):
        # TODO: camera_KRT, make this correct
        camera: unreal.CameraActor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = camera.get_actor_location()
        rotation = camera.get_actor_rotation()
        fov = camera.camera_component.field_of_view
        return location.to_tuple(), rotation.to_tuple(), fov

    @staticmethod
    def _get_camera_fov_in_engine(name):
        camera: unreal.CameraActor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        return camera.camera_component.field_of_view

    # ----- Setter ----- #

    @staticmethod
    def _set_camera_fov_in_engine(name, fov):
        camera: unreal.CameraActor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        camera.camera_component.field_of_view = fov

    @staticmethod
    def _setup_camera_in_engine(
        camera_name,
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        fov: float = 90,
    ):
        camera: unreal.CameraActor = XRFeitoriaUnrealFactory.utils_actor.spawn_actor_from_class(
            unreal.CameraActor, location, rotation
        )
        camera.camera_component.field_of_view = fov
        camera.set_actor_label(camera_name)
        return camera.get_actor_label()
