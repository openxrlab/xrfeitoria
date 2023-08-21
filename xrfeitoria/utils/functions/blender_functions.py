from typing import Optional

from ...constants import PathLike
from ...rpc import remote_blender_decorator

try:
    import bpy
except ImportError:
    pass

# TODO: add import function that wouldn't raise an error


@remote_blender_decorator
def cleanup():
    bpy.ops.outliner.orphans_purge(do_local_ids=True)


@remote_blender_decorator
def save_blend(save_path: "Optional[PathLike]" = None, pack: bool = False):
    try:
        bpy.data.use_autopack = pack
    except Exception as e:
        raise Exception(f"Failed to set autopack: {e}")

    if save_path is None:
        save_path = bpy.data.filepath

    bpy.ops.wm.save_as_mainfile(filepath=save_path)


# --------- INIT  -----------
@remote_blender_decorator
def init_scene_and_collection(default_level_name: str, cleanup: bool = False) -> tuple:
    if default_level_name not in bpy.data.collections.keys():
        default_collection = BlenderSceneCollectionUtils.new_collection(default_level_name)
    else:
        default_collection = BlenderSceneCollectionUtils.get_collection(default_level_name)

    if default_level_name not in bpy.data.scenes.keys():
        if cleanup:
            default_scene = BlenderSceneCollectionUtils.get_active_scene()
            default_scene.name = default_level_name
        else:
            default_scene = BlenderSceneCollectionUtils.new_scene()
    else:
        default_scene = BlenderSceneCollectionUtils.get_scene(default_level_name)

    BlenderSceneCollectionUtils.link_collection_to_scene(default_collection, default_scene)
    BlenderSceneCollectionUtils.set_scene_active(default_scene)
    BlenderSceneCollectionUtils.set_collection_active(default_collection)


class BlenderSceneCollectionUtils:
    # --------- NEW  -----------
    def new_collection(name: str) -> "bpy.types.Collection":
        if name in bpy.data.collections:
            raise ValueError(f"Collection '{name}' already exists.")
        collection = bpy.data.collections.new(name)
        return collection

    def new_scene(name: str) -> "bpy.types.Scene":
        if name in bpy.data.scenes:
            raise ValueError(f"Scene '{name}' already exists.")
        scene = bpy.data.scenes.new(name)
        return scene

    # --------- GET  -----------
    def get_collection(name: str) -> "bpy.types.Collection":
        if name not in bpy.data.collections:
            raise ValueError(f"Collection '{name}' does not exists.")
        return bpy.data.collections[name]

    def get_scene(name: str) -> "bpy.types.Scene":
        if name not in bpy.data.scenes:
            raise ValueError(f"Scene '{name}' does not exists.")
        return bpy.data.scenes[name]

    def get_active_scene() -> "bpy.types.Scene":
        return bpy.context.scene

    # --------- SET  -----------
    def set_scene_active(scene: "bpy.types.Scene") -> None:
        bpy.context.window.scene = scene

    def set_collection_active(collection: "bpy.types.Collection") -> None:
        layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]
        bpy.context.view_layer.active_layer_collection = layer_collection

    # --------- LINK  -----------
    def link_collection_to_collection(
        child_collection: "bpy.types.Collection",
        parent_collection: "bpy.types.Collection",
    ) -> None:
        if child_collection.name not in parent_collection.children.keys():
            parent_collection.children.link(child_collection)

    def link_collection_to_scene(
        collection: "bpy.types.Collection",
        scene: "bpy.types.Scene",
    ) -> None:
        if collection.name not in scene.collection.children.keys():
            scene.collection.children.link(collection)

    def unlink_collection_from_scene(
        collection: "bpy.types.Collection",
        scene: "bpy.types.Scene",
    ) -> None:
        if collection.name in scene.collection.children.keys():
            scene.collection.children.unlink(collection)

    # --------- DELETE  -----------
    def delete_sequence(seq_name: str) -> None:
        if seq_name in bpy.data.collections.keys():
            # delete all objects in seq_collection
            seq_collection = bpy.data.collections[seq_name]
            for obj in seq_collection.objects:
                bpy.data.objects.remove(obj)
            # delete seq_collection
            bpy.data.collections.remove(seq_collection)

        if seq_name in bpy.data.scenes.keys():
            # unlink other collections from seq_scene
            seq_scene = bpy.data.scenes[seq_name]
            for coll in seq_scene.collection.children:
                # cls.unlink_collection_from_scene(coll, seq_scene)
                seq_scene.collection.children.unlink(coll)
            # delete other objects in seq_scene
            for obj in seq_scene.objects:
                bpy.data.objects.remove(obj)
            # delete seq_scene
            bpy.data.scenes.remove(seq_scene)
