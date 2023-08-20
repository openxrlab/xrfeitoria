import logging
import threading

import bpy

from .constants import __range_info__
from .core.renderer import RenderPassUtils
from .rpc import blender_server

logger = logging.getLogger(__name__)


class StartRPCServerOperator(bpy.types.Operator):
    """Bootstraps unreal and blender with rpc server threads, so that they are ready for remote calls."""

    bl_idname = "wm.start_rpc_servers"
    bl_label = "Start RPC Servers"

    block: bpy.props.BoolProperty(name="block", default=False)
    port: bpy.props.IntProperty(name="port", default=9997)

    def execute(self, context):
        # start the blender rpc server if its not already running
        if "BlenderRPCServer" not in [thread.name for thread in threading.enumerate()]:
            rpc_server = blender_server.RPCServer(port=self.port)
            rpc_server.start(threaded=bool(not self.block))

        return {"FINISHED"}


class BpyRenderWithLogOperator(bpy.types.Operator):
    """Render with log"""

    bl_idname = "wm.render_with_log"
    bl_label = "Render with log"

    write_still: bpy.props.BoolProperty(name="Write still", default=True)
    animation: bpy.props.BoolProperty(name="Animation", default=False)
    render_step: bpy.props.IntProperty(name="Total step to render", default=-1)

    def execute(self, context):
        if hasattr(self, "render_step") and self.render_step > 0:
            frame_start = 1
            frame_end = self.render_step
        else:
            frame_start = bpy.context.scene.frame_start
            frame_end = bpy.context.scene.frame_end

        logger.info(__range_info__.format(frame_start, frame_end))
        bpy.ops.render.render(write_still=self.write_still, animation=self.animation)
        return {"FINISHED"}


class RenderPassesOperator(bpy.types.Operator):
    """Adds render passes to the scene."""

    bl_idname = "wm.add_render_pass"
    bl_label = "Add Render Passes"

    output_path: bpy.props.StringProperty(name="Output path", subtype="FILE_PATH", default="//")
    render_layer: bpy.props.EnumProperty(
        name="Render Passes",
        items=[
            ("img", "Image", "Image"),
            ("Image", "Image", "Image"),
            ("mask", "IndexOB", "IndexOB"),
            ("IndexOB", "IndexOB", "IndexOB"),
            ("depth", "Depth", "Depth"),
            ("Depth", "Depth", "Depth"),
            ("denoising_depth", "Denoising Depth", "Denoising Depth"),
            ("Denoising Depth", "Denoising Depth", "Denoising Depth"),
            ("flow", "Vector", "Vector"),
            ("Vector", "Vector", "Vector"),
            ("normal", "Normal", "Normal"),
            ("Normal", "Normal", "Normal"),
            ("diffuse", "DiffCol", "DiffCol"),
            ("DiffCol", "DiffCol", "DiffCol"),
        ],
    )
    format: bpy.props.EnumProperty(
        name="File Format",
        items=[
            ("png", "PNG", "PNG"),
            ("PNG", "PNG", "PNG"),
            ("bmp", "BMP", "BMP"),
            ("BMP", "BMP", "BMP"),
            ("jpg", "JPEG", "JPEG"),
            ("JPEG", "JPEG", "JPEG"),
            ("jpeg", "JPEG", "JPEG"),
            ("JPEG", "JPEG", "JPEG"),
            ("exr", "OPEN_EXR", "OPEN_EXR"),
            ("OPEN_EXR", "OPEN_EXR", "OPEN_EXR"),
        ],
    )

    def execute(self, context):
        context.scene.use_nodes = True
        RenderPassUtils.add_render_pass(
            context,
            output_path=self.output_path,
            render_layer=self.render_layer,
            image_format=self.format,
        )
        return {"FINISHED"}


operator_classes = [
    BpyRenderWithLogOperator,
    StartRPCServerOperator,
    RenderPassesOperator,
]


def register():
    for operator_class in operator_classes:
        bpy.utils.register_class(operator_class)


def unregister():
    for operator_class in reversed(operator_classes):
        bpy.utils.unregister_class(operator_class)
