import os
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Optional, Union

from loguru import logger

from ..actor import ActorBlender, MeshBlender
from ..camera import CameraBlender, CameraUtils
from ..constants import PathLike, SequenceTransformKey, Vector, default_level_blender
from ..rpc import remote_class_blender
from ..utils import BlenderSceneCollectionUtils, blender_functions
from .sequence_base import SequenceBase

try:
    import bpy
except ModuleNotFoundError:
    pass


@contextmanager
def new_sequence_blender(
    seq_name: str,
    seq_fps: "Optional[float]" = None,
    seq_length: "Optional[int]" = None,
    hdr_map_path: "Optional[PathLike]" = None,
    link_default: bool = True,
    link_collections: Optional[Union[List[str], str]] = [],
    save_blend_path: Optional[PathLike] = None,
    replace: bool = False,
) -> "Generator[SequenceBlender, None, None]":
    if not isinstance(link_collections, list):
        link_collections = [link_collections]
    if link_default:
        link_collections.append(default_level_blender)

    SequenceBlender.new_seq(
        seq_name=seq_name,
        link_collections=link_collections,
        hdr_map_path=hdr_map_path,
        seq_fps=seq_fps,
        seq_length=seq_length,
        replace=replace,
    )
    logger.info(f"created new sequence at blender scene '{seq_name}'")
    yield SequenceBlender
    SequenceBlender.close_seq()
    if save_blend_path:
        blender_functions.save_blend(save_blend_path=save_blend_path)


@contextmanager
def open_sequence_blender(
    seq_name: str,
    seq_fps: "Optional[float]" = None,
    seq_length: "Optional[int]" = None,
) -> "Generator[SequenceBlender, None, None]":
    SequenceBlender.open_seq(
        seq_name=seq_name,
        seq_fps=seq_fps,
        seq_length=seq_length,
    )
    logger.info(f"created new sequence at blender scene '{seq_name}'")
    yield
    SequenceBlender.close_seq()


@remote_class_blender
class SequenceBlender(SequenceBase):
    name = "Sequence"

    @classmethod
    def new_seq(
        cls,
        seq_name: str,
        hdr_map_path: "Optional[PathLike]" = None,
        link_collections: List[str] = [],
        seq_fps: "Optional[float]" = None,
        seq_length: "Optional[int]" = None,
        replace: bool = False,
        # TODO: add replace option
    ) -> None:
        cls.name = seq_name
        cls._new_seq_in_engine(
            seq_name=seq_name,
            link_collections=link_collections,
            seq_fps=seq_fps,
            seq_length=seq_length,
            replace=replace,
        )
        if hdr_map_path:
            assert Path(hdr_map_path).exists(), f"hdr map '{hdr_map_path}' does not exist"
            cls._set_hdr_map_in_engine(seq_name=seq_name, hdr_map_path=hdr_map_path)

    @classmethod
    def open_seq(cls, seq_name: str) -> None:
        cls.name = seq_name
        cls._open_seq_in_engine(seq_name=seq_name)

    @classmethod
    def close_seq(cls) -> None:
        cls.name = default_level_blender
        cls._close_seq_in_engine()

    @classmethod
    def spawn_camera(
        cls,
        name: str,
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        fov: float = 90.0,
    ) -> "CameraBlender":
        return CameraBlender.spawn_camera(
            name=name, collection_name=cls.name, location=location, rotation=rotation, fov=fov
        )

    @classmethod
    def spawn_camera_with_keys(
        cls,
        name: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        fov: float = 90.0,
    ) -> "CameraBlender":
        return CameraBlender.spawn_camera_with_keys(
            name=name, collection_name=cls.name, transform_keys=transform_keys, fov=fov
        )

    @classmethod
    def spawn_actor(
        cls,
        name: str,
        actor_asset_path: "PathLike",
        location: "Vector" = (0, 0, 0),
        rotation: "Vector" = (0, 0, 0),
        scale: "Vector" = (1, 1, 1),
        stencil_value: int = 1,
    ) -> "ActorBlender":
        return ActorBlender.import_actor_from_file(
            name=name,
            path=actor_asset_path,
            location=location,
            rotation=rotation,
            scale=scale,
            collection_name=cls.name,
            stencil_value=stencil_value,
        )

    @classmethod
    def spawn_actor_with_keys(
        cls,
        actor_name: str,
        actor_asset_path: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        stencil_value: int = 1,
    ) -> "ActorBlender":
        return ActorBlender.import_actor_from_file_with_keys(
            name=actor_name,
            path=actor_asset_path,
            collection_name=cls.name,
            transform_keys=transform_keys,
            stencil_value=stencil_value,
        )

    @classmethod
    def spawn_mesh(
        cls,
        mesh_name: str,
        mesh_type: str,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
        **kwargs,
    ) -> "MeshBlender":
        return MeshBlender.spawn_mesh(
            name=mesh_name,
            mesh_type=mesh_type,
            location=location,
            rotation=rotation,
            scale=scale,
            collection_name=cls.name,
            stencil_value=stencil_value,
            **kwargs,
        )

    @classmethod
    def spawn_mesh_with_keys(
        cls,
        mesh_name: str,
        mesh_type: str,
        transform_keys: "Union[List[SequenceTransformKey], SequenceTransformKey]",
        stencil_value: int = 1,
        **kwargs,
    ) -> "MeshBlender":
        return MeshBlender.spawn_mesh_with_keys(
            name=mesh_name,
            mesh_type=mesh_type,
            collection_name=cls.name,
            transform_keys=transform_keys,
            stencil_value=stencil_value,
            **kwargs,
        )

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

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

    @staticmethod
    def _set_hdr_map_in_engine(
        seq_name: str,
        hdr_map_path: str,
    ):
        scene = BlenderSceneCollectionUtils.get_scene(seq_name)
        scene = bpy.data.scenes[seq_name]
        scene_world = bpy.data.worlds.new(name=seq_name)
        scene.world = scene_world
        scene.world.use_nodes = True
        tree = scene.world.node_tree
        links = tree.links
        for node in tree.nodes:
            tree.nodes.remove(node)

        environment_texture_node = tree.nodes.new("ShaderNodeTexEnvironment")
        background_node = tree.nodes.new("ShaderNodeBackground")
        world_output_node = tree.nodes.new("ShaderNodeOutputWorld")

        links.new(environment_texture_node.outputs[0], background_node.inputs[0])
        links.new(background_node.outputs[0], world_output_node.inputs[0])

        environment_texture_node.image = bpy.data.images.load(hdr_map_path)

    @staticmethod
    def _new_seq_in_engine(
        seq_name: str,
        link_collections: "Optional[Union[List[str],str]]" = [],
        seq_fps: "Optional[float]" = None,
        seq_length: "Optional[int]" = None,
        replace: bool = False,
    ) -> None:
        if seq_name in bpy.data.scenes.keys() or seq_name in bpy.data.collections.keys():
            if replace:
                BlenderSceneCollectionUtils.delete_sequence(seq_name)
            else:
                raise ValueError(f"Invalid name, Sequence '{seq_name}' already exists.")

        # new scene named seq_name
        new_seq_scene = BlenderSceneCollectionUtils.new_scene(seq_name)
        # new collection named seq_name
        new_seq_collection = BlenderSceneCollectionUtils.new_collection(seq_name)
        # link seq_name(collection) to seq_name(scene)
        BlenderSceneCollectionUtils.link_collection_to_scene(collection=new_seq_collection, scene=new_seq_scene)
        # link all collections in 'link_collections' to 'new_seq_scene'
        for coll in link_collections:
            coll = BlenderSceneCollectionUtils.get_collection(coll)
            BlenderSceneCollectionUtils.link_collection_to_scene(collection=coll, scene=new_seq_scene)
            CameraUtils.set_multiview(new_seq_scene)
            for obj in coll.objects:
                print(obj.data.__class__.__name__)
                if obj.data.__class__.__name__ == "Camera":
                    CameraUtils.add_multiview_camera(camera_name=obj.name, scene=new_seq_scene, active=False)
                    new_seq_scene.camera = obj

        new_seq_scene.frame_start = 0
        new_seq_scene.frame_end = seq_length
        new_seq_scene.render.fps = seq_fps
        # set scene to active
        BlenderSceneCollectionUtils.set_scene_active(new_seq_scene)
        # set collection to active
        BlenderSceneCollectionUtils.set_collection_active(new_seq_collection)

    @staticmethod
    def _open_seq_in_engine(seq_name: str) -> None:
        if seq_name not in bpy.data.scenes.keys():
            raise ValueError(f"Invalid name, Sequence '{seq_name}' does not exist.")
        seq_scene = BlenderSceneCollectionUtils.get_scene(seq_name)
        seq_collection = BlenderSceneCollectionUtils.get_collection(seq_name)
        # set scene to active
        BlenderSceneCollectionUtils.set_scene_active(seq_scene)
        # set collection to active
        BlenderSceneCollectionUtils.set_collection_active(seq_collection)

    @staticmethod
    def _close_seq_in_engine() -> None:
        default_scene = BlenderSceneCollectionUtils.get_scene(default_level_blender)
        default_collection = BlenderSceneCollectionUtils.get_collection(default_level_blender)
        BlenderSceneCollectionUtils.set_scene_active(default_scene)
        BlenderSceneCollectionUtils.set_collection_active(default_collection)

    @staticmethod
    def _show_seq_in_engine(seq_name: str) -> None:
        pass

    @staticmethod
    def _spawn_camera_in_engine(
        transform_keys: "Union[List[Dict], Dict]",
        fov: float = 90.0,
        camera_name: str = "Camera",
    ) -> None:
        pass

    @staticmethod
    def _spawn_actor_in_engine(
        actor_asset_path: str,
        transform_keys: "Union[List[Dict], Dict]",
        anim_asset_path: "Optional[str]" = None,
        actor_name: str = "Actor",
    ) -> None:
        pass
