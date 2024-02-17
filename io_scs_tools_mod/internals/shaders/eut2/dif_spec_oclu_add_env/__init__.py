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

from io_scs_tools_mod.internals.shaders.eut2.dif_spec_oclu import DifSpecOclu
from io_scs_tools_mod.internals.shaders.eut2.std_passes.add_env import StdAddEnv


class DifSpecOcluAddEnv(DifSpecOclu, StdAddEnv):
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

        # init parent
        DifSpecOclu.init(node_tree)

        StdAddEnv.add(node_tree,
                      DifSpecOclu.GEOM_NODE,
                      node_tree.nodes[DifSpecOclu.SPEC_COL_NODE].outputs['Color'],
                      node_tree.nodes[DifSpecOclu.BASE_TEX_NODE].outputs['Alpha'],
                      node_tree.nodes[DifSpecOclu.LIGHTING_EVAL_NODE].outputs['Normal'],
                      node_tree.nodes[DifSpecOclu.COMPOSE_LIGHTING_NODE].inputs['Env Color'])

        oclu_sep_n = node_tree.nodes[DifSpecOclu.OCLU_SEPARATE_RGB_NODE]
        add_env_gn = node_tree.nodes[StdAddEnv.ADD_ENV_GROUP_NODE]

        # links creation
        node_tree.links.new(add_env_gn.inputs['Strength Multiplier'], oclu_sep_n.outputs['R'])
