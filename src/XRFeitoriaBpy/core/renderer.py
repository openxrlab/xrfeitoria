from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import bpy

from .. import logger
from ..constants import ImageFileFormatEnum, RenderEngineEnum, RenderLayerEnum


class RenderPassUtils:
    @staticmethod
    def reset_tree(scene) -> None:
        tree = scene.node_tree
        tree.nodes.clear()  # clear default nodes

    @staticmethod
    def find_or_add_render_layer_node(context) -> Optional[bpy.types.CompositorNodeRLayers]:
        scene = context.scene
        tree = scene.node_tree
        for node in tree.nodes:
            if node.type == 'R_LAYERS':
                return node
        render_layers = tree.nodes.new(type='CompositorNodeRLayers')  # Define Render Layers
        return render_layers

    @classmethod
    def find_or_add_file_output_node(cls, context, output_path: str) -> bpy.types.CompositorNodeOutputFile:
        scene = context.scene
        tree = scene.node_tree
        # check if file output node already exists
        for node in tree.nodes:
            if node.type == 'OUTPUT_FILE' and Path(node.base_path).resolve() == Path(output_path).resolve():
                return node
        # Define File Output Node
        file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output.base_path = output_path
        file_output.inputs.clear()
        # set location for better view
        render_layer_node = cls.find_or_add_render_layer_node(context)
        file_output.location = (render_layer_node.location.x + 300, 0)
        return file_output

    @staticmethod
    def setup_buffer(context: bpy.types.Context, render_layer: RenderLayerEnum) -> None:
        scene = context.scene
        view_layer = context.view_layer

        scene.render.use_persistent_data = True  # Render Optimizations

        # setup buffers
        if render_layer == RenderLayerEnum.depth:
            view_layer.use_pass_z = True
        elif render_layer == RenderLayerEnum.denoising_depth:
            if not scene.render.engine == RenderEngineEnum.cycles:
                raise TypeError('Denoising depth is only supported in Cycles')
            view_layer.use_pass_z = True
            view_layer.cycles.denoising_store_passes = True  # De-noising Passes like Albedo, Normal, Depth, etc
        elif render_layer == RenderLayerEnum.flow:
            if not scene.render.engine == RenderEngineEnum.cycles:
                raise TypeError('Flow is only supported in Cycles')
            view_layer.use_pass_vector = True
        elif render_layer == RenderLayerEnum.mask:
            if not scene.render.engine == RenderEngineEnum.cycles:
                raise TypeError('Mask is only supported in Cycles')
            view_layer.use_pass_object_index = True
        elif render_layer == RenderLayerEnum.normal:
            view_layer.use_pass_normal = True
        elif render_layer == RenderLayerEnum.diffuse:
            view_layer.use_pass_diffuse_color = True

    @staticmethod
    def set_color_depth(context: bpy.types.Context, color_depth: int) -> None:
        """Set the color depth of the scene."""
        scene = context.scene
        scene.render.image_settings.color_depth = str(color_depth)

    @staticmethod
    def set_file_format(context: bpy.types.Context, file_format: ImageFileFormatEnum) -> None:
        """Set the format of the scene."""
        scene = context.scene
        scene.render.image_settings.file_format = file_format

    ##########################
    # ------- Nodes -------- #
    ##########################
    @staticmethod
    def set_slot_to_jpg(node_slot: bpy.types.NodeOutputFileSlotFile):
        node_slot.use_node_format = False
        node_slot.format.file_format = ImageFileFormatEnum.jpeg

    @staticmethod
    def set_slot_to_png(node_slot: bpy.types.NodeOutputFileSlotFile):
        node_slot.use_node_format = False
        node_slot.format.file_format = ImageFileFormatEnum.png

    @staticmethod
    def set_slot_to_exr(node_slot: bpy.types.NodeOutputFileSlotFile):
        """Set depth to save as float (EXR)"""
        node_slot.use_node_format = False
        node_slot.format.file_format = ImageFileFormatEnum.exr
        node_slot.format.color_depth = '32'

    @staticmethod
    def set_slot_to_gray(node_slot: bpy.types.NodeOutputFileSlotFile):
        node_slot.use_node_format = False
        node_slot.format.color_mode = 'BW'

    @classmethod
    def add_node_cut_off(context, node) -> bpy.types.CompositorNodeMath:
        scene = context.scene
        tree = scene.node_tree
        links = tree.links

        # cut off depth at 1000mm, and set to 0 for invalid depth
        math_node1 = tree.nodes.new('CompositorNodeMath')
        math_node1.operation = 'LESS_THAN'
        math_node1.inputs[1].default_value = 1.0
        links.new(node.outputs[0], math_node1.inputs[0])

        math_node2 = tree.nodes.new('CompositorNodeMath')
        math_node2.operation = 'MULTIPLY'
        links.new(node.outputs[0], math_node2.inputs[0])
        links.new(math_node1.outputs[0], math_node2.inputs[1])
        return math_node2

    @classmethod
    def add_render_pass(
        cls,
        context,
        output_path: str,
        image_format: str,
        render_layer: str,
    ) -> None:
        """Add a render pass to the scene."""
        scene = context.scene
        tree = scene.node_tree
        links = tree.links

        # init
        image_format = ImageFileFormatEnum.get(image_format)
        render_layer = RenderLayerEnum.get(render_layer)
        render_layer_node = cls.find_or_add_render_layer_node(context)

        # check if the pass is available
        cls.setup_buffer(context, render_layer)
        assert render_layer_node.outputs.get(render_layer) is not None, f'{render_layer} is not available'

        file_output_node = cls.find_or_add_file_output_node(context=context, output_path=output_path)
        slot_name = f'{render_layer.name}/'
        if file_output_node.file_slots.get(slot_name) is not None:
            logger.warning(f'Render pass {render_layer.name} already exists, skipping')
            return

        file_output_node.file_slots.new(name=slot_name)
        file_slot = file_output_node.file_slots[slot_name]

        # default to png
        # if image_format == ImageFileFormatEnum.png:
        #     self.set_slot_to_png(file_slot)
        if image_format == ImageFileFormatEnum.exr:
            cls.set_slot_to_exr(file_slot)
        elif image_format == ImageFileFormatEnum.jpeg:
            cls.set_slot_to_jpg(file_slot)

        # link node of render layer to file output (mask and depth need to be processed)
        node_out = render_layer_node.outputs[render_layer]
        if render_layer == RenderLayerEnum.mask:
            if not image_format == ImageFileFormatEnum.exr:
                cls.set_slot_to_gray(file_slot)
            # link mask
            math_node = tree.nodes.new('CompositorNodeMath')
            math_node.operation = 'DIVIDE'
            math_node.inputs[1].default_value = 255.0
            links.new(node_out, math_node.inputs[0])
            node_out = math_node.outputs[0]
        if (
            render_layer == RenderLayerEnum.depth or render_layer == RenderLayerEnum.denoising_depth
        ) and image_format == ImageFileFormatEnum.png:
            cls.set_slot_to_gray(file_slot)
            file_slot.format.color_depth = '16'
            file_slot.format.compression = 100
            # scale depth by 1000 (to get mm), divide by 65535 to scale to 16bit
            math_node = tree.nodes.new('CompositorNodeMath')
            math_node.operation = 'MULTIPLY'
            math_node.inputs[1].default_value = 1000.0 / 65535.0
            links.new(node_out, math_node.inputs[0])
            node_out = math_node.outputs[0]
        links.new(node_out, file_output_node.inputs[slot_name])
