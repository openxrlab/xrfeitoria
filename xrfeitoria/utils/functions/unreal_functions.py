"""Remote functions for unreal."""

from typing import List, Optional, Tuple, Union

from ...rpc import remote_unreal

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in src/XRFeitoriaUnreal/Content/Python
except ImportError:
    pass


@remote_unreal()
def get_mask_color(stencil_value: int) -> 'Tuple[int, int, int]':
    """Get mask color from stencil value.

    Args:
        stencil_value (int): stencil value

    Returns:
        Tuple[int, int, int]: mask color. (r, g, b) in [0, 255]
    """
    # TODO: move this to local, not remote
    return XRFeitoriaUnrealFactory.utils_actor.get_mask_color(stencil_value)


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
def import_asset(path: 'Union[str, List[str]]', dst_dir_in_engine: 'Optional[str]' = None) -> 'Union[str, List[str]]':
    """Import assets to the default asset path.

    Args:
        path (Union[str, List[str]]): a file path or a list of file paths to import, e.g. "D:/assets/SMPL_XL.fbx"
        dst_dir_in_engine (Optional[str], optional): destination directory in the engine.
            Defaults to None falls back to '/Game/XRFeitoriaUnreal/Assets'

    Returns:
        Union[str, List[str]]: a path or a list of paths to the imported assets, e.g. "/Game/XRFeitoriaUnreal/Assets/SMPL_XL"
    """
    paths = XRFeitoriaUnrealFactory.utils.import_asset(path, dst_dir_in_engine)
    if len(paths) == 1:
        return paths[0]
    return paths


@remote_unreal()
def import_anim(path: str, skeleton_path: str) -> 'List[str]':
    """Import animation to the default asset path.

    Args:
        path (str): a file path to import, e.g. "D:/assets/SMPL_XL-Animation.fbx"
        skeleton_path (str): a path to the skeleton, e.g. "/Game/XRFeitoriaUnreal/Assets/SMPL_XL_Skeleton"

    Returns:
        str: a path to the imported animation, e.g. "/Game/XRFeitoriaUnreal/Assets/SMPL_XL-Animation"
    """
    return XRFeitoriaUnrealFactory.utils.import_anim(path, skeleton_path)


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
