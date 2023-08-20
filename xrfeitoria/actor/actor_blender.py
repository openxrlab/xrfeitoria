from typing import Dict, List, Optional, Union

from .. import default_level_blender
from ..constants import PathLike, SequenceTransformKey, Vector
from ..object import ObjectBase, ObjectUtilsBlender
from ..rpc import remote_class_blender
from ..utils import BlenderSceneCollectionUtils, Validator
from . import ActorBase

try:
    import bpy
except ModuleNotFoundError:
    pass


@remote_class_blender
class ActorBlender(ActorBase):
    _object_utils = ObjectUtilsBlender

    @classmethod
    def import_actor_from_file(
        cls,
        path: str,
        collection_name: str = default_level_blender,
        name: Optional[str] = None,
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        scale: "Vector" = (1, 1, 1),
        stencil_value: int = 1,
    ) -> "ActorBase":
        cls._object_utils.validate_new_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_vector(scale, 3)

        cls._object_utils.import_actor_from_file(path=path, name=name, collection_name=collection_name)
        cls._object_utils._set_pass_index_in_engine(name, stencil_value)
        actor = cls(name)
        actor.set_transform(location, rotation, scale)
        return actor

    @classmethod
    def import_actor_from_file_with_keys(
        cls,
        name: str,
        path: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        stencil_value: int = 1,
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        actor = cls.import_actor_from_file_to_collection(name=name, path=path, collection_name=collection_name)
        cls._object_utils._set_keyframe_in_engine(obj_name=name, transform_keys=transform_keys)
        cls._object_utils._set_pass_index_in_engine(name=name, index=stencil_value)
        return actor

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _spawn_actor_in_engine(name: str, location: Vector, rotation: Vector) -> None:
        raise NotImplementedError


@remote_class_blender
class MeshBlender(ObjectBase):
    _object_utils = ObjectUtilsBlender

    @classmethod
    def spawn_cube(
        cls,
        name: str,
        collection_name: str = default_level_blender,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        size: int = 1,
        stencil_value: int = 1,
    ) -> "MeshBlender":
        return cls.spawn_mesh(name, "cube", collection_name, location, rotation, scale, stencil_value, size=size)

    @classmethod
    def spawn_plane(
        cls,
        name: str,
        collection_name: str = default_level_blender,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
        size: int = 1,
    ) -> "MeshBlender":
        return cls.spawn_mesh(name, "plane", collection_name, location, rotation, scale, stencil_value, size=size)

    @classmethod
    def spawn_uv_sphere(
        cls,
        name: str,
        stencil_value: int = 1,
        collection_name: str = default_level_blender,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        segments: int = 32,
        ring_count: int = 16,
    ) -> "MeshBlender":
        return cls.spawn_mesh(
            name,
            "uv_sphere",
            collection_name,
            location,
            rotation,
            scale,
            stencil_value,
            segments=segments,
            ring_count=ring_count,
        )

    @classmethod
    def spawn_ico_sphere(
        cls,
        name: str,
        collection_name: str = default_level_blender,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
        subdivisions: int = 2,
    ) -> "MeshBlender":
        return cls.spawn_mesh(
            name, "ico_sphere", collection_name, location, rotation, scale, stencil_value, subdivisions=subdivisions
        )

    @classmethod
    def spawn_cylinder(
        cls,
        name: str,
        collection_name: str = default_level_blender,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
        vertices: int = 32,
    ) -> "MeshBlender":
        return cls.spawn_mesh(
            name, "cylinder", collection_name, location, rotation, scale, stencil_value, vertices=vertices
        )

    @classmethod
    def spawn_cone(
        cls,
        name: str,
        collection_name: str = default_level_blender,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
        vertices: int = 32,
        radius1: int = 1,
        radius2: int = 0,
    ) -> "MeshBlender":
        return cls.spawn_mesh(
            name,
            "cone",
            collection_name,
            location,
            rotation,
            scale,
            stencil_value,
            vertices=vertices,
            radius1=radius1,
            radius2=radius2,
        )

    @classmethod
    def spawn_mesh(
        cls,
        name: str,
        mesh_type: str,
        collection_name: str = default_level_blender,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
        **kwargs,
    ) -> "MeshBlender":
        cls._object_utils.validate_new_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_vector(scale, 3)

        cls._object_utils.validate_new_name(name)
        cls._spawn_mesh_in_engine(name, mesh_type, collection_name, **kwargs)
        cls._object_utils._set_pass_index_in_engine(name, stencil_value)
        mesh = cls(name=name)
        mesh.set_transform(location, rotation, scale)
        return mesh

    @classmethod
    def spawn_cube_with_keys(
        cls,
        name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        stencil_value: int = 1,
        size: int = 1,
    ) -> "MeshBlender":
        return cls.spawn_mesh_with_keys(name, "cube", transform_keys, collection_name, stencil_value, size=size)

    @classmethod
    def spawn_plane_with_keys(
        cls,
        name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        stencil_value: int = 1,
        size: int = 1,
    ) -> "MeshBlender":
        return cls.spawn_mesh_with_keys(name, "plane", transform_keys, collection_name, stencil_value, size=size)

    @classmethod
    def spawn_uv_sphere_with_keys(
        cls,
        name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        stencil_value: int = 1,
        segments: int = 32,
        ring_count: int = 16,
    ) -> "MeshBlender":
        return cls.spawn_mesh_with_keys(
            name, "uv_sphere", transform_keys, collection_name, stencil_value, segments=segments, ring_count=ring_count
        )

    @classmethod
    def spawn_ico_sphere_with_keys(
        cls,
        name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        stencil_value: int = 1,
        subdivisions: int = 2,
    ) -> "MeshBlender":
        return cls.spawn_mesh_with_keys(
            name, "ico_sphere", transform_keys, collection_name, stencil_value, subdivisions=subdivisions
        )

    @classmethod
    def spawn_cylinder_with_keys(
        cls,
        name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        stencil_value: int = 1,
        vertices: int = 32,
    ) -> "MeshBlender":
        return cls.spawn_mesh_with_keys(
            name, "cylinder", transform_keys, collection_name, stencil_value, vertices=vertices
        )

    @classmethod
    def spawn_cone_with_keys(
        cls,
        name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        stencil_value: int = 1,
        vertices: int = 32,
        radius1: int = 1.0,
        radius2: int = 2.0,
    ) -> "MeshBlender":
        return cls.spawn_mesh_with_keys(
            name,
            "cone",
            transform_keys,
            collection_name,
            stencil_value,
            vertices=vertices,
            radius1=radius1,
            radius2=radius2,
        )

    @classmethod
    def spawn_mesh_with_keys(
        cls,
        name: str,
        mesh_type: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        collection_name: str = default_level_blender,
        stencil_value: int = 1,
        **kwargs,
    ) -> "MeshBlender":
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        mesh = cls.spawn_mesh(
            name=name,
            mesh_type=mesh_type,
            collection_name=collection_name,
            **kwargs,
        )
        cls._object_utils._set_keyframe_in_engine(obj_name=name, transform_keys=transform_keys)
        cls._object_utils._set_pass_index_in_engine(name, stencil_value)
        return mesh

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _spawn_mesh_in_engine(
        name: str,
        mesh_type: str,
        collection_name: str,
        segments: "Optional[int]" = None,
        ring_count: "Optional[int]" = None,
        subdivisions: "Optional[int]" = None,
        vertices: "Optional[int]" = None,
        radius1: "Optional[int]" = None,
        radius2: "Optional[int]" = None,
        size: int = 1,
    ) -> None:
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

        # spawn mesh
        with ObjectUtilsBlender.__judge__(name, scene=scene):
            if mesh_type == "plane":
                bpy.ops.mesh.primitive_plane_add(size=size)
            elif mesh_type == "cube":
                bpy.ops.mesh.primitive_cube_add(size=size)
            elif mesh_type == "uv_sphere":
                bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=ring_count)
            elif mesh_type == "ico_sphere":
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions)
            elif mesh_type == "cylinder":
                bpy.ops.mesh.primitive_cylinder_add(vertices=vertices)
            elif mesh_type == "cone":
                bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2)
            else:
                raise TypeError(
                    f"Unspported mesh type, expected 'plane', 'cube', 'uv_sphere', 'ico_sphere', 'cylinder' or 'cone', (got '{mesh_type}' instead)."
                )
        # unlink 'collection' from 'scene' if necessary
        if tmp_link:
            BlenderSceneCollectionUtils.unlink_collection_from_scene(collection, scene)
