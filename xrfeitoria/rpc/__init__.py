import os

from . import client, factory

__all__ = [client, factory]

# blender
REMAP_PAIRS = []
BLENDER_PORT = int(os.environ.get("BLENDER_PORT", 9997))

# use different remap pairs when inside a container
if os.environ.get("TEST_ENVIRONMENT"):
    BLENDER_PORT = int(os.environ.get("BLENDER_PORT", 8997))
    REMAP_PAIRS = [(os.environ.get("HOST_REPO_FOLDER"), os.environ.get("CONTAINER_REPO_FOLDER"))]

remote_blender_decorator = factory.remote_call(
    port=BLENDER_PORT,
    remap_pairs=REMAP_PAIRS,
    # TODO: check if it's right
    default_imports=["import bpy", "default_level_blender=bpy.context.scene.default_level_blender"],
)
remote_blender_decorator_class = factory.remote_class(remote_blender_decorator)
remote_class_blender = factory.remote_class_private(remote_blender_decorator)


###############################################


# unreal
UNREAL_PORT = int(os.environ.get("UNREAL_PORT", 9998))

# use a different remap pairs when inside a container
if os.environ.get("TEST_ENVIRONMENT"):
    UNREAL_PORT = int(os.environ.get("UNREAL_PORT", 8998))
    REMAP_PAIRS = [(os.environ.get("HOST_REPO_FOLDER"), os.environ.get("CONTAINER_REPO_FOLDER"))]

# this defines a the decorator that makes function run as remote call in unreal
remote_unreal_decorator = factory.remote_call(
    port=UNREAL_PORT,
    default_imports=["import unreal", "from unreal_factory import XRFeitoriaUnrealFactory"],
    remap_pairs=REMAP_PAIRS,
)
remote_unreal_decorator_class = factory.remote_class(remote_unreal_decorator)
remote_class_unreal = factory.remote_class_private(remote_unreal_decorator)
