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

# Copyright (C) 2013-2019: SCS Software

from collections import OrderedDict
from io_scs_tools_mod.internals.structure import SectionData as _SectionData


class PieceSkinStream:
    class Types:
        """Enumerator class for storing types of possible PIM streams
        """
        POSITION = "_POSITION"
        NORMAL = "_NORMAL"
        TANGENT = "_TANGENT"

    class Entry:
        """Skin stream entry class for easy storing and identifying entries
        when adding new entries to skin stream.
        """

        PERCISION = 6
        """Percision constant for float values inside entry hash."""

        __position = None
        __bone_weights = None
        __vertex_indices = None

        def __init__(self, vertex_index, vertex_pos, bone_weights, bone_weights_sum):
            """Create new entry instance with given indices, position and bone weights.
            NOTE: There is no check-up for zero bone weights sum, which will result in division by zero error

            :param vertex_index: index of the vertex inside piece
            :type vertex_index: int
            :param vertex_pos: global position of the vertex in non animated state
            :type vertex_pos: tuple
            :param bone_weights: bone weights dictonary where key is bone index and value is bone weight
            :type bone_weights: dict
            :param bone_weights_sum: none-zero summary of weights of all the bones vertex is skinned to
            :type bone_weights_sum: float
            """

            self.__bone_weights = OrderedDict()
            self.__vertex_indices = OrderedDict()

            self.__position = vertex_pos

            # always normalize weights as game binary format is expecting normalized weights
            for bone_indx in bone_weights.keys():
                self.__bone_weights[bone_indx] = bone_weights[bone_indx] / bone_weights_sum

            self.add_vertex_index(vertex_index)

        def add_vertex_index(self, vertex_index):
            """Add vertex index to this skin entry.
            NOTE: in case of already existing clone value will be overwritten; so there are only unique entries

            :param vertex_index: index of the vertex inside piece
            :type vertex_index: int
            :return: True if clone was added; False if clone already exists;
            :rtype: bool
            """

            if vertex_index not in self.__vertex_indices:
                self.__vertex_indices[vertex_index] = None
                return True

            return False

        def get_first_vertex_index(self):
            """Get first index from vertex indices in this entry..

            :return: first vertex index which should be also origin of this skin entry
            :rtype: int
            """
            return next(iter(self.__vertex_indices.keys()))

        def get_hash(self):
            """Gets hash for this entry used for identifying clones in skin streams.

            :return: hash generated from position, bone indices and it's weights
            :rtype: str
            """

            perc = 10 ** self.PERCISION  # represent precision for maximal float precision inside hash key
            key = str(self.__position)

            for bone_index in sorted(self.__bone_weights.keys()):
                key += str(bone_index) + str(int(self.__bone_weights[bone_index] * perc))

            return key

        def get_weight_count(self):
            """Gets number of weights written in this skin entry. Shall be used as helper for global
            weight count inside skin stream.

            :return: number of weights
            :rtype: int
            """
            return len(self.__bone_weights)

        def get_section_repr(self):
            """Gets representation of skin entry used in skin stream section.

            :return: tuple of (position, list of (bone_index, bone_weight), list of (piece_index, vertex_index)
            :rtype: tuple
            """

            weights = []
            for bone_indx in sorted(self.__bone_weights.keys()):
                weights.append((bone_indx, self.__bone_weights[bone_indx]))

            vertex_indices = []
            for vertex_indx in sorted(self.__vertex_indices.keys()):
                vertex_indices.append(vertex_indx)

            return self.__position, weights, vertex_indices

    __format = ""  # defined by type of tag
    __tag = Types.POSITION
    __item_count = 0
    __total_weight_count = 0
    __total_vertex_index_count = 0

    _data = None

    def __init__(self, stream_type):
        """Creates new skin stream with specified type.
        :param stream_type: stream type for skin
        :type stream_type: PieceSkinStream.Types
        """

        self.__tag = stream_type

        if stream_type == PieceSkinStream.Types.POSITION:
            self.__format = "FLOAT3"
        elif stream_type == PieceSkinStream.Types.NORMAL:
            self.__format = "FLOAT3"
        elif stream_type == PieceSkinStream.Types.TANGENT:
            self.__format = "FLOAT4"

        self.__total_weight_count = 0
        self.__total_vertex_index_count = 0

        self._data = OrderedDict()

    def add_entry(self, skin_entry):
        """Adds new skin stream entry to list.
        NOTE: same entries can be added as duplicates will be ignored!
        :param skin_entry: entry of the skin stream
        :type skin_entry: PieceSkinStream.Entry
        """

        entry_hash = skin_entry.get_hash()
        if entry_hash not in self._data:  # create new entry
            self._data[entry_hash] = skin_entry
            self.__total_weight_count += skin_entry.get_weight_count()
            self.__total_vertex_index_count += 1
        else:  # add new vertex indedx and increment vertex index count if index was actually added
            vertex_index = skin_entry.get_first_vertex_index()
            if self._data[entry_hash].add_vertex_index(vertex_index):
                self.__total_vertex_index_count += 1

    def get_tag(self):
        """Returns tag which represents type of this skin stream
        :return: type tag for this skin stream
        :rtype: string
        """
        return self.__tag

    def get_as_section(self):
        """Gets skin stream represented with SectionData structure class.
        :return: packed skin stream as section data
        :rtype: io_scs_tools_mod.internals.structure.SectionData
        """

        self.__item_count = len(self._data)

        section = _SectionData("PieceSkinStream")

        section.props.append(("Format", self.__format))
        section.props.append(("Tag", self.__tag))
        section.props.append(("ItemCount", self.__item_count))
        section.props.append(("TotalWeightCount", self.__total_weight_count))
        section.props.append(("TotalVertexIndexCount", self.__total_vertex_index_count))

        for skin_entry in self._data.values():
            section.data.append(("__skin__", skin_entry.get_section_repr()))

        return section
