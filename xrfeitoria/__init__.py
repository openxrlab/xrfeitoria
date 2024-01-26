import threading

__all__ = ['__version__', 'init_blender', 'init_unreal']


class CacheThread:
    def __init__(self):
        self.global_vars = {}

    @property
    def cache(self):
        key = threading.current_thread().ident
        if key not in self.global_vars:
            self.global_vars[key] = {'platform': None, 'engine_process': None, 'unreal_project_path': None}
        return self.global_vars[key]


def _get_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = 'unknown'

    return __version__


_tls = CacheThread()
__version__ = _get_version()
from .factory import init_blender, init_unreal
