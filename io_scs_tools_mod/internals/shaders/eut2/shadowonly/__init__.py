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

# Copyright (C) 2015-2019: SCS Software

from io_scs_tools_mod.internals.shaders.base import BaseShader


class Shadowonly(BaseShader):
    COL_NODE = "Color"
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
        col_n = node_tree.nodes.new("ShaderNodeRGB")
        col_n.name = col_n.label = Shadowonly.COL_NODE
        col_n.location = (start_pos_x, start_pos_y)
        col_n.outputs['Color'].default_value = (0.01, 0, 0.01, 1.0)

        output_n = node_tree.nodes.new("ShaderNodeOutputMaterial")
        output_n.name = output_n.label = Shadowonly.OUTPUT_NODE
        output_n.location = (start_pos_x + pos_x_shift, start_pos_y)

        # links creation
        node_tree.links.new(output_n.inputs['Surface'], col_n.outputs['Color'])

    @staticmethod
    def finalize(node_tree, material):
        """Finalize node tree and material settings. Should be called as last.

        :param node_tree: node tree on which this shader should be finalized
        :type node_tree: bpy.types.NodeTree
        :param material: material used for this shader
        :type material: bpy.types.Material
        """

        material.use_backface_culling = True
        material.blend_method = "OPAQUE"

    @staticmethod
    def set_shadow_bias(node_tree, value):
        """Set shadow bias attirbute for this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param value: blender material for used in this tree node as output
        :type value: float
        """

        pass  # NOTE: shadow bias won't be visualized as game uses it's own implementation
