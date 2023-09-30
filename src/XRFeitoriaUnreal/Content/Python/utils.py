import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import unreal
from constants import DEFAULT_ASSET_PATH, SubSystem

EditorAssetSub = SubSystem.EditorAssetSub
EditorSub = SubSystem.EditorSub
EditorLevelSub = SubSystem.EditorLevelSub

################################################################################
# define decorators


class Loader:
    """A decorator to load the persistent level and content browser before running the
    main function.

    example_usage:
        >>> @Loader
        >>> def main():
        >>>     ...
    Caution: Function decorated by this decorator cannot return anything.
    """

    def __init__(self, func):
        self.func = func
        self.args: Tuple = None
        self.kwargs: Dict = None

        self.asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
        self.tickhandle = unreal.register_slate_pre_tick_callback(self.timer)
        unreal.log_warning('registered tick handle')

    def __call__(self, *args, **kwargs):
        if args is None:
            args = []
        self.args = args

        if kwargs is None:
            kwargs = {}
        self.kwargs = kwargs

    def timer(self, deltaTime):
        if self.asset_registry.is_loading_assets():
            unreal.log_warning('loading assets...')
        else:
            unreal.log_warning('ready!')
            unreal.unregister_slate_pre_tick_callback(self.tickhandle)
            self.func(*self.args, **self.kwargs)


def timer_func(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        unreal.log(f'[Timer] Function {repr(func.__name__)} executed in {(t2-t1):.4f}s')
        return result

    return wrap_func


################################################################################
# assets


def import_asset(path: Union[str, List[str]], dst_dir_in_engine: Optional[str] = None) -> List[str]:
    """Import assets to the default asset path.

    Args:
        path (Union[str, List[str]]): a file path or a list of file paths to import, e.g. "D:/assets/SMPL_XL.fbx"
        dst_dir_in_engine (str, optional): destination directory in the engine.
            Defaults to None falls back to DEFAULT_ASSET_PATH.

    Returns:
        List[str]: a list of paths to the imported assets, e.g. ["/Game/XRFeitoriaUnreal/Assets/SMPL_XL"]
    """
    if dst_dir_in_engine is None:
        dst_dir_in_engine = DEFAULT_ASSET_PATH
    if not isinstance(path, list):
        paths = [path]
    else:
        paths = path.copy()

    asset_paths = []
    for path in paths:
        name = Path(path).stem
        dst_dir = unreal.Paths.combine([dst_dir_in_engine, Path(path).stem])
        # check if asset exists
        dst_path = unreal.Paths.combine([dst_dir, name])
        if unreal.EditorAssetLibrary.does_asset_exist(dst_path):
            asset_paths.append(dst_path)
            continue

        unreal.log(f'Importing asset: {path}')
        # assetsTools = unreal.AssetToolsHelpers.get_asset_tools()
        # assetImportData = unreal.AutomatedAssetImportData()
        # assetImportData.destination_path = dst_dir
        # assetImportData.filenames = [p]
        # assets: List[unreal.Object] = assetsTools.import_assets_automated(assetImportData)
        # asset_paths.extend([asset.get_path_name().split('.')[0] for asset in assets])

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        import_options = unreal.FbxImportUI()
        import_options.set_editor_property('import_animations', True)

        import_task = unreal.AssetImportTask()
        import_task.set_editor_property('automated', True)
        import_task.set_editor_property('destination_name', '')
        import_task.set_editor_property('destination_path', dst_dir)
        import_task.set_editor_property('filename', path)
        import_task.set_editor_property('replace_existing', True)
        import_task.set_editor_property('options', import_options)

        import_tasks = [import_task]
        asset_tools.import_asset_tasks(import_tasks)
        asset_paths.extend([path.split('.')[0] for path in import_task.get_editor_property('imported_object_paths')])

        unreal.EditorAssetLibrary.save_directory(dst_dir, False, True)  # save assets
        unreal.log(f'Imported asset: {path}')
    return asset_paths


def import_anim(path: str, skeleton_path: str) -> List[str]:
    """Import animation to the default asset path.

    Args:
        path (str): a file path to import, e.g. "D:/assets/SMPL_XL.fbx"
        skeleton_path (str): a path to the skeleton, e.g. "/Game/XRFeitoriaUnreal/Assets/SMPL_XL"

    Returns:
        str: a path to the imported animation, e.g. "/Game/XRFeitoriaUnreal/Assets/SMPL_XL"
    """
    # init task
    import_task = unreal.AssetImportTask()
    import_task.set_editor_property('filename', path)
    # set destination path to {skeleton_path}/Animation
    dst_path = unreal.Paths.combine([unreal.Paths.get_path(skeleton_path), 'Animation'])
    import_task.set_editor_property('destination_path', dst_path)
    import_task.set_editor_property('replace_existing', True)
    import_task.set_editor_property('replace_existing_settings', True)
    import_task.set_editor_property('automated', True)
    # options for importing animation
    options = unreal.FbxImportUI()
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    options.skeleton = unreal.load_asset(skeleton_path)
    import_data = unreal.FbxAnimSequenceImportData()
    import_data.set_editor_properties(
        {
            'animation_length': unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME,
            'remove_redundant_keys': True,
        }
    )
    options.anim_sequence_import_data = import_data
    # set options
    import_task.set_editor_property('options', options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([import_task])

    # save assets
    unreal.EditorAssetLibrary.save_directory(dst_path, False, True)
    # return paths
    return [path.split('.')[0] for path in import_task.get_editor_property('imported_object_paths')]


def delete_asset(asset_path: str) -> None:
    """Delete asset.

    Args:
        asset_path (str): asset path in unreal, e.g. "/Game/Resources/Mat0"
    """
    unreal.EditorAssetLibrary.delete_asset(asset_path)


def open_asset(asset_path: str) -> None:
    """Open asset.

    Args:
        asset_path (str): asset path in unreal, e.g. "/Game/Resources/Mat0"
    """
    asset = unreal.load_asset(asset_path)
    unreal.AssetToolsHelpers.get_asset_tools().open_editor_for_assets([asset])


################################################################################
# misc


class PathUtils:
    asset_registry: unreal.AssetRegistry = unreal.AssetRegistryHelpers.get_asset_registry()

    @classmethod
    def get_sub_paths(cls, path, recurse=True) -> List[str]:
        return cls.asset_registry.get_sub_paths(path, recurse=recurse)

    @staticmethod
    def list_dir(path: str, recursive: bool = True) -> List[str]:
        return sorted(unreal.EditorAssetLibrary.list_assets(path, recursive=recursive))


def get_asset_class(asset_path: str) -> str:
    asset_class_path = unreal.EditorAssetLibrary.find_asset_data(asset_path).asset_class_path
    return str(asset_class_path.asset_name)


def create_material_instance(asset_path: str) -> unreal.MaterialInstance:
    """Create material instance.

    Args:
        asset_path (str): asset path in unreal, e.g. "/Game/Resources/Mat0"
    Returns:
        my_new_asset (unreal.MaterialInstance): a new material instance
    """
    package_path, asset_name = asset_path.rsplit('/', 1)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    my_new_asset = asset_tools.create_asset(asset_name, package_path, None, factory)
    unreal.EditorAssetLibrary.save_loaded_asset(my_new_asset)
    return my_new_asset


def get_world() -> unreal.World:
    if EditorSub:
        world = EditorSub.get_editor_world()
    else:
        world = unreal.EditorLevelLibrary.get_editor_world()
    return world


def new_world(new_level_path: str) -> bool:
    if EditorLevelSub:
        success = EditorLevelSub.new_level(new_level_path)
    else:
        success = unreal.EditorLevelLibrary().new_level(new_level_path)
    return success


def save_current_level() -> None:
    """Save current level."""
    if EditorLevelSub:
        EditorLevelSub.save_current_level()
    else:
        unreal.EditorLevelLibrary.save_current_level()


def get_soft_object_path(path: str) -> unreal.SoftObjectPath:
    """Get soft object path from a path string, e.g. "/Game/Maps/PersistentLevel" ->
    "/Game/Maps/PersistentLevel.PersistentLevel.

    Args:
        path (str): a path to the persistent level, e.g. "/Game/Maps/PersistentLevel"

    Returns:
        soft_object_path (unreal.SoftObjectPath): a soft object path, e.g. "/Game/Maps/PersistentLevel.PersistentLevel
    """
    path = f'{path}.{path.split("/")[-1]}'
    return unreal.SoftObjectPath(path)


def get_levels(world: Optional[unreal.World] = None) -> List[unreal.Level]:
    if not world:
        world = get_world()
    levels = unreal.EditorLevelUtils.get_levels(world)
    return levels


def get_sublevels(persistent_level_path: str) -> List[Dict]:
    """Get sublevels of persistent level, this step would load the persistent level.

    Args:
        persistent_level_path (str): a path to the persistent level, e.g. "/Game/Maps/PersistentLevel"

    Returns:
        level_configs (List(Dict)): a list of level_configs (dict) containing keys of
            `level_name`, `is_visible`, and `streaming_class`.
    """
    asset_registry: unreal.AssetRegistry = unreal.AssetRegistryHelpers.get_asset_registry()

    # load persistent level
    world = unreal.EditorLoadingAndSavingUtils.load_map(persistent_level_path)
    # unreal.GameplayStatics.open_level(self.get_last_loaded_world(), mapPackagePath, True, gameOverrideClassPath)

    # get all sub-levels of persistent level and their config
    level_configs = []
    persistent_level_asset_data = asset_registry.get_asset_by_object_path(persistent_level_path)
    persistent_level_name = str(persistent_level_asset_data.package_name)
    level_configs.append(
        {
            'level_name': persistent_level_name,
            'is_visible': True,
            'streaming_class': 'LevelStreamingAlwaysLoaded',
        }
    )

    levels = get_levels(world)
    for level in levels:
        asset_data = asset_registry.get_asset_by_object_path(level.get_path_name())
        sub_level_name = str(asset_data.package_name)
        streaming_level = unreal.GameplayStatics.get_streaming_level(world, sub_level_name)
        if streaming_level is not None:
            level_configs.append(
                {
                    'level_name': sub_level_name,
                    'is_visible': streaming_level.is_level_visible(),
                    'streaming_class': type(streaming_level).__name__,
                }
            )

    unreal.log(level_configs)
    return level_configs


def add_levels(persistent_level_path: str, new_level_path: str) -> Tuple[List, List]:
    """Add levels from persistent level to the current world.

    Args:
        persistent_level_path (str): a path to the persistent level, e.g. "/Game/Maps/PersistentLevel"

    Returns:
        level_visible_names (list): a list of visible level names
        level_hidden_names (list): a list of hidden level names
    """

    # check if persistent level exists
    is_level_exist = unreal.EditorAssetLibrary.does_asset_exist(persistent_level_path)
    assert is_level_exist, RuntimeError('Persistent level does not exist', persistent_level_path)

    # get sublevels of persistent level
    level_configs = []
    level_infos = {}

    # get sublevels of persistent level, this step would load the persistent level
    level_configs = get_sublevels(persistent_level_path)
    # reload new levels
    world = unreal.EditorLoadingAndSavingUtils.load_map(new_level_path)
    level_infos[persistent_level_path] = level_configs

    # add persistent level and its sub levels, set visibility
    level_visible_names, level_hidden_names = [], []
    world = get_world()

    for level_config in level_configs:
        level_name: str = level_config['level_name']
        is_visible: bool = level_config['is_visible']
        streaming_class: str = level_config['streaming_class']
        streaming_class_cls = getattr(unreal, streaming_class)
        streaming_level: unreal.LevelStreaming = unreal.EditorLevelUtils.add_level_to_world(
            world, level_name, streaming_class_cls
        )

        assert streaming_class_cls is not None, f'Unknown unreal class: {streaming_class}'
        assert streaming_level is not None, f'Unable to add level to the world: {level_name}'

        unreal.EditorLevelUtils.set_level_visibility(streaming_level.get_loaded_level(), is_visible, False)

        level_basename = level_name.rpartition('/')[-1]
        if is_visible:
            level_visible_names.append(level_basename)
        else:
            level_hidden_names.append(level_basename)

    return level_visible_names, level_hidden_names
