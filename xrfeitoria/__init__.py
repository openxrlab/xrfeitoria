__all__ = ['__version__', 'init_blender', 'init_unreal']


class CacheThread:
    def __init__(self):
        self.global_vars = {}

    @property
    def cache(self):
        return self.global_vars


def _get_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = 'unknown'

    return __version__


_tls = CacheThread()
__version__ = _get_version()  # e.g. '0.5.0'
from .factory import init_blender, init_unreal
