import os
import time
from contextlib import contextmanager
from functools import partial

from loguru import logger

import xrfeitoria as xf
from xrfeitoria.rpc import remote_blender_decorator, remote_unreal_decorator
from xrfeitoria.utils import Logger


@remote_blender_decorator
def test_blender():
    import bpy  # fmt: skip
    print("test")


@remote_unreal_decorator
def test_unreal():
    import unreal  # fmt: skip
    unreal.log("test")


def set_logger(debug: bool = False):
    Logger.setup_logging(level="DEBUG" if debug else "INFO")
    if debug:
        os.environ["RPC_DEBUG"] = "1"


@contextmanager
def __timer__(step_name: str):
    t1 = time.time()
    yield
    t2 = time.time()
    logger.info(f"✅ {step_name} executed in {(t2-t1):.4f}s")


_init_blender = partial(
    xf.init_blender,
    exec_path="C:/Program Files/Blender Foundation/Blender 3.3/blender.exe",
    new_process=False,
)
_init_unreal = partial(
    xf.init_unreal,
    exec_path="E:/Program Files/Epic Games/UE_5.2/Engine/Binaries/Win64/UnrealEditor-Cmd.exe",
    project_path="C:/Documents/Unreal_Projects/MyProject_52/MyProject_52.uproject",
    new_process=False,
)
