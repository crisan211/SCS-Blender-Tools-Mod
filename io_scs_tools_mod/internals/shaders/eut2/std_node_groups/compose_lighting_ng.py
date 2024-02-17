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

# Copyright (C) 2016-2022: SCS Software

import bpy
from io_scs_tools_mod.consts import Material as _MAT_consts
from io_scs_tools_mod.consts import SCSLigthing as _LIGHTING_consts
from io_scs_tools_mod.internals.shaders.std_node_groups import output_shader_ng
from io_scs_tools_mod.utils import convert as _convert_utils

COMPOSE_LIGHTING_G = _MAT_consts.node_group_prefix + "ComposeLighting"

_ADD_AMBIENT_COL_NODE = "AdditionalAmbientColor"  # sun profile ambient color
_MULT_AA_NODE = "AA=AddAmbient*AdditionalAmbientColor"
_SUM_DL_FINAL_NODE = "DLF=DL+AA"
_MULT_DIFFUSE_NODE = "Diffuse=DC*DLF"
_MULT_SPECULAR_NODE = "Specular=SC*SL"
_SUM_DIFF_SPEC_NODE = "DiffSpec=Diffuse+Specular"
_SUM_FINAL_NODE = "Result=DiffSpec+Env"
_OUT_MAT_NODE = "OutMaterial"


def get_node_group():
    """Gets node group for calcualtion of final lighting color.

    DL = lighting diffuse
    SL = lighting specular
    AAC = additional ambient color (which is environment ambient)
    AC = attributes add ambient
    DC = attributes diffuse color
    SC = attirbutes specular color
    ENV = provided environment pass color

    R = (DC * (DL + (AAC * AC)) + (SC * SL) + ENV

    :return: node group which calculates finall shader output color
    :rtype: bpy.types.NodeGroup
    """

    if COMPOSE_LIGHTING_G not in bpy.data.node_groups:
        __create_node_group__()

    return bpy.data.node_groups[COMPOSE_LIGHTING_G]


def set_additional_ambient_col(color):
    """Sets ambient color which should be used when material is using additional ambient.

    :param color: ambient color from sun profile (not converted to srgb)
    :type color: list[float] | tuple[float]
    """
    get_node_group().nodes[_ADD_AMBIENT_COL_NODE].outputs[0].default_value = _convert_utils.to_node_color(color, from_linear=True)


def reset_lighting_params():
    """Resets lighting to default values.
    """
    set_additional_ambient_col(_LIGHTING_consts.default_ambient)


def __create_node_group__():
    """Creates compose lighting group.

    Inputs: AddAmbient, Diffuse Color, Specular Color, Env Color, Diffuse Lighting, Specular Lighting, Alpha
    Outputs: Shader, Color, Alpha
    """

    start_pos_x = 0

    pos_x_shift = 185

    compose_light_g = bpy.data.node_groups.new(type="ShaderNodeTree", name=COMPOSE_LIGHTING_G)

    # inputs defining
    add_ambient_socket = compose_light_g.interface.new_socket(name = "AddAmbient", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
    add_ambient_socket.attribute_domain = 'POINT'
    
    diffuse_color_socket = compose_light_g.interface.new_socket(name = "Diffuse Color", in_out = 'INPUT', socket_type = 'NodeSocketColor')
    diffuse_color_socket.attribute_domain = 'POINT'
    
    specular_color_socket = compose_light_g.interface.new_socket(name = "Specular Color", in_out = 'INPUT', socket_type = 'NodeSocketColor')
    specular_color_socket.attribute_domain = 'POINT'
    
    env_color_socket = compose_light_g.interface.new_socket(name = "Env Color", in_out = 'INPUT', socket_type = 'NodeSocketColor')
    env_color_socket.attribute_domain = 'POINT'
    
    diffuse_lighting_socket = compose_light_g.interface.new_socket(name = "Diffuse Lighting", in_out = 'INPUT', socket_type = 'NodeSocketColor')
    diffuse_lighting_socket.attribute_domain = 'POINT'
    
    specular_lighting_socket = compose_light_g.interface.new_socket(name = "Specular Lighting", in_out = 'INPUT', socket_type = 'NodeSocketColor')
    specular_lighting_socket.attribute_domain = 'POINT'
    
    alpha_socket = compose_light_g.interface.new_socket(name = "Alpha", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
    alpha_socket.attribute_domain = 'POINT'

    input_n = compose_light_g.nodes.new("NodeGroupInput")
    input_n.location = (start_pos_x - pos_x_shift, 0)

    # outputs defining
    shader_socket = compose_light_g.interface.new_socket(name = "Shader", in_out = 'OUTPUT', socket_type = 'NodeSocketShader')
    shader_socket.attribute_domain = 'POINT'

    color_socket = compose_light_g.interface.new_socket(name = "Color", in_out = 'OUTPUT', socket_type = 'NodeSocketColor')
    color_socket.attribute_domain = 'POINT'

    alpha_socket = compose_light_g.interface.new_socket(name = "Alpha", in_out = 'OUTPUT', socket_type = 'NodeSocketFloat')
    alpha_socket.attribute_domain = 'POINT'

    output_n = compose_light_g.nodes.new("NodeGroupOutput")
    output_n.location = (start_pos_x + pos_x_shift * 8, 0)

    # nodes creation
    add_ambient_col_n = compose_light_g.nodes.new("ShaderNodeRGB")
    add_ambient_col_n.name = add_ambient_col_n.label = _ADD_AMBIENT_COL_NODE
    add_ambient_col_n.location = (start_pos_x + pos_x_shift * 1, 400)

    mult_aa_node = compose_light_g.nodes.new("ShaderNodeVectorMath")
    mult_aa_node.name = mult_aa_node.label = _MULT_AA_NODE
    mult_aa_node.location = (start_pos_x + pos_x_shift * 2, 350)
    mult_aa_node.operation = "MULTIPLY"

    sum_dl_final_n = compose_light_g.nodes.new("ShaderNodeVectorMath")
    sum_dl_final_n.name = sum_dl_final_n.label = _SUM_DL_FINAL_NODE
    sum_dl_final_n.location = (start_pos_x + pos_x_shift * 3, 300)
    sum_dl_final_n.operation = "ADD"

    mult_diffuse_n = compose_light_g.nodes.new("ShaderNodeVectorMath")
    mult_diffuse_n.name = mult_diffuse_n.label = _MULT_DIFFUSE_NODE
    mult_diffuse_n.location = (start_pos_x + pos_x_shift * 4, 250)
    mult_diffuse_n.operation = "MULTIPLY"

    mult_specular_n = compose_light_g.nodes.new("ShaderNodeVectorMath")
    mult_specular_n.name = mult_specular_n.label = _MULT_SPECULAR_NODE
    mult_specular_n.location = (start_pos_x + pos_x_shift * 4, 50)
    mult_specular_n.operation = "MULTIPLY"

    sum_diff_spec_n = compose_light_g.nodes.new("ShaderNodeVectorMath")
    sum_diff_spec_n.name = sum_diff_spec_n.label = _SUM_DIFF_SPEC_NODE
    sum_diff_spec_n.location = (start_pos_x + pos_x_shift * 5, 100)
    sum_diff_spec_n.operation = "ADD"

    sum_final_n = compose_light_g.nodes.new("ShaderNodeVectorMath")
    sum_final_n.name = sum_final_n.label = _SUM_FINAL_NODE
    sum_final_n.location = (start_pos_x + pos_x_shift * 6, 0)
    sum_final_n.operation = "ADD"

    out_mat_node = compose_light_g.nodes.new("ShaderNodeGroup")
    out_mat_node.name = out_mat_node.label = _OUT_MAT_NODE
    out_mat_node.location = (start_pos_x + pos_x_shift * 7, 0)
    out_mat_node.node_tree = output_shader_ng.get_node_group()

    # links creation
    compose_light_g.links.new(mult_aa_node.inputs[0], add_ambient_col_n.outputs["Color"])
    compose_light_g.links.new(mult_aa_node.inputs[1], input_n.outputs["AddAmbient"])

    compose_light_g.links.new(sum_dl_final_n.inputs[0], mult_aa_node.outputs[0])
    compose_light_g.links.new(sum_dl_final_n.inputs[1], input_n.outputs["Diffuse Lighting"])

    compose_light_g.links.new(mult_diffuse_n.inputs[0], sum_dl_final_n.outputs["Vector"])
    compose_light_g.links.new(mult_diffuse_n.inputs[1], input_n.outputs["Diffuse Color"])

    compose_light_g.links.new(mult_specular_n.inputs[0], input_n.outputs["Specular Color"])
    compose_light_g.links.new(mult_specular_n.inputs[1], input_n.outputs["Specular Lighting"])

    compose_light_g.links.new(sum_diff_spec_n.inputs[0], mult_diffuse_n.outputs[0])
    compose_light_g.links.new(sum_diff_spec_n.inputs[1], mult_specular_n.outputs[0])

    compose_light_g.links.new(sum_final_n.inputs[0], sum_diff_spec_n.outputs["Vector"])
    compose_light_g.links.new(sum_final_n.inputs[1], input_n.outputs["Env Color"])

    compose_light_g.links.new(out_mat_node.inputs["Color"], sum_final_n.outputs["Vector"])
    compose_light_g.links.new(out_mat_node.inputs["Alpha"], input_n.outputs["Alpha"])

    compose_light_g.links.new(output_n.inputs["Shader"], out_mat_node.outputs["Shader"])
    compose_light_g.links.new(output_n.inputs["Color"], sum_final_n.outputs["Vector"])
    compose_light_g.links.new(output_n.inputs["Alpha"], input_n.outputs["Alpha"])

    # set default lighting
    reset_lighting_params()
