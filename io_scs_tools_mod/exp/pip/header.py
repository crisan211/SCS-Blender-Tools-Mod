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

# Copyright (C) 2015: SCS Software

from io_scs_tools_mod.internals.structure import SectionData as _SectionData
from io_scs_tools_mod.utils.info import get_combined_ver_str


class Header:
    def __init__(self, format_version, name):
        """Constructs header of PIP prefab.
        :param format_version: version of PIP file format
        :type format_version: int
        :param name: name of the prefab
        :type name: str
        """
        self.__format_version = format_version
        self.__source = get_combined_ver_str()
        self.__name = name

    def get_as_section(self):
        """Gets header information represented with SectionData structure class.
        :return: packed header as section data
        :rtype: io_scs_tools_mod.internals.structure.SectionData
        """

        section = _SectionData("Header")
        section.props.append(("FormatVersion", self.__format_version))
        section.props.append(("Source", self.__source))
        section.props.append(("Type", "Prefab"))
        section.props.append(("Name", self.__name))

        return section
