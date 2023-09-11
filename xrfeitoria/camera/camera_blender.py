import math
from typing import Dict, List, Optional, Tuple, Union

from ..data_structure.constants import Vector
from ..object.object_utils import ObjectUtilsBlender
from ..rpc import remote_blender
from ..utils import Validator
from .camera_base import CameraBase

try:
    import bpy  # isort:skip
    from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory  # defined in src/XRFeitoriaBpy/core/factory.py
except ModuleNotFoundError:
    pass

try:
    from ..data_structure.models import TransformKeys  # isort:skip
except ModuleNotFoundError:
    pass


@remote_blender(dec_class=True, suffix='_in_engine')
class CameraBlender(CameraBase):
    """Camera class for Blender."""

    _object_utils = ObjectUtilsBlender

    @property
    def active(self) -> bool:
        """Activaty of the camera.

        Only active cameras participate in rendering.
        """
        return self._get_camera_active_in_engine(self._name)

    @active.setter
    def active(self, value):
        Validator.validate_argument_type(value, bool)
        self._set_camera_active_in_engine(self._name, value)

    def set_transform_keys(self, transform_keys: 'TransformKeys') -> None:
        """Set transform keys of actor.

        Args:
            transform_keys (List[Dict]): Keyframes of transform (frame, location, rotation, scale, and interpolation).
        """
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        self._object_utils.set_transform_keys(name=self.name, transform_keys=transform_keys)

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    ######   Getter   ######
    @staticmethod
    def _get_camera_active_in_engine(name: str) -> bool:
        """Get camera's activity in blender. (Only the active cameras participate in
        rendering.)

        Args:
            name (str): name of the camera.

        Returns:
            bool: activity of the camera.
        """
        view: bpy.types.SceneRenderView = bpy.context.scene.render.views.get(name)
        if view is None:
            return False
        else:
            return view.use

    @staticmethod
    def _get_fov_in_engine(name: str) -> float:
        """Get camera's field of view from blender.

        Args:
            name (str): name of the camera.

        Returns:
            float: camera's field of view. (unit: degree)
        """
        camera = bpy.data.objects[name]
        return math.degrees(camera.data.angle)

    @staticmethod
    def _get_KRT_in_engine(name: str) -> 'Tuple[List, List, List]':
        """Get camrea's intrinsic and extrinsic parameters from blender.

        Args:
            name (str): name of the camera.

        Returns:
            Tuple[List, List, List]: K (3x3), R (3x3), T (3)
        """
        camera = bpy.data.objects[name]
        K, R, T = XRFeitoriaBlenderFactory.get_camera_KRT_from_blender(camera)
        return K.tolist(), R.tolist(), T.tolist()

    ######   Setter   ######

    @staticmethod
    def _set_KRT_in_engine(name, K, R, T):
        raise NotImplementedError

    @staticmethod
    def _spawn_in_engine(
        camera_name: str,
        collection_name: 'Optional[str]' = None,
        location: 'Vector' = (0, 0, 0),
        rotation: 'Vector' = (0, 0, 0),
        fov: float = 90.0,
    ) -> None:
        """Setup a new camera in blender.

        Args:
            name (str): Name of the new camera.
            collection_name (str): Name of the scene where spawn the new camera.
            location (Vector, optional): Location of the camera. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the camera. Defaults to (0, 0, 0).
            fov (float in (0.0, 180.0), optional): Field of view of the camera. Defaults to 90.0. (unit: degree)
        """
        ## Create new camera datablock
        camera_data = bpy.data.cameras.new(name=camera_name)

        ## set FOV
        camera_data.lens_unit = 'FOV'
        camera_data.angle = math.radians(fov)  # fov in radians

        ## Create new object with the camera datablock
        camera = bpy.data.objects.new(name=camera_name, object_data=camera_data)

        ## set camera location and rotation
        camera.location = location
        camera.rotation_euler = tuple(math.radians(r) for r in rotation)

        ## get scene and collection
        scene, collection = XRFeitoriaBlenderFactory.get_scene_and_collection_for_new_object(collection_name)

        # link the camera to the collection
        collection.objects.link(camera)

        # set camera activity
        active = False if scene.name == collection.name else True
        XRFeitoriaBlenderFactory.set_camera_activity(camera_name=camera_name, scene=scene, active=active)
        scene.camera = camera

    @staticmethod
    def _set_camera_fov_in_engine(name: str, fov: float):
        """Set camera's field of view in blender.

        Args:
            name (str): name of the camera.
            fov (float): field of view of the camera.
        """
        camera = bpy.data.objects[name]
        camera.data.angle = math.radians(fov)

    @staticmethod
    def _set_camera_active_in_engine(name: str, active: bool):
        """Set camera's activity in blender. (Only the active cameras participate in
        rendering.)

        Args:
            name (str): name of the camera.
            active (bool): activity of the camera.
        """
        bpy.context.scene.render.views[name].use = active

    @staticmethod
    def _look_at_in_engine(name: str, target: 'Vector'):
        """Set the camera to look at the target in blender.

        Args:
            name (str): name of the camera.
            target (Vector): the location of the target.
        """
        camera = bpy.data.objects[name]
        loc_camera = camera.location
        camera.rotation_euler = XRFeitoriaBlenderFactory.get_rotation_to_look_at(loc_camera, target)
