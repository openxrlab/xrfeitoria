from .utils_logger import logger  # isort:skip
from . import constants, operators, properties, ui  # isort:skip

bl_info = {
    'name': 'XRFeitoriaBpy',
    'author': 'OpenXRLab',
    'version': (0, 5, 1),
    'blender': (3, 3, 0),
    'category': 'Tools',
}


def register():
    operators.register()
    properties.register()
    ui.register()


def unregister():
    operators.unregister()
    properties.unregister()
    ui.unregister()
