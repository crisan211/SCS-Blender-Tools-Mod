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

import bmesh
import bpy
import numpy
from mathutils import Color
from time import time
from bpy.props import StringProperty, FloatProperty
from io_scs_tools_mod.consts import Mesh as _MESH_consts
from io_scs_tools_mod.consts import LampTools as _LT_consts
from io_scs_tools_mod.consts import VertexColorTools as _VCT_consts
from io_scs_tools_mod.utils import mesh as _mesh_utils
from io_scs_tools_mod.utils import view3d as _view3d_utils
from io_scs_tools_mod.utils.printout import lprint


class LampTool:
    """
    Wrapper class for better navigation in file
    """

    class SCS_TOOLS_OT_SetLampmaskUV(bpy.types.Operator):
        bl_label = "Set UV to lamp mask"
        bl_idname = "mesh.scs_tools_set_lampmask_uv"
        bl_description = "Sets offset for lamp mask UV according to given vehicle side or auxiliary color."

        vehicle_side: StringProperty(
            description="",
            default="",
            options={'HIDDEN'},
        )

        aux_color: StringProperty(
            description="",
            default="",
            options={'HIDDEN'},
        )

        traffic_light_color: StringProperty(
            description="",
            default="",
            options={'HIDDEN'},
        )

        @classmethod
        def poll(cls, context):
            return context.object is not None and context.object.mode == "EDIT"

        def execute(self, context):
            mesh = context.object.data
            bm = bmesh.from_edit_mesh(mesh)  # use bmesh module because we are working in edit mode

            # decide which offset to use depending on vehicle side, auxiliary color and traffic light type
            offset_y = 0
            if _LT_consts.VehicleSides.FrontLeft.name == self.vehicle_side:  # vehicle lights checking
                offset_x = 0
            elif _LT_consts.VehicleSides.FrontRight.name == self.vehicle_side:
                offset_x = 1
            elif _LT_consts.VehicleSides.RearLeft.name == self.vehicle_side:
                offset_x = 2
            elif _LT_consts.VehicleSides.RearRight.name == self.vehicle_side:
                offset_x = 3
            elif _LT_consts.VehicleSides.Middle.name == self.vehicle_side:
                offset_x = 4
            elif _LT_consts.AuxiliaryLampColors.White.name == self.aux_color:  # auxiliary lights checking
                offset_x = 0
            elif _LT_consts.AuxiliaryLampColors.Orange.name == self.aux_color:
                offset_x = 1
            elif _LT_consts.TrafficLightTypes.Red.name == self.traffic_light_color:  # traffic lights checking
                offset_x = 1
                offset_y = 1
            elif _LT_consts.TrafficLightTypes.Yellow.name == self.traffic_light_color:
                offset_x = 2
                offset_y = 2
            elif _LT_consts.TrafficLightTypes.Green.name == self.traffic_light_color:
                offset_x = 3
                offset_y = 3
            else:
                self.report({"ERROR"}, "Unsupported vehicle side or auxiliary color or traffic light color!")
                return {"FINISHED"}

            polys_changed = 0
            for face in bm.faces:

                if face.select and len(context.object.material_slots) > 0:
                    material = context.object.material_slots[face.material_index].material
                    if material and len(material.scs_props.shader_texture_mask_uv) > 0:

                        # use first mapping from mask texture
                        uv_lay_name = material.scs_props.shader_texture_mask_uv[0].value

                        # if mask uv layer specified by current material doesn't exists
                        # move to next face
                        if uv_lay_name not in mesh.uv_layers:
                            self.report({"ERROR"}, "UV layer: '%s' not found in this object!" % uv_lay_name)
                            break

                        uv_lay = bm.loops.layers.uv[uv_lay_name]
                        for loop in face.loops:

                            uv = loop[uv_lay].uv
                            uv = (offset_x + (uv[0] - int(uv[0])), offset_y + (uv[1] - int(uv[1])))
                            loop[uv_lay].uv = uv

                        polys_changed += 1

            # write data back if modified
            if polys_changed > 0:
                bmesh.update_edit_mesh(mesh)

            if self.vehicle_side != "":
                changed_type = self.vehicle_side
            elif self.aux_color != "":
                changed_type = self.aux_color
            else:
                changed_type = "INVALID"

            self.report({"INFO"}, "Lamp mask UV tool set %i faces to '%s'" % (polys_changed, changed_type))
            return {'FINISHED'}


class VertexColorTools:
    """
    Wrapper class for better navigation in file
    """

    class SCS_TOOLS_OT_WrapVertexColors(bpy.types.Operator):
        bl_label = "Wrap"
        bl_idname = "mesh.scs_tools_wrap_vertex_colors"
        bl_description = "Wraps vertex colors to given interval."
        bl_options = {'REGISTER', 'UNDO'}

        wrap_type: StringProperty(
            options={'HIDDEN'},
        )
        min: FloatProperty(
            name="Min Value",
            description="New minimal possible value for vertex colors.",
            default=0.4,
            max=0.5,
            min=0.0,
        )
        max: FloatProperty(
            name="Max Value",
            description="New maximal possible value for vertex colors.",
            default=0.6,
            max=1.0,
            min=0.5
        )

        original_col = {}
        """Dictionary of original vertex colors which are used for calculation
        if operator interval is changed"""

        @classmethod
        def poll(cls, context):
            return context.object is not None and context.object.mode == "VERTEX_PAINT" and len(context.object.data.color_attributes) > 0

        def __init__(self):
            self.original_col = {}

        def __del__(self):
            self.original_col.clear()

        def execute(self, context):

            mesh = context.object.data
            interval = self.max - self.min
            vcolor_layer = mesh.color_attributes.active_color

            for poly in mesh.polygons:

                # calculate wrapped value for face it wrap type is all or face is selected
                if self.wrap_type == _VCT_consts.WrapType.All or (self.wrap_type == _VCT_consts.WrapType.Selected and poly.select):

                    if vcolor_layer.domain == 'POINT':
                        data_iterator = poly.vertices
                    elif vcolor_layer.domain == 'CORNER':
                        data_iterator = poly.loop_indices
                    else:
                        raise TypeError("Invalid vertex color domain type!")

                    for idx in data_iterator:

                        # cache original vertex colors because of update on interval change
                        if idx not in self.original_col:
                            color = Color(vcolor_layer.data[idx].color[:3]).from_scene_linear_to_srgb()
                            self.original_col[idx] = (color[0], color[1], color[2])

                        new_color = Color((
                            self.original_col[idx][0] * interval + self.min,
                            self.original_col[idx][1] * interval + self.min,
                            self.original_col[idx][2] * interval + self.min,
                        )).from_srgb_to_scene_linear()

                        vcolor_layer.data[idx].color[:3] = new_color[:]

            self.report({"INFO"}, "Vertex colors wrapped!")
            return {'FINISHED'}

    class SCS_TOOLS_OT_PrintVertexColorsStats(bpy.types.Operator):
        bl_label = "Get Statistics"
        bl_idname = "mesh.scs_tools_print_vertex_colors_stats"
        bl_description = "Prints out min, max and avarage vertex color for active vertex color layer."
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            return context.object is not None and context.object.mode == "VERTEX_PAINT" and len(context.object.data.color_attributes) > 0

        def execute(self, context):

            mesh = context.object.data
            vcolor_layer = mesh.color_attributes.active_color

            c_min = [100] * 3
            c_max = [0] * 3
            c_sum = [0] * 3
            colors_count = 0
            for vcol_item in vcolor_layer.data:
                curr_col = vcol_item.color

                for i in range(0, 3):
                    if curr_col[i] < c_min[i]:
                        c_min[i] = curr_col[i]

                    if curr_col[i] > c_max[i]:
                        c_max[i] = curr_col[i]

                    c_sum[i] += curr_col[i]

                colors_count += 1

            c_avg = []
            for i in range(0, 3):
                c_avg.append(c_sum[i] / colors_count)

            # we want to represent srgb values, that we would/will export
            c_min = list(Color(c_min).from_scene_linear_to_srgb())
            c_max = list(Color(c_max).from_scene_linear_to_srgb())
            c_avg = list(Color(c_avg).from_scene_linear_to_srgb())

            self.report({"INFO"}, "Vertex color stats: MIN(%.2f, %.2f, %.2f), MAX(%.2f, %.2f, %.2f), AVG(%.2f, %.2f, %.2f)" %
                        (c_min[0], c_min[1], c_min[2],
                         c_max[0], c_max[1], c_max[2],
                         c_avg[0], c_avg[1], c_avg[2]))

            return {'FINISHED'}

    class SCS_TOOLS_OT_AddVertexColorsToActive(bpy.types.Operator):
        bl_label = "Add Vertex Colors To Active"
        bl_idname = "mesh.scs_tools_add_vertex_colors_to_active"
        bl_description = "Adds missing vertex colors layers to active object."
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            return context.object is not None and context.object.type == 'MESH' and context.object.active_material is not None

        def execute(self, context):
            default_color = tuple(Color((0.5,) * 3).from_srgb_to_scene_linear()) + (1.0,)

            layer_name = _MESH_consts.default_vcol
            layer_a_name = _MESH_consts.default_vcol + _MESH_consts.vcol_a_suffix
            old_active_col_i = context.object.data.color_attributes.active_index

            for curr_lay_name in (layer_name, layer_a_name):

                if curr_lay_name not in context.object.data.color_attributes:

                    vcolor = context.object.data.color_attributes.new(name=curr_lay_name, type='FLOAT_COLOR', domain='CORNER')
                    vcolor.name = curr_lay_name  # repeat naming step to make sure it's properly named

                    # setting neutral value (0.5) to all colors
                    for vertex_col_data in context.object.data.color_attributes[curr_lay_name].data:
                        vertex_col_data.color = default_color

            # restore active or set to default vcol if there was none
            if old_active_col_i is None:
                context.object.data.color_attributes.active_color = context.object.data.color_attributes[layer_name]
            else:
                context.object.data.color_attributes.active_color = context.object.data.color_attributes[old_active_col_i]

            return {'FINISHED'}

    class SCS_TOOLS_OT_AddVertexColorsToAll(bpy.types.Operator):
        bl_label = "Add Vertex Colors To All"
        bl_idname = "mesh.scs_tools_add_vertex_colors_to_all"
        bl_description = "Adds missing vertex colors layers to all objects using this material."
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            return context.object is not None and context.object.type == 'MESH' and context.object.active_material is not None

        def execute(self, context):
            default_color = tuple(Color((0.5,) * 3).from_srgb_to_scene_linear()) + (1.0,)

            layer_name = _MESH_consts.default_vcol
            layer_a_name = _MESH_consts.default_vcol + _MESH_consts.vcol_a_suffix

            objs_using_active_material = []

            # search for all objects using active material and put them into list
            for obj in bpy.data.objects:

                # ignore none mesh objects
                if obj.type != 'MESH':
                    continue

                for mat_slot in obj.material_slots:
                    if mat_slot.material and mat_slot.material.name == context.object.active_material.name:
                        objs_using_active_material.append(obj)
                        break

            # add missing vertex color layers to found objects
            for obj in objs_using_active_material:
                old_active_col_i = obj.data.color_attributes.active_index

                for curr_lay_name in (layer_name, layer_a_name):

                    if curr_lay_name not in obj.data.color_attributes:

                        vcolor = obj.data.color_attributes.new(name=curr_lay_name, type='FLOAT_COLOR', domain='CORNER')
                        vcolor.name = curr_lay_name  # repeat naming step to make sure it's properly named

                        # setting neutral value (0.5) to all colors
                        for vertex_col_data in obj.data.color_attributes[curr_lay_name].data:
                            vertex_col_data.color = default_color

                # restore active or set to default vcol if there was none
                if old_active_col_i is None:
                    obj.data.color_attributes.active_color = obj.data.color_attributes[layer_name]
                else:
                    obj.data.color_attributes.active_color = obj.data.color_attributes[old_active_col_i]

            return {'FINISHED'}

    class SCS_TOOLS_OT_StartVColoring(bpy.types.Operator):
        bl_label = "VColoring - Edit"
        bl_idname = "mesh.scs_tools_start_vcoloring"
        bl_description = "Enters complex vertex paint edit mode, where user can edit one of 4 vertex color layers: color, decal, ao, ao2.\n" \
                         "This layers are baked together by extra overlay functions designed for usage in map assets."
        bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

        layer_name: StringProperty(default="", description="Name of the layer to edit currently.")

        __static_active_layer = _VCT_consts.ColoringLayersTypes.Color  # by default start editing color
        """Stores currently active vertex color layer. Used for switching to other modes when user invokes this operator again."""
        __static_is_active = False
        """Flag indicating weather this operator is running already or not. To prevent multiple instances of this operator."""

        __timer = None
        """Storing timer reference for modal execution."""
        __active_object_name = None
        """Storing name of the currently active object for vertex painting, used to be able to abort operator if user selects other object."""
        __active_object_mode = None
        """Storing mode of currently active object, to be able to abort operator if user jumps out of vertex mode."""
        __vcolors_buffer_arrays = []
        """Used for storing vertex color layers data when rebaking. Should be array of 4 numpy ndarrays as we are rebaking from 4 layers."""
        __old_vcolors_array_hash = None
        """Storing hash value of active vertex color array values. Used to identify weather rebake should happen or not."""

        def __get_active_object__(self):
            """Returns operator cached active object.

            :return: active object or None if object was somehow deleted
            :rtype: bpy.types.Object | None
            """
            return bpy.data.objects[self.__active_object_name] if self.__active_object_name in bpy.data.objects else None

        def initialize(self, context):
            """Initialize operator with timer, active object data, creates needed vertex color layers and fills default values.

            :param context: blender context
            :type context: bpy.types.Context
            :return: Blender operator return set
            :rtype: set
            """

            wm = context.window_manager

            self.__timer = wm.event_timer_add(0.15, window=context.window)
            self.__active_object_name = context.active_object.name
            self.__active_object_mode = context.active_object.mode

            VertexColorTools.SCS_TOOLS_OT_StartVColoring.__static_is_active = True

            wm.modal_handler_add(self)

            # now ensure all needed vertex color layers are initialized with proper colors
            mesh = self.__get_active_object__().data
            for layer_name in _VCT_consts.ColoringLayersTypes.as_list():

                if layer_name in mesh.color_attributes:
                    continue

                vcolor = mesh.color_attributes.new(name=layer_name, type='FLOAT_COLOR', domain='CORNER')

                buffer = None
                color = list(Color((0.5,) * 3).from_srgb_to_scene_linear()) + [1.0, ]  # our default is 0.5, even for alpha where 0.5 is also max
                if layer_name == _VCT_consts.ColoringLayersTypes.Color:
                    buffer = numpy.array(color * len(mesh.loops))
                elif layer_name == _VCT_consts.ColoringLayersTypes.Decal:
                    buffer = numpy.array(color * len(mesh.loops))
                elif layer_name == _VCT_consts.ColoringLayersTypes.AO:
                    buffer = numpy.array(color * len(mesh.loops))
                elif layer_name == _VCT_consts.ColoringLayersTypes.AO2:
                    buffer = numpy.array(color * len(mesh.loops))

                if buffer is not None:
                    vcolor.data.foreach_set("color", buffer)

            # initialize buffers and hash
            self.__vcolors_buffer_arrays = [
                numpy.array([0.0] * (len(mesh.loops) * 4)),
                numpy.array([0.0] * (len(mesh.loops) * 4)),
                numpy.array([0.0] * (len(mesh.loops) * 4)),
                numpy.array([0.0] * (len(mesh.loops) * 4))
            ]

            self.__old_vcolors_array_hash = None

            return {'RUNNING_MODAL'}

        def switch_to_layer(self, layer_name):
            """Make given vertex color layer as active.

            :param layer_name: name of vertex color layer to which we want to switch
            :type layer_name: str
            :returns: True if layer was properly switch of it was already active, False if layer doesn't exists
            :rtype: bool
            """

            obj_vcolors = self.__get_active_object__().data.color_attributes

            if layer_name not in obj_vcolors:
                return False

            if layer_name == obj_vcolors.active_color.name:
                return True

            obj_vcolors.active_color = obj_vcolors[layer_name]
            lprint("D Changed active vertex layer to: %s" % layer_name)
            return True

        @classmethod
        def abort(cls):

            if cls.__static_is_active:
                # just put it into object mode modal callback will automatically abort in that case
                bpy.ops.object.mode_set(mode="OBJECT")

        @classmethod
        def poll(cls, context):

            is_active_mesh = context.object is not None and context.object.type == "MESH"
            valid_when_active = is_active_mesh and cls.__static_is_active and context.object.mode == "VERTEX_PAINT"
            valid_when_inactive = is_active_mesh and not cls.__static_is_active and context.object.mode == "OBJECT"

            return valid_when_active or valid_when_inactive

        def modal(self, context, event):

            active_obj = self.__get_active_object__()

            active_object_changed = active_obj != context.active_object

            # abort immeadiatelly if active object was changed
            if active_object_changed:
                self.cancel(context)
                return {'CANCELLED'}

            is_object_mode_changed = self.__active_object_mode != context.active_object.mode

            # allow changing into the edit mode as user might go there just to reselect
            # masked faces on which he wants to paint
            if is_object_mode_changed and context.active_object.mode == "EDIT":
                return {'PASS_THROUGH'}

            # abort if active object mode has changed
            if is_object_mode_changed:
                self.cancel(context)
                return {'CANCELLED'}

            if event.type == "ESC" and event.value == "PRESS":
                self.cancel(context)
                return {'FINISHED'}

            # always ensure to be in proper vertex color layer
            self.switch_to_layer(self.__static_active_layer)

            # do rebake only on timer event
            if event.type == "TIMER":

                start_time = time()
                new_hash = _mesh_utils.vcoloring_rebake(active_obj.data, self.__vcolors_buffer_arrays, self.__old_vcolors_array_hash)
                if new_hash is None:  # sth went really wrong, no sufficient data
                    lprint("E VColoring rebake failed! Contact the developer...")
                elif new_hash != self.__old_vcolors_array_hash:  # rebake happened
                    self.__old_vcolors_array_hash = new_hash
                    _view3d_utils.tag_redraw_all_view3d()  # trigger view update to see rebaked colors

                    lprint("D VColoring real-time rebake took: %.4fs" % (time() - start_time))
                else:  # checked active vertex color layer, but nothing had to be recalculated
                    lprint("D VColoring checkup took: %.4fs" % (time() - start_time))

            return {'PASS_THROUGH'}

        def execute(self, context):

            # user requested layer change
            if self.layer_name != "" and self.layer_name in _VCT_consts.ColoringLayersTypes.as_list():
                VertexColorTools.SCS_TOOLS_OT_StartVColoring.__static_active_layer = self.layer_name

            # already active abort another one
            if VertexColorTools.SCS_TOOLS_OT_StartVColoring.__static_is_active:
                return {'CANCELLED'}

            # ensure our output layers definition
            #
            # NOTE: here is the deal: when switching to vertex paint mode
            # blender creates first color attribute if none is present.
            # As it happens it's name is the same as we use, so to ensure it creates proper
            # color type and domain we rather create our output layers beforehand.
            mesh_vcolors = context.active_object.data.color_attributes
            if _MESH_consts.default_vcol not in mesh_vcolors:
                mesh_vcolors.new(name=_MESH_consts.default_vcol, type='FLOAT_COLOR', domain='CORNER')

            if _MESH_consts.default_vcol + _MESH_consts.vcol_a_suffix not in mesh_vcolors:
                mesh_vcolors.new(name=_MESH_consts.default_vcol + _MESH_consts.vcol_a_suffix, type='FLOAT_COLOR', domain='CORNER')

            bpy.ops.object.mode_set(mode="VERTEX_PAINT")

            # NOTE: We have to push undo event otherwise undo was just
            # ignoring all the painting that has been done and
            # aborted this operator. Practically undo was useless.
            bpy.ops.ed.undo_push(message="[%s] - Switching to vertex paint mode" % self.bl_label)

            return self.initialize(context)

        def cancel(self, context):

            active_obj = self.__get_active_object__()

            # finish operator execution - go back to object mode
            if active_obj.mode == "VERTEX_PAINT":
                with context.temp_override(mode='OBJECT', active_object=active_obj):
                    bpy.ops.object.mode_set()

            # one last time rebake
            start_time = time()
            new_hash = _mesh_utils.vcoloring_rebake(active_obj.data, self.__vcolors_buffer_arrays, self.__old_vcolors_array_hash)

            if new_hash is None:
                lprint("E VColoring rebake failed! Contact the developer...")
            else:
                lprint("D VColoring rebake on exit took: %.4fs" % (time() - start_time))

            # cleanup
            wm = context.window_manager
            wm.event_timer_remove(self.__timer)

            self.__timer = None
            self.__active_object_name = None
            self.__active_object_mode = None
            self.__old_vcolors_array_hash = None
            self.__vcolors_buffer_arrays = []

            VertexColorTools.SCS_TOOLS_OT_StartVColoring.__static_is_active = False
            lprint("D VColoring operator cleanup done, exiting now!")

    class SCS_TOOLS_OT_ExitVColoring(bpy.types.Operator):
        bl_label = "VColoring - Exit"
        bl_idname = "mesh.scs_tools_exit_vcoloring"
        bl_description = "Exits complex vertex paint edit mode."
        bl_options = {'REGISTER', 'INTERNAL'}

        @classmethod
        def poll(cls, context):
            return VertexColorTools.SCS_TOOLS_OT_StartVColoring.poll(context)

        def execute(self, context):
            VertexColorTools.SCS_TOOLS_OT_StartVColoring.abort()
            return {'FINISHED'}

    class SCS_TOOLS_OT_RebakeVColoring(bpy.types.Operator):
        bl_label = "VColoring - Rebake"
        bl_idname = "mesh.scs_tools_rebake_vcoloring"
        bl_description = "Rebakes 4 vertex color layers (use it if you edited any of 4 extra vertex color layers by hand)."
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):

            if context.object is None or context.object.type != "MESH":
                return False

            has_needed_vcolors = (
                _VCT_consts.ColoringLayersTypes.Color in context.object.data.color_attributes and
                _VCT_consts.ColoringLayersTypes.Decal in context.object.data.color_attributes and
                _VCT_consts.ColoringLayersTypes.AO in context.object.data.color_attributes and
                _VCT_consts.ColoringLayersTypes.AO2 in context.object.data.color_attributes
            )
            return has_needed_vcolors

        def execute(self, context):
            mesh = context.active_object.data

            start_time = time()

            # prepare buffers
            vcolors_buffer_arrays = [
                numpy.array([0.0] * (len(mesh.loops) * 4)),
                numpy.array([0.0] * (len(mesh.loops) * 4)),
                numpy.array([0.0] * (len(mesh.loops) * 4)),
                numpy.array([0.0] * (len(mesh.loops) * 4))
            ]

            # rebake
            result = _mesh_utils.vcoloring_rebake(mesh, vcolors_buffer_arrays, None)
            if result:

                message = "I Successful! Vertex colors rebake took: %.4fs" % (time() - start_time)
                lprint(message)
                self.report({'INFO'}, message[2:])

                # trigger view update to see rebaked colors, with fake reassignment.
                mesh.color_attributes.active_color = mesh.color_attributes.active_color

            else:

                message = "E Failed! This shouldn't happen, please contact the developer..."
                lprint(message)
                self.report({'ERROR'}, message[2:])

            return {'FINISHED'}


classes = (
    LampTool.SCS_TOOLS_OT_SetLampmaskUV,

    VertexColorTools.SCS_TOOLS_OT_AddVertexColorsToActive,
    VertexColorTools.SCS_TOOLS_OT_AddVertexColorsToAll,
    VertexColorTools.SCS_TOOLS_OT_PrintVertexColorsStats,
    VertexColorTools.SCS_TOOLS_OT_StartVColoring,
    VertexColorTools.SCS_TOOLS_OT_ExitVColoring,
    VertexColorTools.SCS_TOOLS_OT_RebakeVColoring,
    VertexColorTools.SCS_TOOLS_OT_WrapVertexColors,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
