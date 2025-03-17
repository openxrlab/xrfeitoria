"""Remote functions for unreal."""

import json
from functools import lru_cache
from typing import List, Optional, Tuple, Union

from ...data_structure.constants import Vector, color_type
from ...rpc import remote_unreal

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in src/XRFeitoriaUnreal/Content/Python
except ImportError:
    pass

# Constants
mask_colors: List[color_type] = []


@remote_unreal()
def get_mask_color_file() -> str:
    """Returns the path of the mask color file.

    Returns:
        str: The path of the mask color file.
    """
    return XRFeitoriaUnrealFactory.constants.MASK_COLOR_FILE.as_posix()


@lru_cache
def get_mask_color(stencil_value: int) -> 'Tuple[int, int, int]':
    """Retrieves the RGB color value associated with the given stencil value.

    Args:
        stencil_value (int): The stencil value for which to retrieve the color.

    Returns:
        Tuple[int, int, int]: The RGB color value associated with the stencil value.
    """
    global mask_colors
    if len(mask_colors) == 0:
        with open(get_mask_color_file(), 'r') as f:
            mask_colors = json.load(f)
    return mask_colors[stencil_value]['rgb']


@lru_cache
@remote_unreal()
def get_skeleton_names(actor_asset_path: str) -> 'List[str]':
    """Retrieves the names of the bones in the skeleton of a SkeletalMeshActor (also can
    be child class of it).

    Args:
        actor_asset_path (str): The asset path of the SkeletalMeshActor.

    Returns:
        List[str]: The names of the bones in the skeleton.
    """
    return XRFeitoriaUnrealFactory.utils_actor.get_skeleton_names(actor_asset_path)


@remote_unreal()
def check_asset_in_engine(path: str, raise_error: bool = False) -> bool:
    """Check if an asset exists in the engine.

    Args:
        path (str): asset path in unreal, e.g. "/Game/Resources/Mat0"
        raise_error (bool): raise error if the asset does not exist

    Returns:
        bool: True if the asset exists, False otherwise

    Raises:
        ValueError: if the asset does not exist and raise_error is True
    """
    is_exist = unreal.EditorAssetLibrary.does_asset_exist(path)
    if not is_exist and raise_error:
        raise ValueError(f'Asset `{path}` does not exist')
    return is_exist


@remote_unreal()
def open_level(asset_path: str) -> None:
    """Open a level.

    Args:
        asset_path (str): asset path in unreal, e.g. "/Game/Maps/Map0"
    """
    check_asset_in_engine(asset_path, raise_error=True)
    XRFeitoriaUnrealFactory.SubSystem.EditorLevelSub.load_level(asset_path)


@remote_unreal()
def save_current_level(asset_path: 'Optional[str]' = None) -> None:
    """Save the current opened level."""
    if asset_path is not None:
        # BUG: save_map to a new path does not work
        world = XRFeitoriaUnrealFactory.SubSystem.EditorLevelSub.get_world()
        unreal.EditorLoadingAndSavingUtils.save_map(world, asset_path)
    else:
        XRFeitoriaUnrealFactory.SubSystem.EditorLevelSub.save_current_level()


@remote_unreal()
def import_asset(
    path: 'Union[str, List[str]]',
    dst_dir_in_engine: 'Optional[str]' = None,
    replace: bool = True,
    with_parent_dir: bool = True,
) -> 'Union[str, List[str]]':
    """Import assets to the default asset path.

    Args:
        path (Union[str, List[str]]): a file path or a list of file paths to import, e.g. "D:/assets/SMPL_XL.fbx"
        dst_dir_in_engine (Optional[str], optional): destination directory in the engine.
            Defaults to None falls back to '/Game/XRFeitoriaUnreal/Assets'
        replace (bool, optional): whether to replace the existing asset. Defaults to True.
        with_parent_dir (bool, optional): whether to create a parent directory that contains the imported asset.
            If False, the imported asset will be in `dst_dir_in_engine` directly. Defaults to True.

    Returns:
        Union[str, List[str]]: a path or a list of paths to the imported assets, e.g. "/Game/XRFeitoriaUnreal/Assets/SMPL_XL"
    """
    paths = XRFeitoriaUnrealFactory.utils.import_asset(
        path, dst_dir_in_engine, replace=replace, with_parent_dir=with_parent_dir
    )
    if len(paths) == 1:
        return paths[0]
    return paths


@remote_unreal()
def import_anim(path: str, skeleton_path: str, dest_path: 'Optional[str]' = None, replace: bool = True) -> 'List[str]':
    """Import animation to the default asset path.

    Args:
        path (str): The file path to import, e.g. "D:/assets/SMPL_XL-Animation.fbx".
        skeleton_path (str): The path to the skeleton, e.g. "/Game/XRFeitoriaUnreal/Assets/SMPL_XL_Skeleton".
        dest_path (str, optional): The destination directory in the engine. Defaults to None, falls back to {skeleton_path.parent}/Animation.
        replace (bool, optional): whether to replace the existing asset. Defaults to True.

    Returns:
        List[str]: A list of paths to the imported animations, e.g. ["/Game/XRFeitoriaUnreal/Assets/SMPL_XL-Animation"].
    """
    return XRFeitoriaUnrealFactory.utils.import_anim(path, skeleton_path, dest_path, replace=replace)


@remote_unreal()
def duplicate_asset(src_path: str, dst_path: str, replace: bool = False) -> None:
    """Duplicate asset in unreal.

    Args:
        src_path (str): source asset path in unreal, e.g. "/Game/Resources/Mat0"
        dst_path (str): destination asset path in unreal, e.g. "/Game/Resources/Mat1"
    """
    check_asset_in_engine(src_path, raise_error=True)
    if check_asset_in_engine(dst_path) and replace:
        delete_asset(dst_path)
    unreal.EditorAssetLibrary.duplicate_asset(
        source_asset_path=src_path,
        destination_asset_path=dst_path,
    )
    check_asset_in_engine(dst_path, raise_error=True)
    unreal.EditorAssetLibrary.save_asset(dst_path)


@remote_unreal()
def new_seq_data(asset_path: str, sequence_path: str, map_path: str) -> None:
    """Create a new data asset of sequence data.

    Args:
        asset_path (str): path of the data asset.
        sequence_path (str): path of the sequence asset.
        map_path (str): path of the map asset.

    Returns:
        unreal.DataAsset: the created data asset.

    Notes:
        SequenceData Properties:
            - "SequencePath": str
            - "MapPath": str
    """
    XRFeitoriaUnrealFactory.sequence_data_asset(
        asset_path=asset_path,
        sequence_path=sequence_path,
        map_path=map_path,
    )


@remote_unreal()
def delete_asset(asset_path: str) -> None:
    """Delete asset.

    Args:
        asset_path (str): asset path in unreal, e.g. "/Game/Resources/Mat0"
    """
    XRFeitoriaUnrealFactory.utils.delete_asset(asset_path)


@remote_unreal()
def open_asset(asset_path: str) -> None:
    """Open asset.

    Args:
        asset_path (str): asset path in unreal, e.g. "/Game/Resources/Mat0"
    """
    XRFeitoriaUnrealFactory.utils.open_asset(asset_path)


@remote_unreal()
def get_rotation_to_look_at(location: 'Vector', target: 'Vector') -> 'Vector':
    """Get the rotation of an object to look at another object.

    Args:
        location (Vector): Location of the object.
        target (Vector): Location of the target object.

    Returns:
        Vector: Rotation of the object.
    """
    target = unreal.Vector(x=target[0], y=target[1], z=target[2])
    forward = target - location
    z = unreal.Vector(0, 0, -1)
    right = forward.cross(z)
    up = forward.cross(right)
    rotation = unreal.MathLibrary.make_rotation_from_axes(forward, right, up)
    return rotation.to_tuple()
