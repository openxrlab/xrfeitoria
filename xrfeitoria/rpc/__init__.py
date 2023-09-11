import os
from functools import partial

from . import factory

__all__ = ['remote_blender', 'remote_unreal']

# blender
REMAP_PAIRS = []
BLENDER_PORT = int(os.environ.get('BLENDER_PORT', 9997))
blender_default_imports = [
    'import bpy',
    'default_level_blender = bpy.context.scene.default_level_blender',
    'from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory',
]

# use different remap pairs when inside a container
if os.environ.get('TEST_ENVIRONMENT'):
    BLENDER_PORT = int(os.environ.get('BLENDER_PORT', 8997))
    REMAP_PAIRS = [
        (
            os.environ.get('HOST_REPO_FOLDER'),
            os.environ.get('CONTAINER_REPO_FOLDER'),
        )
    ]

remote_blender = partial(
    factory.remote_call,
    port=BLENDER_PORT,
    default_imports=blender_default_imports,
    remap_pairs=REMAP_PAIRS,
)
###############################################


# unreal
UNREAL_PORT = int(os.environ.get('UNREAL_PORT', 9998))
unreal_default_imports = [
    'import unreal',
    'from unreal_factory import XRFeitoriaUnrealFactory',
]

# use a different remap pairs when inside a container
if os.environ.get('TEST_ENVIRONMENT'):
    UNREAL_PORT = int(os.environ.get('UNREAL_PORT', 8998))
    REMAP_PAIRS = [
        (
            os.environ.get('HOST_REPO_FOLDER'),
            os.environ.get('CONTAINER_REPO_FOLDER'),
        )
    ]

remote_unreal = partial(
    factory.remote_call,
    port=UNREAL_PORT,
    default_imports=unreal_default_imports,
    remap_pairs=REMAP_PAIRS,
)
