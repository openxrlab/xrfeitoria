import bpy


def register():
    bpy.types.Scene.default_level_blender = bpy.props.StringProperty(
        name="Default Level Blender",
        default="XRFeitoria",
    )


def unregister():
    del bpy.types.Scene.default_level_blender
