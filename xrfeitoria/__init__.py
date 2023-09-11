import threading

_tls = threading.local()
_tls.cache = {'platform': None, 'engine_process': None, 'unreal_project_path': None}

__all__ = ['__version__', 'init_blender', 'init_unreal']


def _get_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = 'unknown'

    return __version__


__version__ = _get_version()
from .factory import init_blender, init_unreal
