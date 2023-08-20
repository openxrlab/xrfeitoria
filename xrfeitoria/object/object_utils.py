import json
import math
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from xrfeitoria.constants import Vector

from ..constants import ImportFileFormatEnum, PathLike, Transform, Vector, default_level_blender
from ..rpc import remote_blender_decorator_class, remote_unreal_decorator_class
from ..utils import BlenderSceneCollectionUtils, Validator

try:
    # only for linting, not imported in runtime
    import bpy
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in XRFeitoriaUnreal/Content/Python
except ModuleNotFoundError:
    pass


class ObjectUtilsBase(ABC):
    ##########################
    # ------- Getter ------- #
    ##########################
    @classmethod
    def get_transform(cls, name: str) -> Transform:
        cls.validate_name(name)
        return cls._get_transform_in_engine(name)

    @classmethod
    def get_location(cls, name: str) -> Vector:
        cls.validate_name(name)
        return cls._get_location_in_engine(name)

    @classmethod
    def get_rotation(cls, name: str) -> Vector:
        cls.validate_name(name)
        return cls._get_rotation_in_engine(name)

    @classmethod
    def get_scale(cls, name: str) -> Vector:
        cls.validate_name(name)
        return cls._get_scale_in_engine(name)

    ##########################
    # ------- Setter ------- #
    ##########################
    @classmethod
    def set_transform(cls, name: str, location: Vector, rotation: Vector, scale: Vector):
        cls.validate_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_vector(scale, 3)
        cls._set_transform_in_engine(name, location, rotation, scale)

    @classmethod
    def set_location(cls, name, location: Vector):
        cls.validate_name(name)
        Validator.validate_vector(location, 3)
        cls._set_location_in_engine(name, location)

    @classmethod
    def set_rotation(cls, name, rotation: Vector):
        cls.validate_name(name)
        Validator.validate_vector(rotation, 3)
        cls._set_rotation_in_engine(name, rotation)

    @classmethod
    def set_scale(cls, name, scale: Vector):
        cls.validate_name(name)
        Validator.validate_vector(scale, 3)
        cls._set_scale_in_engine(name, scale)

    @classmethod
    def set_name(cls, name: str, new_name: str):
        if name == new_name:
            return
        cls.validate_name(name)
        cls.validate_new_name(new_name)
        cls._set_name_in_engine(name, new_name)

    @classmethod
    def import_actor_from_file(cls, path: str, name: str, collection_name: str = default_level_blender) -> str:
        Validator.validate_argument_type(path, str)
        cls.validate_new_name(name)
        return cls._import_actor_from_file_in_engine(path, name, collection_name)

    ##########################
    # ----- Engine API ----- #
    ##########################

    # ----- Getter ----- #

    @staticmethod
    @abstractmethod
    def _get_transform_in_engine(name: str) -> "Transform":
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_location_in_engine(name) -> "Vector":
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_rotation_in_engine(name) -> "Vector":
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_scale_in_engine(name) -> "Vector":
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_all_objects_in_engine() -> "List[str]":
        raise NotImplementedError

    # ----- Setter ----- #

    @staticmethod
    @abstractmethod
    def _set_transform_in_engine(name: str, location: "Vector", rotation: "Vector", scale: "Vector"):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _set_location_in_engine(name: str, location: "Vector"):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _set_rotation_in_engine(name: str, rotation: "Vector"):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _set_scale_in_engine(name: str, scale: "Vector"):
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
    def delete_all():
        raise NotImplementedError

    @staticmethod
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

    # -------- IO ---------- #

    @staticmethod
    @abstractmethod
    def _import_actor_from_file_in_engine(path: str, name: str) -> None:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _import_animation_from_file_in_engine(path: str, name: str) -> None:
        raise NotImplementedError


@remote_blender_decorator_class
class ObjectUtilsBlender(ObjectUtilsBase):
    @classmethod
    def import_actor_from_file(cls, path: str, name: str, collection_name: str = default_level_blender) -> str:
        super().import_actor_from_file(path, name, collection_name)

    @classmethod
    def set_pass_index(cls, name: str, index: int):
        cls.validate_name(name)
        cls._set_pass_index_in_engine(name, index)

    ##########################
    # ------- Getter ------- #
    ##########################
    @staticmethod
    def _get_transform_in_engine(name) -> "Transform":
        actor = bpy.data.objects[name]
        location = tuple(actor.location)
        rotation = tuple(math.degrees(r) for r in actor.rotation_euler)  # convert to degrees
        scale = tuple(actor.scale)
        return location, rotation, scale

    @staticmethod
    def _get_location_in_engine(name) -> "Vector":
        return tuple(bpy.data.objects[name].location)

    @staticmethod
    def _get_rotation_in_engine(name) -> "Vector":
        return tuple(math.degrees(r) for r in bpy.data.objects[name].rotation_euler)  # convert to degrees

    @staticmethod
    def _get_scale_in_engine(name) -> "Vector":
        return tuple(bpy.data.objects[name].scale)

    @staticmethod
    def _get_all_objects_in_engine() -> list[str]:
        return bpy.data.objects.keys()

    ##########################
    # ------- Setter ------- #
    ##########################
    @staticmethod
    def _set_transform_in_engine(name: str, location: "Vector", rotation: "Vector", scale: "Vector"):
        actor = bpy.data.objects[name]
        actor.location = location
        actor.rotation_euler = [math.radians(r) for r in rotation]  # convert to radians
        actor.scale = scale

    @staticmethod
    def _set_location_in_engine(name: str, location: "Vector"):
        actor = bpy.data.objects[name]
        actor.location = location

    @staticmethod
    def _set_rotation_in_engine(name: str, rotation: "Vector"):
        actor = bpy.data.objects[name]
        actor.rotation_euler = [math.radians(r) for r in rotation]  # convert to radians

    @staticmethod
    def _set_scale_in_engine(name: str, scale: "Vector"):
        bpy.data.objects[name].scale = scale

    @staticmethod
    def _set_name_in_engine(name: str, new_name: str):
        bpy.data.objects[name].name = new_name

    @staticmethod
    @abstractmethod
    def _set_pass_index_in_engine(name: str, index: int):
        object = bpy.data.objects[name]
        object.pass_index = index
        for child in object.children:
            child.pass_index = index

    @staticmethod
    def _set_keyframe_in_engine(
        obj_name: str,
        transform_keys: "List[Dict]",
    ) -> None:
        obj = bpy.data.objects[obj_name]
        for i, key in enumerate(transform_keys):
            ## insert keyframes
            # https://docs.blender.org/api/current/bpy.types.bpy_struct.html
            obj.location = key["location"]
            obj.rotation_euler = key["rotation"]
            obj.keyframe_insert(data_path="location", frame=key["frame"])
            obj.keyframe_insert(data_path="rotation_euler", frame=key["frame"])

            ## set interpolation mode
            # https://blender.stackexchange.com/questions/260149/set-keyframe-interpolation-constant-while-setting-a-keyframe-in-blender-python
            if obj.animation_data.action:
                obj_action = bpy.data.actions.get(obj.animation_data.action.name)
                obj_location_fcurve = obj_action.fcurves.find("location")
                obj_location_fcurve.keyframe_points[i].interpolation = transform_keys[i]["interpolation"]
                obj_rotation_fcurve = obj_action.fcurves.find("rotation_euler")
                obj_rotation_fcurve.keyframe_points[i].interpolation = transform_keys[i]["interpolation"]

    @contextmanager
    @staticmethod
    def __judge__(name: str, scene: "bpy.types.Scene", import_path: "Optional[str]" = None):
        old_objs = set(scene.objects)
        yield
        new_objs = list(set(scene.objects) - old_objs)
        if not new_objs:
            if import_path:
                raise ValueError(f"Failed to import from '{import_path}'")
            else:
                raise ValueError(f"Failed to spawn '{name}'.")
        elif len(new_objs) == 1:
            new_objs[0].name = name
        elif len(new_objs) >= 2:
            obj_types = [obj.data.__class__.__name__ for obj in new_objs]
            if 'Armature' in obj_types and 'Mesh' in obj_types:
                new_objs[obj_types.index('Armature')].name = name
        #     else:
        #         # TODO: how to express this error
        #         raise ValueError(f"Unspport file")
        # else:
        #     raise ValueError(f"Unspport file")

    ##########################
    # ------- Delete ------- #
    ##########################
    @staticmethod
    def _delete_obj_in_engine(name):
        bpy.data.objects.remove(bpy.data.objects[name])

    # https://blender.stackexchange.com/questions/192871/how-to-delete-all-objects-cameras-meshes-etc-using-python-scripting
    @staticmethod
    def delete_all():
        """
        Deletes all objects/collections/scenes in the current blend file
        """
        # Delete all objects
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)

        # Delete all collections
        for coll in bpy.data.collections:
            bpy.data.collections.remove(coll)

        # Delete all scenes
        for scene in bpy.data.scenes[:-1]:
            bpy.data.scenes.remove(scene)

    ##########################
    # -------- IO ---------- #
    ##########################

    @staticmethod
    def _import_actor_from_file_in_engine(
        path: str,
        name: str,
        collection_name: str = "XRFeitoria",
    ) -> None:
        # TODO: import to collection, same as camera
        if collection_name not in bpy.data.collections.keys():
            raise ValueError(f"Invalid collection_name, '{collection_name}' does not exists.")

        if collection_name == default_level_blender:
            scene = BlenderSceneCollectionUtils.get_scene(default_level_blender)
        else:
            scene = BlenderSceneCollectionUtils.get_active_scene()

        collection = BlenderSceneCollectionUtils.get_collection(collection_name)

        # link the 'collection' to 'scene' if collection dose not belongs to 'scene'
        tmp_link = False
        if collection_name not in scene.collection.children.keys():
            BlenderSceneCollectionUtils.link_collection_to_scene(collection, scene)
            tmp_link = True

        # set 'collection' and 'scene' active
        BlenderSceneCollectionUtils.set_scene_active(scene)
        BlenderSceneCollectionUtils.set_collection_active(collection)

        with ObjectUtilsBlender.__judge__(name=name, import_path=path, scene=scene):
            file_type = Path(path).suffix[1:].lower()  # remove dot, lower case
            file_type = ImportFileFormatEnum[file_type]

            if file_type == ImportFileFormatEnum.fbx:
                ImportFunctions.import_fbx(fbx_file=path)
            elif file_type == ImportFileFormatEnum.obj:
                ImportFunctions.import_obj(obj_file=path)
            elif file_type == ImportFileFormatEnum.abc:
                ImportFunctions.import_alembic(alembic_file=path)
            else:
                raise NotImplementedError(f"File type {file_type} not supported")

        # unlink 'collection' from 'scene' if necessary
        if tmp_link:
            BlenderSceneCollectionUtils.unlink_collection_from_scene(collection, scene)

    @staticmethod
    def _import_animation_from_file_in_engine(animation_path: "PathLike", name: str, action_name: str = None) -> None:
        # TODO: import animation
        # import animation and apply animation to armature
        anim_file_ext = Path(animation_path).suffix
        if anim_file_ext.lower() == ".json":
            ImportFunctions.import_mo_json(mo_json_file=animation_path, actor_name=name)
        elif anim_file_ext.lower() == ".blend":
            ImportFunctions.import_mo_blend(mo_blend_file=animation_path, actor_name=name, action_name=action_name)
        elif anim_file_ext.lower() == ".fbx":
            ImportFunctions.import_mo_fbx(mo_fbx_file=animation_path, actor_name=name)
        else:
            raise TypeError(f"Invalid anim file, expected 'json', 'blend', or 'fbx' (got {anim_file_ext[1:]} instead).")


@remote_unreal_decorator_class
class ObjectUtilsUnreal(ObjectUtilsBase):
    @staticmethod
    def _get_transform_in_engine(name: str) -> "Transform":
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = actor.get_actor_location().to_tuple()
        rotation = actor.get_actor_rotation().to_tuple()
        scale = actor.get_actor_scale3d().to_tuple()
        return location, rotation, scale

    @staticmethod
    def _get_location_in_engine(name) -> "Vector":
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        actor_location = actor.get_actor_location()
        return actor_location.to_tuple()

    @staticmethod
    def _get_rotation_in_engine(name) -> "Vector":
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        actor_rotation = actor.get_actor_rotation()
        return actor_rotation.to_tuple()

    @staticmethod
    def _get_scale_in_engine(name) -> "Vector":
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        actor_scale = actor.get_actor_scale3d()
        return actor_scale.to_tuple()

    @staticmethod
    def _get_all_objects_in_engine() -> list[str]:
        return XRFeitoriaUnrealFactory.utils_actor.get_all_actors_name()

    @staticmethod
    def _set_transform_in_engine(name: str, location: "Vector", rotation: "Vector", scale: "Vector") -> None:
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = unreal.Vector(location[0], location[1], location[2])
        # location /= 100  # convert from cm to m
        rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2])
        actor.set_actor_transform(unreal.Transform(location, rotation, scale), False, False)

    @staticmethod
    def _set_location_in_engine(name: str, location: "Vector") -> None:
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        location = unreal.Vector(location[0], location[1], location[2])
        # location /= 100  # convert from cm to m
        actor.set_actor_location(location, False, False)

    @staticmethod
    def _set_rotation_in_engine(name: str, rotation: "Vector") -> None:
        actor = XRFeitoriaUnrealFactory.utils_actor.get_actor_by_name(name)
        rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2])
        actor.set_actor_rotation(rotation, False)

    @staticmethod
    def _set_scale_in_engine(name, scale: "Vector") -> None:
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
    def _import_actor_from_file_in_engine(path: str, name: str) -> None:
        raise NotImplementedError


######################
# ----- Import ----- #
######################


class ImportFunctions:
    ##########################
    # ------- Meshes ------- #
    ##########################
    @staticmethod
    def import_fbx(fbx_file: str) -> None:
        # import fbx
        try:
            bpy.ops.import_scene.fbx(filepath=str(fbx_file))
        except Exception as e:
            raise Exception(f"Failed to import fbx: {fbx_file}\n{e}")

    @staticmethod
    def import_obj(obj_file: str) -> None:
        # import obj
        try:
            bpy.ops.import_scene.obj(filepath=str(obj_file))
        except Exception:
            raise Exception(f"Failed to import obj: {obj_file}")

    @staticmethod
    def import_alembic(alembic_file: str) -> None:
        """import an existing alembic animation into blender"""
        try:
            bpy.ops.wm.alembic_import(filepath=str(alembic_file), relative_path=False, as_background_job=False)
        except Exception as e:
            raise Exception(f"Failed to import alembic: {alembic_file}, error: {e}")

    @classmethod
    def import_mo_json(
        cls,
        mo_json_file: Path,
        actor_name: str,
    ) -> None:
        motion_data = json.load(Path(mo_json_file).open("r"))
        action = bpy.data.actions.new("Action")
        object = bpy.data.objects[actor_name]
        cls._apply_action_to_object(action, object)
        cls._apply_motion_data_to_action(motion_data=motion_data, action=action)

    @classmethod
    def import_mo_blend(
        cls,
        mo_blend_file: Path,
        action_name: str,
        actor_name: str,
    ) -> None:
        with bpy.data.libraries.load(mo_blend_file) as (data_from, data_to):
            data_to.actions.append(action_name)
        action = bpy.data.actions[action_name]
        object = bpy.data.objects[actor_name]
        cls._apply_action_to_object(action, object)

    @classmethod
    def import_mo_fbx(
        cls,
        mo_fbx_file: Path,
        actor_name: str,
    ) -> None:
        mo_object_name = "tmp_import_action"
        with ObjectUtilsBlender.__judge__(
            name=mo_object_name, import_path=mo_fbx_file, scene=BlenderSceneCollectionUtils.get_active_scene()
        ):
            ImportFunctions.import_fbx(mo_fbx_file)
        action = bpy.data.objects[mo_object_name].animation_data.action
        object = bpy.data.objects[actor_name]
        cls._apply_action_to_object(action, object)
        bpy.data.objects.remove(bpy.data.objects[mo_object_name])

    @staticmethod
    def _apply_action_to_object(action: "bpy.types.Action", object: "bpy.types.Object") -> None:
        if object.animation_data:
            object.animation_data_clear()
        object.animation_data_create()
        object.animation_data.action = action

    @staticmethod
    def _apply_motion_data_to_action(
        motion_data: List[Dict[str, Dict]],
        # armature: "bpy.types.Armature",
        action: "bpy.types.Action",
        scale: float = 1.0,
    ) -> None:
        num_frames = len(motion_data)
        fcurves_map = {(fc.data_path, fc.array_index): fc for fc in action.fcurves}

        def _get_fcurve(data_path: str, index: int):
            key_ = (data_path, index)
            if key_ in fcurves_map:
                fcurve = fcurves_map[key_]
            else:
                fcurve = fcurves_map.setdefault(key_, action.fcurves.new(data_path, index=index))
                # fcurve.keyframe_points.add(num_frames)
            return fcurve

        # Set keyframes
        frames_iter = range(num_frames)
        loc0 = [0, 0, 0]
        for f in frames_iter:
            for bone_name in motion_data[0].keys():
                # rotation_quaternion
                data_path = f'pose.bones["{bone_name}"].rotation_quaternion'
                motion = motion_data[f][bone_name]
                for idx, val in enumerate(motion["rotation"]):
                    fcurve = _get_fcurve(data_path=data_path, index=idx)
                    # fcurve.keyframe_points[f].co = (f, val)
                    fcurve.keyframe_points.insert(frame=f, value=val, options={"FAST"})
                    # if bone_name == "left_shoulder":
                    #     print(f, [list(x.co) for x in fcurve.keyframe_points])
                # location
                if "location" in motion:
                    data_path = f'pose.bones["{bone_name}"].location'
                    location_ = motion["location"]
                    if f < 1:
                        loc0 = location_
                        location_ = np.zeros(3)
                    else:
                        location_ = np.subtract(location_, loc0) * scale
                    for idx, val in enumerate(location_):
                        fcurve = _get_fcurve(data_path=data_path, index=idx)
                        # fcurve.keyframe_points[f].co = (f, val)
                        fcurve.keyframe_points.insert(frame=f, value=val, options={"FAST"})
