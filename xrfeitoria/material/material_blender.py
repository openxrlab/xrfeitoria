import math
from typing import Dict, List, Optional, Tuple, Union

from ..data_structure.constants import BSDFNodeLinkEnumBlender, Vector
from ..object.object_utils import ObjectUtilsBlender
from ..rpc import remote_blender
from ..utils import Validator
from .material_base import MaterialBase

try:
    import bpy  # isort:skip
    from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory  # defined in src/XRFeitoriaBpy/core/factory.py
except ModuleNotFoundError:
    pass

try:
    from ..data_structure.models import TransformKeys  # isort:skip
except ModuleNotFoundError:
    pass


@remote_blender(dec_class=True, suffix='_in_engine')
class MaterialBlender(MaterialBase):
    """Material class for Blender."""

    _object_utils = ObjectUtilsBlender

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    ######   Getter   ######
    @staticmethod
    def _new_material_in_engine(mat_name: str) -> None:
        """Add a new material.

        Args:
            mat_name (str): Name of the material in Blender.
        """
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

    @staticmethod
    def _add_diffuse_texture_in_engine(
        mat_name: str,
        texture_file: str,
        texture_name: str,
    ) -> None:
        """Add a diffuse texture to the material.

        Args:
            mat_name (str): Name of the material in Blender.
            texture_file (PathLike): File path of the texture.
            texture_name (Optional[str]): Name of the texture. Defaults to None.
        """
        mat = XRFeitoriaBlenderFactory.get_material(mat_name=mat_name)
        tex_node = XRFeitoriaBlenderFactory.new_mat_node(mat=mat, type='ShaderNodeTexImage', name=texture_name)
        tex_node.image = XRFeitoriaBlenderFactory.import_texture(texture_file=texture_file)

        # HACK: move nodes to the left, for better visibility
        tex_node.location.x -= 400
        tex_node.location.y += 200

        bsdf_node = mat.node_tree.nodes['Principled BSDF']
        mat.node_tree.links.new(tex_node.outputs['Color'], bsdf_node.inputs[BSDFNodeLinkEnumBlender.diffuse])

    @staticmethod
    def _add_normal_texture_in_engine(
        mat_name: str,
        texture_file: str,
        texture_name: str,
    ) -> None:
        """Add a normal texture to the material.

        Args:
            mat_name (str): Name of the material in Blender.
            texture_file (PathLike): File path of the texture.
            texture_name (Optional[str]): Name of the texture. Defaults to None.
        """
        mat = XRFeitoriaBlenderFactory.get_material(mat_name=mat_name)
        tex_node = XRFeitoriaBlenderFactory.new_mat_node(mat=mat, type='ShaderNodeTexImage', name=texture_name)
        tex_node.image = XRFeitoriaBlenderFactory.import_texture(texture_file=texture_file)

        normal_node = XRFeitoriaBlenderFactory.new_mat_node(mat=mat, type='ShaderNodeNormalMap')
        gamma_node = XRFeitoriaBlenderFactory.new_mat_node(mat=mat, type='ShaderNodeGamma')
        gamma_node.inputs['Gamma'].default_value = 0.454  # 2.2 gamma

        # HACK: move nodes to the left, for better visibility
        tex_node.location.x -= 800
        gamma_node.location.x -= 400
        normal_node.location.x -= 200
        tex_node.location.y -= 600
        gamma_node.location.y -= 600
        normal_node.location.y -= 600

        bsdf_node = mat.node_tree.nodes['Principled BSDF']
        mat.node_tree.links.new(tex_node.outputs['Color'], gamma_node.inputs['Color'])
        mat.node_tree.links.new(gamma_node.outputs['Color'], normal_node.inputs['Color'])
        mat.node_tree.links.new(normal_node.outputs['Normal'], bsdf_node.inputs[BSDFNodeLinkEnumBlender.normal])

    @staticmethod
    def _add_roughness_texture_in_engine(
        mat_name: str,
        texture_file: str,
        texture_name: str,
    ) -> None:
        """Add a roughness texture to the material.

        Args:
            mat_name (str): Name of the material in Blender.
            texture_file (PathLike): File path of the texture.
            texture_name (Optional[str]): Name of the texture. Defaults to None.
        """
        mat = XRFeitoriaBlenderFactory.get_material(mat_name=mat_name)
        tex_node = XRFeitoriaBlenderFactory.new_mat_node(mat=mat, type='ShaderNodeTexImage', name=texture_name)
        tex_node.image = XRFeitoriaBlenderFactory.import_texture(texture_file=texture_file)

        math_node = XRFeitoriaBlenderFactory.new_mat_node(mat=mat, type='ShaderNodeMath')
        math_node.operation = 'SUBTRACT'
        math_node.inputs[0].default_value = 1.0

        map_node = XRFeitoriaBlenderFactory.new_mat_node(mat=mat, type='ShaderNodeMapRange')
        map_node.inputs[3].default_value = 0.5

        # HACK: move nodes to the left, for better visibility
        tex_node.location.x -= 800
        math_node.location.x -= 400
        map_node.location.x -= 200
        tex_node.location.y -= 200
        math_node.location.y -= 200
        map_node.location.y -= 200

        bsdf_node = mat.node_tree.nodes['Principled BSDF']
        mat.node_tree.links.new(tex_node.outputs['Color'], math_node.inputs[1])
        mat.node_tree.links.new(math_node.outputs['Value'], map_node.inputs[0])
        mat.node_tree.links.new(map_node.outputs['Result'], bsdf_node.inputs[BSDFNodeLinkEnumBlender.roughness])
