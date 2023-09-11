import math
from abc import ABC, abstractmethod
from typing import Dict, List, Literal, Tuple

from ..data_structure.constants import Transform, Vector, xf_obj_name
from ..rpc import remote_blender, remote_unreal
from ..utils import Validator
from ..utils.functions import blender_functions

try:
    # only for linting, not imported in runtime
    import bpy
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in src/XRFeitoriaUnreal/Content/Python
    from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory  # defined in src/XRFeitoriaBpy/core/factory.py
except ModuleNotFoundError:
    pass


class ObjectUtilsBase(ABC):
    """Base class for object utils."""

    ##########################
    # ------- Getter ------- #
    ##########################
    @classmethod
    def get_transform(cls, name: str) -> Tuple[List, List, List]:
        """Get transform (location, rotation, scale) of the object.

        Args:
            name (str): Name of the object.

        Returns:
            Transform: (location 3D vector, rotation 3D vector, scale 3D vector).
                location: Location of the object. unit: meters.
                rotation: Rotation of the object. unit: degrees.
                scale: Scale of the object.
        """
        cls.validate_name(name)
        return cls._get_transform_in_engine(name)

    @classmethod
    def get_location(cls, name: str) -> Vector:
        """Get location of the object.

        Args:
            name (str): Name of the object.

        Returns:
            Vector: Location of the object.
        """
        cls.validate_name(name)
        return cls._get_location_in_engine(name)

    @classmethod
    def get_rotation(cls, name: str) -> Vector:
        """Get rotation of the object.

        Args:
            name (str): Name of the object.

        Returns:
            Vector: Rotation of the object.
        """
        cls.validate_name(name)
        return cls._get_rotation_in_engine(name)

    @classmethod
    def get_scale(cls, name: str) -> Vector:
        """Get scale of the object.

        Args:
            name (str): Name of the object.

        Returns:
            Vector: Scale of the object.
        """
        cls.validate_name(name)
        return cls._get_scale_in_engine(name)

    ##########################
    # ------- Setter ------- #
    ##########################
    @classmethod
    def set_transform(cls, name: str, location: Vector, rotation: Vector, scale: Vector):
        """Set transform (location, rotation, scale) of the object.

        Args:
            name (str): Name of the object.
            location (Vector): Location of the object.
            rotation (Vector): Rotation of the object.
            scale (Vector): Scale of the object.
        """
        cls.validate_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_vector(scale, 3)
        cls._set_transform_in_engine(name, location, rotation, scale)

    @classmethod
    def set_location(cls, name: str, location: Vector):
        """Set location of the object.

        Args:
            name (str): Name of the object.
            location (Vector): Location of the object.
        """
        cls.validate_name(name)
        Validator.validate_vector(location, 3)
        cls._set_location_in_engine(name, location)

    @classmethod
    def set_rotation(cls, name: str, rotation: Vector):
        """Set rotation of the object.

        Args:
            name (str): Name of the object.
            rotation (Vector): Rotation of the object.
        """
        cls.validate_name(name)
        Validator.validate_vector(rotation, 3)
        cls._set_rotation_in_engine(name, rotation)

    @classmethod
    def set_scale(cls, name, scale: Vector):
        """Set scale of the object.

        Args:
            name (str): Name of the object.
            scale (Vector): Scale of the object.
        """
        cls.validate_name(name)
        Validator.validate_vector(scale, 3)
        cls._set_scale_in_engine(name, scale)

    @classmethod
    def set_name(cls, name: str, new_name: str):
        """Set a new name for the object.

        Args:
            name (str): Original name of the object.
            new_name (str): New name of the object.
        """
        if name == new_name:
            return
        cls.validate_name(name)
        cls.validate_new_name(new_name)
        cls._set_name_in_engine(name, new_name)

    @classmethod
    def generate_obj_name(cls, obj_type: 'Literal["camera", "actor"]') -> str:
        return cls._generate_obj_name_in_engine(obj_type)

    ##########################
    # ----- Engine API ----- #
    ##########################

    # ----- Getter ----- #

    @staticmethod
    @abstractmethod
    def _get_transform_in_engine(name: str) -> 'Transform':
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_location_in_engine(name) -> 'Vector':
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_rotation_in_engine(name) -> 'Vector':
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_scale_in_engine(name) -> 'Vector':
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_all_objects_in_engine() -> 'List[str]':
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _generate_obj_name_in_engine(obj_type: str) -> str:
        raise NotImplementedError

    # ----- Setter ----- #

    @staticmethod
    @abstractmethod
    def _set_transform_in_engine(name: str, location: 'Vector', rotation: 'Vector', scale: 'Vector'):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _set_location_in_engine(name: str, location: 'Vector'):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _set_rotation_in_engine(name: str, rotation: 'Vector'):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _set_scale_in_engine(name: str, scale: 'Vector'):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _set_name_in_engine(name: str, new_name: str):
        raise NotImplementedError

    # ------- Delete ------- #
    @classmethod
    def delete_obj(cls, name):
        cls.validate_name(name)
        cls._delete_obj_in_engine(name)

    @staticmethod
    @abstractmethod
    def _delete_obj_in_engine(name):
        raise NotImplementedError

    # ----- Validator ------ #
    @classmethod
    def validate_name(cls, name):
        objects = cls._get_all_objects_in_engine()
        if name not in objects:
            raise ValueError(f"Invalid name, '{name}' does not exist in scene.")

    @classmethod
    def validate_new_name(cls, name):
        objects = cls._get_all_objects_in_engine()
        if name in objects:
            raise ValueError(f"Invalid name, '{name}' already exists in scene.")


@remote_blender(dec_class=True)
class ObjectUtilsBlender(ObjectUtilsBase):
    """Object utils class for Blender."""

    ##########################
    # ------- Getter ------- #
    ##########################

    @classmethod
    def get_dimensions(cls, name: str) -> 'Vector':
        """Get dimensions of the object.

        Args:
            name (str): Name of the object.

        Returns:
            Vector: Dimensions of the object.
        """
        cls.validate_name(name)
        return cls._get_dimensions_in_engine(name=name)

    @classmethod
    def get_bbox(cls, name: str) -> 'Dict[Tuple[Vector, Vector]]':
        """Get bounding box of the object across all frames.

        Args:
            name (str): Name of the object.

        Returns:
            Dict[Tuple[Vector, Vector]]: Bounding box of the object across all frames.
        """
        cls.validate_name(name)
        return cls._get_bbox_in_engine(name=name)

    ##########################
    # ------- Setter ------- #
    ##########################
    @classmethod
    def set_transform_keys(cls, name: str, transform_keys: 'List[Dict]'):
        """Set keyframe of the object.

        Args:
            name (str): Name of the object.
            transform_keys (List[Dict]): Keyframes of transform (frame, location, rotation, scale, and interpolation).
        """
        cls.validate_name(name)
        cls._set_transform_keys_in_engine(obj_name=name, transform_keys=transform_keys)

    @classmethod
    def set_origin(cls, name: str) -> None:
        """Set origin of the object to its center.

        Args:
            name (str): Name of the object.
        """
        cls.validate_name(name)
        cls._set_origin_in_engine(name=name)

    @classmethod
    def set_dimensions(cls, name: str, dimensions: 'Vector') -> None:
        """Set dimensions of the object.

        Args:
            name (str): Name of the object.
            dimensions (Vector): Dimensions of the object.
        """
        cls.validate_name(name)
        cls._set_dimensions_in_engine(name=name, dimensions=dimensions)

    ##########################
    # ----- Engine API ----- #
    ##########################

    # ------- Getter ------- #

    @staticmethod
    def _get_dimensions_in_engine(name: str) -> 'Vector':
        """Get dimensions of the object in Blender.

        Args:
            name (str): Name of the object.

        Returns:
            Vector: Dimensions of the object.
        """
        return bpy.data.objects[name].dimensions.to_tuple()

    @staticmethod
    def _get_transform_in_engine(name: str) -> 'Transform':
        """Get transform (location, rotation and scale) of the object in Blender.

        Args:
            name (str): Name of the object.

        Returns:
            Transform: Transform (location, rotation and scale).
        """
        actor = bpy.data.objects[name]
        location = actor.location.to_tuple()
        rotation = tuple(math.degrees(r) for r in actor.rotation_euler)  # convert to degrees
        scale = actor.scale.to_tuple()
        blender_functions.is_background_mode(warning=True)
        return location, rotation, scale

    @staticmethod
    def _get_location_in_engine(name: str) -> 'Vector':
        """Get location of the object in Blender.

        Args:
            name (str): Name of the object.

        Returns:
            Vector: Location.
        """
        blender_functions.is_background_mode(warning=True)
        return bpy.data.objects[name].location.to_tuple()

    @staticmethod
    def _get_rotation_in_engine(name: str) -> 'Vector':
        """Get rotation of the object in Blender.

        Args:
            name (str): Name of the object.

        Returns:
            Vector: Rotation.
        """
        blender_functions.is_background_mode(warning=True)
        return tuple(math.degrees(r) for r in bpy.data.objects[name].rotation_euler)  # convert to degrees

    @staticmethod
    def _get_scale_in_engine(name) -> 'Vector':
        """Get scale of the object in Blender.

        Args:
            name (str): Name of the object.

        Returns:
            Vector: Scale.
        """
        blender_functions.is_background_mode(warning=True)
        return bpy.data.objects[name].scale.to_tuple()

    @staticmethod
    def _get_all_objects_in_engine() -> 'List[str]':
        """Get all objects in this blend file.

        Returns:
            List[str]: Name of all objects.
        """
        return bpy.data.objects.keys()

    @staticmethod
    def _generate_obj_name_in_engine(obj_type: 'Literal["camera", "actor"]') -> str:
        """Generate a name for the new object.

        Args:
            obj_type (str): Type of the object. It can be either 'camera' or 'actor'.

        Returns:
            str: Name of the new object.
        """
        objs = [obj for obj in bpy.data.objects if obj_type in obj.name and obj.name.startswith(xf_obj_name[:4])]
        # return f'[XF]{obj_type}-{collection.name}-{(len(objs)+1):03}'
        return xf_obj_name.format(obj_type=obj_type, obj_idx=(len(objs) + 1))

    @staticmethod
    def _get_bbox_in_engine(name: str) -> 'Dict[Tuple[Vector, Vector]]':
        """Get bounding box of the object across all frames.

        Args:
            name (str): Name of the object.

        Returns:
            Dict[Tuple[Vector, Vector]]: Bounding box of the object across all frames.
        """
        obj = bpy.data.objects[name]

        keys_range = XRFeitoriaBlenderFactory.get_obj_keys_range(obj)

        bound_box = {}
        if obj.type == 'MESH':
            for frame in range(keys_range[0], keys_range[1]):
                bpy.context.scene.frame_current = frame
                depsgraph = bpy.context.evaluated_depsgraph_get()
                evaluated_obj = obj.evaluated_get(depsgraph)
                evaluated_mesh = evaluated_obj.data

                vertex_positions = []
                for vertex in evaluated_mesh.vertices:
                    vertex_position = evaluated_obj.matrix_world @ vertex.co
                    vertex_positions.append(vertex_position)

                bbox_min = (1e9, 1e9, 1e9)
                bbox_max = (-1e9, -1e9, -1e9)
                bbox_min = (
                    min(bbox_min[0], min(pos.x for pos in vertex_positions)),
                    min(bbox_min[1], min(pos.y for pos in vertex_positions)),
                    min(bbox_min[2], min(pos.z for pos in vertex_positions)),
                )
                bbox_max = (
                    max(bbox_max[0], max(pos.x for pos in vertex_positions)),
                    max(bbox_max[1], max(pos.y for pos in vertex_positions)),
                    max(bbox_max[2], max(pos.z for pos in vertex_positions)),
                )
                bound_box[f'{frame}'] = bbox_min, bbox_max
        elif obj.type == 'ARMATURE':
            bound_box = {}
            for frame in range(keys_range[0], keys_range[1]):
                bpy.context.scene.frame_current = frame

                bbox_min = (1e9, 1e9, 1e9)
                bbox_max = (-1e9, -1e9, -1e9)
                for obj_mesh in obj.children:
                    depsgraph = bpy.context.evaluated_depsgraph_get()
                    evaluated_obj = obj_mesh.evaluated_get(depsgraph)
                    evaluated_mesh = evaluated_obj.data

                    vertex_positions = []
                    for vertex in evaluated_mesh.vertices:
                        vertex_position = evaluated_obj.matrix_world @ vertex.co
                        vertex_positions.append(vertex_position)

                    bbox_min = (
                        min(bbox_min[0], min(pos.x for pos in vertex_positions)),
                        min(bbox_min[1], min(pos.y for pos in vertex_positions)),
                        min(bbox_min[2], min(pos.z for pos in vertex_positions)),
                    )
                    bbox_max = (
                        max(bbox_max[0], max(pos.x for pos in vertex_positions)),
                        max(bbox_max[1], max(pos.y for pos in vertex_positions)),
                        max(bbox_max[2], max(pos.z for pos in vertex_positions)),
                    )
                bound_box[f'{frame}'] = bbox_min, bbox_max
        else:
            raise ValueError(f'Invalid object type: {obj.type}')

        return bound_box

    ##########################
    # ------- Setter ------- #
    ##########################
    @staticmethod
    def _set_transform_in_engine(name: str, location: 'Vector', rotation: 'Vector', scale: 'Vector'):
        """Set transform (location, rotation and scale) of the object in Blender.

        Args:
            name (str): Name of the object.
            location (Vector): Location of the object.
            rotation (Vector): Rotation of the object.
            scale (Vector): Scale of the object.
        """
        actor = bpy.data.objects[name]
        actor.location = location
        actor.rotation_euler = [math.radians(r) for r in rotation]  # convert to radians
        actor.scale = scale

    @staticmethod
    def _set_location_in_engine(name: str, location: 'Vector'):
        """Set location of the object in Blender.

        Args:
            name (str): Name of the object.
            location (Vector): Location of the object.
        """
        actor = bpy.data.objects[name]
        actor.location = location

    @staticmethod
    def _set_rotation_in_engine(name: str, rotation: 'Vector'):
        """Set rotation of the object in Blender.

        Args:
            name (str): Name of the object.
            rotation (Vector): Rotation of the object.
        """
        actor = bpy.data.objects[name]
        actor.rotation_euler = [math.radians(r) for r in rotation]  # convert to radians

    @staticmethod
    def _set_scale_in_engine(name: str, scale: 'Vector'):
        """Set scale of the object in Blender.

        Args:
            name (str): Name of the object.
            rotation (Vector): Scale of the object.
        """
        bpy.data.objects[name].scale = scale

    @staticmethod
    def _set_name_in_engine(name: str, new_name: str):
        """Set name of the object in Blender.

        Args:
            name (str): Name of the object.
            new_name (str): New name of the object.
        """
        bpy.data.objects[name].name = new_name

    @staticmethod
    def _set_transform_keys_in_engine(
        obj_name: str,
        transform_keys: 'List[Dict]',
    ) -> None:
        """Set keyframe of the object in Blender.

        Args:
            obj_name (str): Name of the object.
            transform_keys (List[Dict]): Keyframes of transform (location, rotation, scale, and interpolation).
        """
        obj = bpy.data.objects[obj_name]
        for i, key in enumerate(transform_keys):
            ## insert keyframes
            # https://docs.blender.org/api/current/bpy.types.bpy_struct.html
            if key['location']:
                obj.location = key['location']
                obj.keyframe_insert(data_path='location', frame=key['frame'])
            if key['rotation']:
                obj.rotation_euler = [math.radians(i) for i in key['rotation']]
                obj.keyframe_insert(data_path='rotation_euler', frame=key['frame'])
            if key['scale']:
                obj.scale = key['scale']
                obj.keyframe_insert(data_path='scale', frame=key['frame'])

            ## set interpolation mode
            # https://blender.stackexchange.com/questions/260149/set-keyframe-interpolation-constant-while-setting-a-keyframe-in-blender-python
            if obj.animation_data.action:
                obj_action = bpy.data.actions.get(obj.animation_data.action.name)
                if key['location']:
                    obj_location_fcurve = obj_action.fcurves.find('location')
                    obj_location_fcurve.keyframe_points[i].interpolation = transform_keys[i]['interpolation']
                if key['rotation']:
                    obj_rotation_fcurve = obj_action.fcurves.find('rotation_euler')
                    obj_rotation_fcurve.keyframe_points[i].interpolation = transform_keys[i]['interpolation']
                if key['scale']:
                    obj_scale_fcurve = obj_action.fcurves.find('scale')
                    obj_scale_fcurve.keyframe_points[i].interpolation = transform_keys[i]['interpolation']

    @staticmethod
    def _set_origin_in_engine(name: str) -> None:
        obj = bpy.data.objects[name]
        # select this obj in  blender
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        # set origin to center of mass
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')

    @staticmethod
    def _set_dimensions_in_engine(name: str, dimensions: 'Vector') -> None:
        obj = bpy.data.objects[name]
        obj.dimensions = dimensions

    ##########################
    # ------- Delete ------- #
    ##########################
    @staticmethod
    def _delete_obj_in_engine(name: str):
        """Delete the object in Blender.

        Args:
            name (str): Name of the object.
        """
        bpy.data.objects.remove(bpy.data.objects[name])


@remote_unreal(dec_class=True)
class ObjectUtilsUnreal(ObjectUtilsBase):
    """Object utils class for Unreal."""

    ##########################
    # ----- Engine API ----- #
    ##########################

    # ------- Getter ------- #
    @staticmethod
    def _get_transform_in_engine(name: str) -> 'Transform':
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = actor.get_actor_location()
        rotation = actor.get_actor_rotation()
        scale = actor.get_actor_scale3d()
        # convert from centimeters to meters
        location /= 100.0
        return location.to_tuple(), rotation.to_tuple(), scale.to_tuple()

    @staticmethod
    def _get_location_in_engine(name: str) -> 'Vector':
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = actor.get_actor_location()
        # convert from centimeters to meters
        location /= 100.0
        return location.to_tuple()

    @staticmethod
    def _get_rotation_in_engine(name: str) -> 'Vector':
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        rotation = actor.get_actor_rotation()
        return rotation.to_tuple()

    @staticmethod
    def _get_scale_in_engine(name: str) -> 'Vector':
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        scale = actor.get_actor_scale3d()
        return scale.to_tuple()

    @staticmethod
    def _get_all_objects_in_engine() -> 'List[str]':
        return XRFeitoriaUnrealFactory.utils_actor.get_all_actors_name()

    # ------- Setter ------- #

    @staticmethod
    def _set_transform_in_engine(name: str, location: 'Vector', rotation: 'Vector', scale: 'Vector') -> None:
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = unreal.Vector(location[0], location[1], location[2])
        rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2])
        # convert from meters to centimeters
        location *= 100.0
        actor.set_actor_transform(unreal.Transform(location, rotation, scale), False, False)

    @staticmethod
    def _set_location_in_engine(name: str, location: 'Vector') -> None:
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = unreal.Vector(location[0], location[1], location[2])
        # convert from meters to centimeters
        location *= 100.0
        actor.set_actor_location(location, False, False)

    @staticmethod
    def _set_rotation_in_engine(name: str, rotation: 'Vector') -> None:
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2])
        actor.set_actor_rotation(rotation, False)

    @staticmethod
    def _set_scale_in_engine(name, scale: 'Vector') -> None:
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        actor.set_actor_scale3d(scale)

    @staticmethod
    def _set_name_in_engine(name: str, new_name: str) -> None:
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        actor.set_actor_label(new_name)

    @staticmethod
    def _delete_obj_in_engine(name):
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        XRFeitoriaUnrealFactory.utils_actor.destroy_actor(actor)

    @staticmethod
    @abstractmethod
    def _generate_obj_name_in_engine(obj_type: 'Literal["camera", "actor"]') -> str:
        """Generate a name for the new object.

        Args:
            obj_type (str): Type of the object. It can be either 'camera' or 'actor'.

        Returns:
            str: Name of the new object.
        """
        actors = XRFeitoriaUnrealFactory.utils_actor.get_class_actors(unreal.Actor)
        actors = [
            actor
            for actor in actors
            if obj_type in actor.get_actor_label() and actor.get_actor_label().startswith(xf_obj_name[:4])
        ]
        return xf_obj_name.format(obj_type=obj_type, obj_idx=(len(actors) + 1))


##########################
# ------- Tools -------- #
##########################
# def direction_to_euler(cls, direction_vector: np.ndarray) -> Tuple[float, float, float]:
#     """Convert a direction vector to euler angles (yaw, pitch, roll) in degrees.

#     Args:
#         direction_vector (np.ndarray): [x, y, z] direction vector, in units of meters.

#     Returns:
#         Tuple[float, float, float]: yaw, pitch, roll in degrees.
#     """
#     if np.allclose(direction_vector, 0):
#         logger.warning('Camera is on the top of the target, cannot look at it.')
#         return (0.0, 0.0, 0.0)
#     if not isinstance(direction_vector, np.ndarray):
#         direction_vector = np.array(direction_vector)
#     direction_vector = direction_vector / np.linalg.norm(direction_vector)  # Normalize the direction vector
#     rotation = R.align_vectors([direction_vector], [cls.axis_zero_direction])[0].as_euler('xyz', degrees=True)
#     return rotation.tolist()
