from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from .constants import PathLike, PlatformEnum, RenderPass, SequenceTransformKey, default_level_blender
from .constants import platform as __platform__
from .factory import XRFeitoriaUnreal, XRFetoriaBlender


def _get_version() -> str:
    from .version import version as default

    try:
        from importlib.metadata import version
    except ImportError:
        return default
    else:
        try:
            return version(__package__)
        except Exception:
            # Run without install
            return default


@contextmanager
def init_blender(
    exec_path: Optional[PathLike] = None,
    project_path: Optional[PathLike] = None,
    background: bool = True,
    replace_plugin: bool = False,
    new_process: bool = True,
    cleanup: bool = True,
) -> Generator[XRFetoriaBlender, None, None]:
    global __platform__
    __platform__ = PlatformEnum.blender

    xf_runner = XRFetoriaBlender(
        engine_exec=exec_path,
        project_path=project_path,
        replace_plugin=replace_plugin,
        background=background,
        new_process=new_process,
    )
    with xf_runner._rpc_runner:
        if cleanup:
            xf_runner.ObjectUtils.delete_all()
            xf_runner.utils.cleanup()
        xf_runner.utils.init_scene_and_collection(default_level_blender, cleanup)
        yield xf_runner


@contextmanager
def init_unreal(
    exec_path: Optional[PathLike] = None,
    project_path: Optional[PathLike] = None,
    background: bool = True,
    replace_plugin: bool = False,
    new_process: bool = True,
) -> Generator[XRFeitoriaUnreal, None, None]:
    assert exec_path and Path(exec_path).exists(), f"Unreal executable not found: {exec_path}"
    assert project_path and Path(project_path).exists(), f"Unreal project not found: {project_path}"

    global __platform__
    __platform__ = PlatformEnum.unreal

    xf_runner = XRFeitoriaUnreal(
        engine_exec=exec_path,
        project_path=project_path,
        replace_plugin=replace_plugin,
        background=background,
        new_process=new_process,
    )
    with xf_runner._rpc_runner:
        # xf_runner.Renderer.clear()
        yield xf_runner


__version__ = _get_version()
__all__ = [
    __platform__,
    RenderPass,
    SequenceTransformKey,
    init_unreal,
    init_blender,
]
