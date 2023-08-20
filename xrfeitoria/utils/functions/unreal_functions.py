from typing import Optional

from ...constants import PathLike
from ...rpc import remote_unreal_decorator

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in XRFeitoriaUnreal/Content/Python
except ImportError:
    pass


@remote_unreal_decorator
def _check_asset_in_engine(path: str) -> bool:
    assert unreal.EditorAssetLibrary.does_asset_exist(path), f"Asset `{path}` does not exist"
