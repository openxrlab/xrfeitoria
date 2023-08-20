from . import constants, operators, properties, ui

bl_info = {
    "name": "XRFeitoriaBpy",
    "author": "OpenXRLab",
    "version": (0, 1, 0),
    "blender": (3, 3, 0),
    "category": "Tools",
}


def register():
    operators.register()
    properties.register()
    ui.register()


def unregister():
    operators.unregister()
    properties.unregister()
    ui.unregister()
