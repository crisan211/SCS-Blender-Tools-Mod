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

# Copyright (C) 2013-2022: SCS Software

from io_scs_tools_mod.utils.convert import float_to_hex_string, float_array_to_hex_string
from io_scs_tools_mod.utils.printout import lprint

_LIST_TYPE = list
_STR_TYPE = str
_FLOAT_TYPE = float
_INT_TYPE = int
_STR_PROHIBITED_TYPES = {"FLOAT", "FLOAT2", "FLOAT3", "FLOAT4", "FLOAT5", "FLOAT6", "FLOAT7", "FLOAT8", "FLOAT9", "FLOAT4x4", "INT", "INT2", "STRING"}


def _format_matrix(mat, ind, offset):
    str_mat = ""
    for line in mat:
        str_line = ""
        for val in line:
            str_line = str_line + " " + float_to_hex_string(val) + " "
        if str_mat == "":
            str_mat = str_line
        else:
            str_mat = str_mat + "\n" + ind + offset + str_line[:-1]
    return str_mat


def _format_bone(data_line, ind):
    """Takes a list or tuple of float numbers and return
    formatted line of hexadecimal values in a string."""
    line_start = str(ind + (8 * " "))
    bone_name = data_line[1]
    if data_line[2]:
        bone_parent = str(data_line[2].name)
    else:
        bone_parent = ""
    bone_matrix = _format_matrix(data_line[3], ind, str(17 * " "))
    data = str('Name:  "' + bone_name + '"\n' + line_start + 'Parent: "' + bone_parent + '"\n' + line_start + 'Matrix: (' + bone_matrix + ' )')
    return data


def _format_data(data_line, data_line_type, spaces=5, data_hex=True):
    """Takes a list or tuple of values and return
    formatted line values in a string."""

    if data_line_type == _FLOAT_TYPE:
        if data_hex:
            data = float_array_to_hex_string(data_line)
            # data = '  '.join([float_to_hex_string(x) for x in data_line])
        else:
            data = ' '.join([str(x) for x in data_line])
    elif data_line_type == _STR_TYPE:
        data = ' '.join(['"%s"' % x for x in data_line])
    else:
        if spaces == 0:
            data = ' '.join([str(x) for x in data_line])
        else:
            data = ' '.join([str(x).ljust(spaces, ' ') for x in data_line])

    return data


def _write_properties_and_data(fw, section, ind, print_info):
    """Takes a single section data and writes all its "properties"
    and "data" to the file."""
    for prop in section.props:
        # if type(prop[1]) == type(None):
        if prop[1] is None:
            fw('%s%s:\n' % (ind, prop[0]))
        # elif type(prop[1]) == type([]):
        elif isinstance(prop[1], _LIST_TYPE):
            if prop[1][0] == '&':
                fw('%s%s: %s\n' % (ind, prop[0], _format_data(prop[1][1], type(prop[1][1][0]))))
            elif prop[1][0] == '&&':
                if len(prop[1][1]) == 1:
                    fw('%s%s: ( %s )\n' % (ind, prop[0], prop[1][1][0]))
                else:
                    fw('%s%s: ( %s )\n' % (ind, prop[0], _format_data(prop[1][1], type(prop[1][1][0]))))
            elif prop[1][0] == 'i':
                fw('%s%s: ( %s )\n' % (ind, prop[0], _format_data(prop[1][1], type(prop[1][1][0]), 0, False)))
            elif prop[1][0] == 'ii':
                fw('%s%s: ( %s )\n' % (ind, prop[0], _format_data(prop[1][1], type(prop[1][1][0]), 0)))
            elif prop[1][0] == '#':
                fw('%s# %s\n' % (ind, prop[0]))
            else:
                fw('%s%s: %s\n' % (ind, prop[0], str(prop[1])[1:-1].replace(",", "").replace("'", "\"")))
        # elif type(prop[1]) == type("") and prop[1] not in (
        elif isinstance(prop[1], _STR_TYPE) and prop[1] not in _STR_PROHIBITED_TYPES:
            if prop[0] == '#':
                fw('%s# %s\n' % (ind, prop[1]))
            elif prop[0] == '':
                fw('\n')
            else:
                fw('%s%s: "%s"\n' % (ind, prop[0], prop[1]))
        else:
            fw('%s%s: %s\n' % (ind, prop[0], prop[1]))
        if print_info:
            print('%sProp: %s' % (ind, prop))

    data_line_type = None
    for data_line_i, data_line in enumerate(section.data):
        # print('-- data_line: %s' % str(data_line))
        formated_data_line = None
        # if len(data_line) > 1:
        if data_line[0] == "__bone__":
            formated_data_line = _format_bone(data_line, ind)
            fw('%s%s( %s\n%s   )\n' % (ind, str(data_line_i).ljust(6, ' '), formated_data_line, ind))
        elif data_line[0] == "__string__":
            fw('%s%s( "%s" )\n' % (ind, str(data_line_i).ljust(5, ' '), data_line[1]))
        elif data_line[0] == "__skin__":
            fw('%s%s( ( %s  %s  %s )\n' % (
                ind, str(data_line_i).ljust(6, ' '), float_to_hex_string(data_line[1][0][0]), float_to_hex_string(data_line[1][0][1]),
                float_to_hex_string(data_line[1][0][2])))

            weight_string = ""
            for i_i, i in enumerate(data_line[1][1]):
                if i_i == 0:
                    weight_string = weight_string + str(i[0]).ljust(5, ' ') + float_to_hex_string(i[1])
                else:
                    weight_string = weight_string + "   " + str(i[0]).ljust(5, ' ') + float_to_hex_string(i[1])

            vertex_indices_string = ""
            for i_i, i in enumerate(data_line[1][2]):
                vertex_indices_string = vertex_indices_string + str(i).ljust(6, ' ')

            fw('%s%sWeights: %s%s\n' % (ind, 8 * " ", str(len(data_line[1][1])).ljust(7, ' '), weight_string))
            fw('%s%sVertexIndices: %s%s\n' % (ind, 8 * " ", str(len(data_line[1][2])).ljust(7, ' '), vertex_indices_string))
            fw('%s%s)\n' % (ind, 6 * " "))
        elif data_line[0] == "__matrix__":
            # print('MATRIX - data_line: %s' % str(data_line))
            anim_matrix = _format_matrix(data_line[1], ind, str(7 * " "))
            fw('%s%s( %s )\n' % (ind, str(data_line_i).ljust(5, ' '), anim_matrix))
        elif data_line[0] == "__time__":
            # print('TIME - data_line: %s' % str(data_line))
            fw('%s%s( %s )\n' % (ind, str(data_line_i).ljust(5, ' '), float_to_hex_string(data_line[1])))
        else:
            # acquire data type only on first line, rest should be of same type
            if data_line_i == 0:
                if isinstance(data_line[0], float):
                    data_line_type = _FLOAT_TYPE
                elif isinstance(data_line[0], str):
                    data_line_type = _STR_TYPE
            formated_data_line = _format_data(data_line, data_line_type)
            fw('%s%s( %s )\n' % (ind, str(data_line_i).ljust(5, ' '), formated_data_line))
        if print_info:
            print('%sdata: %s' % (ind, formated_data_line))


def _write_section(fw, section, ind, orig_ind, print_info):
    """This function writes the nested sections. It recursively
    calls itself to write all levels in data hierarchy."""
    fw('%s%s {\n' % (ind, section.type))
    if print_info:
        print('%sSEC.: "%s"' % (ind, section.type))
    in_ind = ind
    ind = ind + orig_ind
    _write_properties_and_data(fw, section, ind, print_info)
    for sec in section.sections:
        _write_section(fw, sec, ind, orig_ind, print_info)
    fw('%s}\n' % in_ind)


def write_data(container, filepath, ind, print_progress, print_info):
    """This function is called from outside of this script. It takes
    data container, file path and string of indentation characters
    and it saves all data to the file."""
    # print_info = 0 ## Debug printouts
    orig_ind = ind

    # WRITE TO FILE
    file = open(filepath, mode="w", encoding="utf8", newline="\n")
    fw = file.write

    sections_count = len(container)
    for section_i, section in enumerate(container):
        if section.type != "#comment":
            fw('%s {\n' % section.type)
            if print_info:
                print('SEC.: "%s"' % section.type)
            _write_properties_and_data(fw, section, ind, print_info)
            for sec in section.sections:
                _write_section(fw, sec, ind, orig_ind, print_info)
            fw('}\n')
        else:
            for comment in section.props:
                fw('%s\n' % comment[1])
        if print_progress:
            lprint("S Writting %s file - %i%% done ...", (filepath[-3:].upper(), (section_i + 1) / sections_count * 100), immediate_timeout=5)
    fw('\n')
    file.close()

    return {'FINISHED'}
