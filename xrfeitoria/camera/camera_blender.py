import math
from typing import Dict, Generator, List, Optional, Tuple, Union

import loguru
import numpy as np

from ..constants import PathLike, SequenceTransformKey, Vector, default_level_blender
from ..object import ObjectUtilsBlender
from ..rpc import remote_class_blender
from ..utils import Validator
from . import CameraBase

try:
    import bpy
except ModuleNotFoundError:
    pass


@remote_class_blender
class CameraBlender(CameraBase):
    _object_utils = ObjectUtilsBlender

    @classmethod
    def spawn_camera(
        cls,
        name: str,
        collection_name: str = default_level_blender,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        fov: float = 90,
    ) -> "CameraBase":
        cls._object_utils.validate_new_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_argument_type(fov, [float, int])
        cls._setup_camera_in_engine(
            camera_name=name, location=location, rotation=rotation, fov=fov, collection_name=collection_name
        )
        return cls(name)

    @classmethod
    def spawn_camera_with_keys(
        cls,
        name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        fov: float = 90.0,
    ) -> "CameraBase":
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        cls.spawn_camera(name=name, fov=fov, collection_name=collection_name)
        cls._object_utils._set_keyframe_in_engine(obj_name=name, transform_keys=transform_keys)
        return cls(name)

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    ######   Getter   ######
    @staticmethod
    def _get_camera_fov_in_engine(name) -> float:
        camera = bpy.data.objects[name]
        return math.degrees(camera.data.angle)

    @staticmethod
    def _get_camera_KRT_in_engine(name):
        camera = bpy.data.objects[name]
        K, R, T = CameraUtils.get_camera_KRT_from_blender(camera)
        return K.tolist(), R.tolist(), T.tolist()

    ######   Setter   ######

    @staticmethod
    def _setup_camera_in_engine(
        camera_name: str,
        collection_name: str,
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        fov: float = 90.0,
    ) -> str:
        ## Create new camera datablock
        camera_data = bpy.data.cameras.new(name=camera_name)

        ## set FOV
        camera_data.lens_unit = "FOV"
        camera_data.angle = math.radians(fov)  # fov in radians
        ## set FOV
        camera_data.lens_unit = "FOV"
        camera_data.angle = math.radians(fov)  # fov in radians

        ## Create new object with the camera datablock
        camera = bpy.data.objects.new(name=camera_name, object_data=camera_data)

        ## set camera location and rotation
        camera.location = location
        camera.rotation_euler = tuple(math.radians(r) for r in rotation)
        ## set camera location and rotation
        camera.location = location
        camera.rotation_euler = tuple(math.radians(r) for r in rotation)

        # scene = bpy.data.scenes[collection_name] if collection_name else bpy.context.scene
        collection = bpy.data.collections.get(collection_name)
        assert collection, f"Collection {collection_name} not found"
        collection.objects.link(camera)

        # active scene
        scene = bpy.data.scenes[collection_name]
        if collection_name in scene.collection.children.keys():
            # assert (
            #     collection_name in scene.collection.children.keys()
            # ), f"Collection {collection_name} not found in the active scene"
            CameraUtils.set_multiview(scene)
            CameraUtils.add_multiview_camera(camera_name=camera_name, scene=scene)
            scene.camera = camera

    @staticmethod
    def _set_camera_fov_in_engine(name, fov: float):
        camera = bpy.data.objects[name]
        camera.data.angle = math.radians(fov)

    @staticmethod
    def _set_camera_active_in_engine(name: str, active: bool):
        bpy.context.scene.render.views[name].use = active


@remote_class_blender
class CameraUtils:
    """Camera utils functions"""

    @classmethod
    def get_3x3_K_matrix_from_blender(cls, cam) -> np.array:
        scene = bpy.context.scene
        fov = cam.data.angle

        resolution_x_in_px = scene.render.resolution_x
        resolution_y_in_px = scene.render.resolution_y

        focal = max(resolution_x_in_px, resolution_y_in_px) / 2 / math.tan(fov / 2)
        u_0 = resolution_x_in_px / 2
        v_0 = resolution_y_in_px / 2

        K = np.array(((focal, 0, u_0), (0, focal, v_0), (0, 0, 1)))
        return K

    @classmethod
    def get_R_T_matrix_from_blender(cls, cam) -> Tuple[np.array, np.array]:
        R_BlenderView_to_OpenCVView = np.diag([1, -1, -1])

        location, rotation = cam.matrix_world.decompose()[:2]
        R_BlenderView = rotation.to_matrix().transposed()

        T_BlenderView = -1.0 * R_BlenderView @ location

        R = R_BlenderView_to_OpenCVView @ R_BlenderView
        T = R_BlenderView_to_OpenCVView @ T_BlenderView

        return R, T

    @classmethod
    def get_camera_KRT_from_blender(cls, cam) -> Tuple[np.array, np.array, np.array]:
        """Get camera KRT from blender camera object"""
        from scipy.spatial.transform import Rotation as spRotation

        K = cls.get_3x3_K_matrix_from_blender(cam)
        R, T = cls.get_R_T_matrix_from_blender(cam)

        # TODO: remove scipy dependency, has gimbal lock issue
        R_euler_offset = np.array([-math.pi / 2, 0, 0])
        R_euler = spRotation.from_matrix(R).as_euler("xyz", degrees=False)
        R_euler += R_euler_offset
        R = spRotation.from_euler("xyz", R_euler, degrees=False).as_matrix()
        return K, R, T

    @classmethod
    def set_multiview(cls, scene: "bpy.types.Scene") -> None:
        """Set the multiview of the scene"""
        if not scene.render.use_multiview:
            scene.render.use_multiview = True
            scene.render.views_format = "MULTIVIEW"
            scene.render.views[0].use = False
            scene.render.views[1].use = False

    @classmethod
    def add_multiview_camera(cls, camera_name: str, scene: "bpy.types.Scene", active: bool = True) -> None:
        render_view = scene.render.views.new(camera_name)
        render_view.file_suffix = camera_name
        render_view.camera_suffix = camera_name
        render_view.use = active

    @classmethod
    def get_active_cameras(cls, scene: "bpy.types.Scene") -> List[str]:
        active_cameras = []
        for cam in scene.render.views:
            if cam.use == True:
                active_cameras.append(cam.camera_suffix)
        return active_cameras
