# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (C) 2015-2022: SCS Software

from io_scs_tools_mod.consts import Mesh as _MESH_consts
from io_scs_tools_mod.internals.shaders.base import BaseShader
from io_scs_tools_mod.internals.shaders.std_node_groups import output_shader_ng
from io_scs_tools_mod.utils import material as _material_utils


class Shadowmap(BaseShader):
    UV_MAP_NODE = "UVMap"
    BASE_TEX_NODE = "BaseTex"
    OUT_SHADER_NODE = "OutShader"
    OUTPUT_NODE = "Output"

    @staticmethod
    def get_name():
        """Get name of this shader file with full modules path."""
        return __name__

    @staticmethod
    def init(node_tree):
        """Initialize node tree with links for this shader.

        :param node_tree: node tree on which this shader should be created
        :type node_tree: bpy.types.NodeTree
        """

        start_pos_x = 0
        start_pos_y = 0

        pos_x_shift = 185

        # node creation
        uv_map_n = node_tree.nodes.new("ShaderNodeUVMap")
        uv_map_n.name = uv_map_n.label = Shadowmap.UV_MAP_NODE
        uv_map_n.location = (start_pos_x - pos_x_shift, start_pos_y + 1500)
        uv_map_n.uv_map = _MESH_consts.none_uv

        base_tex_n = node_tree.nodes.new("ShaderNodeTexImage")
        base_tex_n.name = base_tex_n.label = Shadowmap.BASE_TEX_NODE
        base_tex_n.location = (start_pos_x + pos_x_shift, start_pos_y + 1500)
        base_tex_n.width = 140

        out_shader_node = node_tree.nodes.new("ShaderNodeGroup")
        out_shader_node.name = out_shader_node.label = Shadowmap.OUT_SHADER_NODE
        out_shader_node.location = (start_pos_x + pos_x_shift * 3, 1500)
        out_shader_node.node_tree = output_shader_ng.get_node_group()
        out_shader_node.inputs["Color"].default_value = (0.0,) * 4

        output_n = node_tree.nodes.new("ShaderNodeOutputMaterial")
        output_n.name = output_n.label = Shadowmap.OUTPUT_NODE
        output_n.location = (start_pos_x + + pos_x_shift * 4, start_pos_y + 1500)

        # links creation
        node_tree.links.new(base_tex_n.inputs['Vector'], uv_map_n.outputs['UV'])

        node_tree.links.new(out_shader_node.inputs['Alpha'], base_tex_n.outputs['Color'])

        node_tree.links.new(output_n.inputs['Surface'], out_shader_node.outputs['Shader'])

    @staticmethod
    def finalize(node_tree, material):
        """Set output material for this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param material: blender material for used in this tree node as output
        :type material: bpy.types.Material
        """

        material.use_backface_culling = True
        material.blend_method = "BLEND"

    @staticmethod
    def set_base_texture(node_tree, image):
        """Set base texture to shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param image: texture image which should be assignet to base texture node
        :type image: bpy.types.Image
        """

        node_tree.nodes[Shadowmap.BASE_TEX_NODE].image = image

    @staticmethod
    def set_base_texture_settings(node_tree, settings):
        """Set base texture settings to shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param settings: binary string of TOBJ settings gotten from tobj import
        :type settings: str
        """
        _material_utils.set_texture_settings_to_node(node_tree.nodes[Shadowmap.BASE_TEX_NODE], settings)

    @staticmethod
    def set_base_uv(node_tree, uv_layer):
        """Set UV layer to base texture in shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param uv_layer: uv layer string used for base texture
        :type uv_layer: str
        """

        if uv_layer is None or uv_layer == "":
            uv_layer = _MESH_consts.none_uv

        node_tree.nodes[Shadowmap.UV_MAP_NODE].uv_map = uv_layer