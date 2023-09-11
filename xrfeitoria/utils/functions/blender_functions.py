"""Remote functions for blender."""

from pathlib import Path
from typing import List, Literal, Tuple

from ...data_structure.constants import ImportFileFormatEnum, PathLike, Vector
from ...rpc import remote_blender

try:
    # only for linting, not imported in runtime
    import bpy
    from XRFeitoriaBpy import logger  # defined in src/XRFeitoriaBpy/__init__.py
    from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory  # defined in src/XRFeitoriaBpy/core/factory.py
except ImportError:
    pass


@remote_blender()
def import_file(file_path: 'PathLike') -> None:
    """Import file to blender. This function will not return an instance of the imported actor.
    The file type is determined by the file extension.
    Supported file types: fbx, obj, abc, ply, stl.

    Note:
        For fbx file, only support binary format. ASCII format is not supported.
        Ref: https://docs.blender.org/manual/en/3.6/addons/import_export/scene_fbx.html#id4
    """
    file_type = Path(file_path).suffix[1:].lower()  # remove dot, lower case
    try:
        file_type = ImportFileFormatEnum[file_type]
    except KeyError:
        raise TypeError(f'File type {file_type} not supported')

    if file_type == ImportFileFormatEnum.fbx:
        XRFeitoriaBlenderFactory.import_fbx(fbx_file=file_path)
    elif file_type == ImportFileFormatEnum.obj:
        XRFeitoriaBlenderFactory.import_obj(obj_file=file_path)
    elif file_type == ImportFileFormatEnum.abc:
        XRFeitoriaBlenderFactory.import_alembic(alembic_file=file_path)
    elif file_type == ImportFileFormatEnum.ply:
        XRFeitoriaBlenderFactory.import_ply(ply_file=file_path)
    elif file_type == ImportFileFormatEnum.stl:
        XRFeitoriaBlenderFactory.import_stl(stl_file=file_path)


@remote_blender()
def is_background_mode(warning: bool = False) -> bool:
    """Check whether Blender is running in background mode.

    Returns:
        bool: True if Blender is running in background mode.
    """
    _mode = bpy.app.background
    if warning and _mode:
        from XRFeitoriaBpy import logger

        logger.warning('Properties (location, rotation, scale, etc.) cannot be guaranteed in background mode.')
    return _mode


@remote_blender()
def cleanup_unused():
    """Cleanup all the unused data in the current blend file."""
    bpy.ops.outliner.orphans_purge(do_local_ids=True)


@remote_blender()
def save_blend(save_path: 'PathLike' = None, pack: bool = False):
    """Save the current blend file to the given path.

    Args:
        save_path (PathLike, optional): Path to save the blend file. Defaults to None.
        pack (bool, optional): Automatically pack all external data into .blend file. Defaults to False.

    Raises:
        Exception: Failed to set autopack.
    """
    try:
        bpy.data.use_autopack = pack
    except Exception as e:
        raise Exception(f'Failed to set autopack: {e}')

    # fallback to current file path
    if save_path is None:
        save_path = bpy.data.filepath

    # set suffix to .blend
    save_path = Path(save_path).resolve()
    if save_path.suffix != '.blend':
        save_path = save_path.with_suffix('.blend')

    save_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=save_path.as_posix())


@remote_blender()
def set_env_color(color: 'Tuple[float, float, float, float]', intensity: float = 1.0):
    """Set the color of the environment light.

    Args:
        color (Tuple[float, float, float, float]): RGBA color of the environment light.
        intensity (float, optional): Intensity of the environment light. Defaults to 1.0.
    """
    scene = XRFeitoriaBlenderFactory.get_active_scene()
    scene_world = bpy.data.worlds.new(name=scene.name)
    scene.world = scene_world
    scene.world.use_nodes = True
    node = scene.world.node_tree.nodes['Background']
    node.inputs['Color'].default_value = color
    node.inputs['Strength'].default_value = intensity


@remote_blender()
def set_hdr_map(hdr_map_path: 'PathLike') -> None:
    """Set HDR map of the active scene.

    Args:
        hdr_map_path ('PathLike'): Path of the HDR map file.
    """
    scene = XRFeitoriaBlenderFactory.get_active_scene()
    XRFeitoriaBlenderFactory.set_hdr_map(scene=scene, hdr_map_path=hdr_map_path)


@remote_blender()
def get_frame_range() -> 'Tuple[int, int]':
    """Get the frame range of the active scene.

    Returns:
        Tuple[int, int]: Start frame and End frame.
    """
    scene = XRFeitoriaBlenderFactory.get_active_scene()
    return XRFeitoriaBlenderFactory.get_frame_range(scene)


@remote_blender()
def set_frame_range(start: int, end: int) -> None:
    """Set frame range of the active scene.

    Args:
        start (int): Start frame.
        end (int): End frame.
    """
    logger.info(f'Override frame range to [{start}, {end}]')
    scene = XRFeitoriaBlenderFactory.get_active_scene()
    XRFeitoriaBlenderFactory.set_frame_range(scene=scene, start=start, end=end)


@remote_blender()
def set_frame_current(frame: int) -> None:
    """Set current frame of the active scene.

    Args:
        frame (int): Frame number.
    """
    scene = XRFeitoriaBlenderFactory.get_active_scene()
    XRFeitoriaBlenderFactory.set_frame_current(scene=scene, frame=frame)


@remote_blender()
def get_keys_range() -> 'Tuple[int, int]':
    """Get the max keyframe range of all the objects in the active scene.

    Returns:
        Tuple[int, int]: Start frame and End frame.
    """
    scene = XRFeitoriaBlenderFactory.get_active_scene()
    return XRFeitoriaBlenderFactory.get_keys_range(scene)


@remote_blender()
def get_all_object_in_seq(seq_name: str, obj_type: 'Literal["MESH", "ARMATURE", "CAMERA"]') -> 'List[str]':
    """Get all the objects in the given sequence.

    Args:
        seq_name (str): Name of the sequence.
        obj_type (Literal[&quot;MESH&quot;, &quot;ARMATURE&quot;, &quot;CAMERA&quot;]): Object type.

    Returns:
        List[str]: List of object names.
    """
    return XRFeitoriaBlenderFactory.get_all_object_in_seq(seq_name=seq_name, obj_type=obj_type)


@remote_blender()
def get_all_object_in_current_level(obj_type: 'Literal["MESH", "ARMATURE", "CAMERA"]') -> 'List[str]':
    """Get all the objects in the current level.

    Args:
        obj_type (Literal["MESH";, "ARMATURE";, "CAMERA";]): Object type.

    Returns:
        List[str]: List of object names.
    """
    return XRFeitoriaBlenderFactory.get_all_object_in_current_level(obj_type=obj_type)


@remote_blender()
def new_level(name: str) -> None:
    """Create a new level.

    Args:
        name (str): Name of the level.
    """
    level_scene = XRFeitoriaBlenderFactory.new_scene(name)
    level_collection = XRFeitoriaBlenderFactory.new_collection(name)
    XRFeitoriaBlenderFactory.link_collection_to_scene(level_collection, level_scene)


@remote_blender()
def export_vertices(export_path: 'PathLike', use_animation: bool = True) -> None:
    """Export vertices in the world space of all objects in the active scene to npz
    file, with animation (export N frame) if use_animation is True. export_path will be
    an npz file with a single key 'verts' which is a numpy array in shape of (N, V, 3),
    where N is the number of frames, V is the number of vertices.

    Args:
        export_path (PathLike): Path to export vertices. (Require a folder)
        use_animation (bool, optional): Export with animation. Defaults to True.
    """
    scene = XRFeitoriaBlenderFactory.get_active_scene()
    XRFeitoriaBlenderFactory.export_vertices(scene=scene, export_path=export_path, use_animation=use_animation)


@remote_blender()
def get_rotation_to_look_at(location: 'Vector', target: 'Vector') -> 'Vector':
    """Get the rotation of an object to look at another object.

    Args:
        location (Vector): Location of the object.
        target (Vector): Location of the target object.

    Returns:
        Vector: Rotation of the object.
    """
    import math

    rotation = XRFeitoriaBlenderFactory.get_rotation_to_look_at(location=location, target=target)
    return tuple(math.degrees(r) for r in rotation)


@remote_blender()
def init_scene_and_collection(name: str, cleanup: bool = False) -> None:
    """Init the default scene and default collection.

    Args:
        name (str): Name of the default scene and default collection.
        cleanup (bool, optional): Clean up the all the scenes, collections and objects. Defaults to False.
    """
    if cleanup:
        XRFeitoriaBlenderFactory.delete_all()
        cleanup_unused()
    # get or create collection
    if name not in bpy.data.collections.keys():
        _collection = XRFeitoriaBlenderFactory.new_collection(name)
    else:
        _collection = XRFeitoriaBlenderFactory.get_collection(name)

    # get or create scene
    if name not in bpy.data.scenes.keys():
        if cleanup:
            _scene = XRFeitoriaBlenderFactory.get_active_scene()
            _scene.name = name
        else:
            _scene = XRFeitoriaBlenderFactory.new_scene(name=name)
    else:
        _scene = XRFeitoriaBlenderFactory.get_scene(name)

    # link collection to scene
    XRFeitoriaBlenderFactory.link_collection_to_scene(_collection, _scene)
    # set scene and collection active
    XRFeitoriaBlenderFactory.set_scene_active(_scene)
    XRFeitoriaBlenderFactory.set_collection_active(_collection)


@remote_blender()
def enable_gpu(gpu_num: int = 1):
    """Enable GPU in blender.

    Args:
        gpu_num (int, optional): Number of GPUs to use. Defaults to 1.
    """
    XRFeitoriaBlenderFactory.enable_gpu(gpu_num=gpu_num)
