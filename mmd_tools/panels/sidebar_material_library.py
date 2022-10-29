import bpy
from bpy.types import PropertyGroup, Panel, Operator, Scene, UIList
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty, FloatVectorProperty, StringProperty, PointerProperty, CollectionProperty

from mmd_tools.core import material as mmd_tool_material
from mmd_tools.core import model
from mmd_tools.core.material_library import \
    get_mat_lib_root, create_mat_lib_root,\
    get_all_mat_lib, get_active_mat_lib,\
    new_mat_lib, remove_mat_lib, apply_mat_lib, cancel_mat_lib,\
    sync_mat_lib, save_mat_lib


def get_hide_icon(is_enable):
    if is_enable:
        return 'HIDE_OFF'
    else:
        return 'HIDE_ON'


def get_select_icon(is_select):
    if is_select:
        return 'RESTRICT_SELECT_OFF'
    else:
        return 'RESTRICT_SELECT_ON'


get_data_icon_value = bpy.types.UILayout.icon


class MMD_ML_MaterialLibrary_UL_Item_State(PropertyGroup):
    is_select: BoolProperty(default=False)
    mat_lib_name: StringProperty(default='')


class MMD_ML_MaterialLibrary_UL_Item(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        icon = get_select_icon(item.is_select)
        layout.prop(item, 'is_select', icon=icon, icon_only=True)
        layout.label(text=item.mat_lib_name, translate=False)


class MMD_ML_MaterialSlot_UL_Item(UIList):
    def draw_item(self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index, flt_flag):
        obj = data
        slot = item
        slot_idx = slot.slot_index

        if slot.material is None:
            layout.label(icon='SELECT_SET')
        else:
            layout.prop(slot.material.mmd_material, 'is_select', icon=get_select_icon(slot.material.mmd_material.is_select), icon_only=True)

        row = layout.split(factor=0.08)
        row.label(text=str(index), translate=False)

        row = row.row(align=True)
        if slot.link == 'OBJECT' and slot.material is not None:
            # row.label(text=slot.material.name, translate=False, icon_value=get_data_icon(slot.material))
            row.prop(slot.material, 'name', text='', emboss=False, translate=False, icon_value=get_data_icon_value(slot.material))
        else:
            row.label(text=' ', icon='X')

        data_mat = obj.data.materials[slot_idx]
        if data_mat is not None:
            # row.label(text=data_mat.name, translate=False, icon_value=get_data_icon(data_mat))
            row.prop(data_mat, 'name', text='', emboss=False, translate=False, icon_value=get_data_icon_value(data_mat))
        else:
            row.label(text=' ', icon='X')
        
        icon_link = 'MESH_DATA' if slot.link == 'DATA' else 'OBJECT_DATA'
        row.prop(slot, "link", icon=icon_link, icon_only=True)


class MMD_MaterialLibrary_Prop(PropertyGroup):
    mat_lib_active:    IntProperty()
    mat_lib_list:      CollectionProperty(type=MMD_ML_MaterialLibrary_UL_Item_State)

    # -------------------------------------------------------------------------------------


class MMD_MaterialLibrary_Panel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_material_library_panel'
    bl_label = 'Material Library'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MMD'
    bl_context = ''
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop

        layout = self.layout
        grid = layout.column(align=True)

        # -----------------------------------------------------------------------------------------
        mmd_root_obj = model.FnModel.find_root(bpy.context.active_object)
        mat_lib_root_obj = get_mat_lib_root()

        if mmd_root_obj is None:
            grid.label(text='Please select a mmd object')
            return
        elif 'mmd_tools_is_morph_bind' in mmd_root_obj and mmd_root_obj['mmd_tools_is_morph_bind']:
            grid.label(text='Please unbind morph.')
            grid.label(text='MaterialLibrary cannot work when morph was bind.')
            return

        if mat_lib_root_obj is None:
            grid.operator(OT_CreateMmdMaterialLibraryRoot.bl_idname)
            return
        
        grid.label(text='Material Library List', icon='PRESET')

        # Check if the material library list needs to be updated.
        _A = tuple(get_ul_mat_lib_list())
        _B = tuple(get_current_mat_lib_list())
        if _A != _B:
            col = grid.column(align=True)
            col.label(text='Outdated! Please refresh the material lib list.', icon='INFO')
            col.operator(OT_MaterialLibraryListRefresh.bl_idname, text='Refresh', icon='FILE_REFRESH')
            return
        #

        row = grid.row(align=True).split(factor=0.8)
        row.template_list('MMD_ML_MaterialLibrary_UL_Item', '', prop, 'mat_lib_list', prop, 'mat_lib_active', rows=4)

        col = row.column(align=True)
        col.operator(OT_MaterialLibraryListRefresh.bl_idname, text='Refresh', icon='FILE_REFRESH')
        col.separator()
        col.operator(OT_MaterialLibraryListSelect.bl_idname, text='Select All', icon='SELECT_EXTEND').select_type = 'SELECT_ALL'
        col.operator(OT_MaterialLibraryListSelect.bl_idname, text='Deselect All', icon='SELECT_SET').select_type = 'DESELECT_ALL'
        col.operator(OT_MaterialLibraryListSelect.bl_idname, text='Select Invert', icon='SELECT_SUBTRACT').select_type = 'SELECT_INVERT'

        # -----------------------------------------------------------------------------------------
        grid.separator()
        row = grid.row(align=True)
        row.operator(OT_NewMaterialLibrary.bl_idname, text='New', icon='ADD')
        row.operator(OT_RemoveMaterialLibrary.bl_idname, text='Remove', icon='REMOVE')
        row = grid.row(align=True)
        row.operator(OT_ApplyMaterialLibrary.bl_idname, text='Apply', icon='RADIOBUT_ON')
        row.operator(OT_CancelMaterialLibrary.bl_idname, text='Cancel', icon='RADIOBUT_OFF')
        
        grid.separator()
        row = grid.row(align=True)
        row.operator(OT_SyncMaterialLibrary.bl_idname, text='Sync', icon='UV_SYNC_SELECT')
        row.operator(OT_SaveMaterialLibrary.bl_idname, text='Save', icon='FILE_TICK')

        # -----------------------------------------------------------------------------------------

        grid.separator()

        active_mat_lib = get_active_mat_lib(prop)
        if active_mat_lib is None:
            grid.label(text='Please select a mmd lib')
            return

        grid.label(text=active_mat_lib.name, icon='MATERIAL')

        row = grid.row(align=True).split(factor=0.8)
        row.template_list('MMD_ML_MaterialSlot_UL_Item', '', active_mat_lib, 'material_slots', active_mat_lib, 'active_material_index', rows=4)

        col = row.column(align=True)
        col.operator(OT_MaterialSlotSelect.bl_idname, text='Select All', icon='SELECT_EXTEND').select_type = 'SELECT_ALL'
        col.operator(OT_MaterialSlotSelect.bl_idname, text='Deselect All', icon='SELECT_SET').select_type = 'DESELECT_ALL'
        col.operator(OT_MaterialSlotSelect.bl_idname, text='Select Invert', icon='SELECT_SUBTRACT').select_type = 'SELECT_INVERT'

        grid.separator()
        row = grid.row(align=True)
        row.operator(OT_SyncMaterialSlot.bl_idname, text='Sync', icon='UV_SYNC_SELECT')
        row.operator(OT_ResetAllLinkMaterialSlot.bl_idname, text='Reset All Link', icon='DECORATE_OVERRIDE')

        return

        # -----------------------------------------------------------------------------------------


def get_current_mat_lib_list():
    current_mat_lib_list = []
    for obj in get_all_mat_lib():
        current_mat_lib_list.append(obj.name)
    return current_mat_lib_list


def get_ul_mat_lib_list():
    scene = bpy.context.scene
    prop = scene.mmd_material_library_prop
    mat_lib_list = []
    for item in prop.mat_lib_list:
        mat_lib_list.append(item.mat_lib_name)
    return mat_lib_list


class OT_CreateMmdMaterialLibraryRoot(Operator):
    bl_idname = 'mmd_tools.create_mmd_material_library_root'
    bl_label = 'Create mmd material library root'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        create_mat_lib_root()
        return {'FINISHED'}


class OT_MaterialLibraryListRefresh(Operator):
    bl_idname = 'mmd_tools.material_library_list_refresh'
    bl_label = 'Material library list refresh'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop
        
        new_mat_lib_list = get_current_mat_lib_list()
                    
        while len(prop.mat_lib_list) < len(new_mat_lib_list):
            prop.mat_lib_list.add()

        need_del_ids = []
        for i, item in enumerate(prop.mat_lib_list):
            if i < len(new_mat_lib_list):
                if item.mat_lib_name != new_mat_lib_list[i]:
                    item.mat_lib_name = new_mat_lib_list[i]
                    item.is_select = False
            else:
                need_del_ids.append(i)
        need_del_ids = sorted(need_del_ids, reverse=True)
        for i in need_del_ids:
            prop.mat_lib_list.remove(i)

        return {'FINISHED'}


class OT_MaterialLibraryListSelect(Operator):
    bl_idname = 'mmd_tools.material_library_list_select'
    bl_label = 'Material library list select'
    bl_options = {'REGISTER', 'UNDO'}

    select_type:   EnumProperty(
        default='SELECT_ALL', description='Select type',
        items=[('SELECT_ALL', 'SELECT_ALL', ''), ('DESELECT_ALL', 'DESELECT_ALL', ''), ('SELECT_INVERT', 'SELECT_INVERT', '')]
    )

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop
        for item in prop.mat_lib_list:
            if self.select_type == 'SELECT_ALL':
                item.is_select = True
            elif self.select_type == 'DESELECT_ALL':
                item.is_select = False
            elif self.select_type == 'SELECT_INVERT':
                item.is_select = not item.is_select
        return {'FINISHED'}


class OT_NewMaterialLibrary(Operator):
    bl_idname = 'mmd_tools.new_material_library'
    bl_label = 'New material library'
    bl_options = {'REGISTER', 'UNDO'}

    mat_lib_name: StringProperty(default='preset')

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop
        new_mat_lib(self.mat_lib_name)
        bpy.ops.mmd_tools.material_library_list_refresh()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OT_RemoveMaterialLibrary(Operator):
    bl_idname = 'mmd_tools.remove_material_library'
    bl_label = 'Remove material library'
    bl_options = {'REGISTER', 'UNDO'}

    only_active: BoolProperty(default=True)

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop
        remove_mat_lib(prop, only_active=self.only_active)
        bpy.ops.mmd_tools.material_library_list_refresh()
        return {'FINISHED'}


class OT_ApplyMaterialLibrary(Operator):
    bl_idname = 'mmd_tools.apply_material_library'
    bl_label = 'Apply material library'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prop = context.scene.mmd_material_library_prop
        apply_mat_lib(prop)
        return {'FINISHED'}


class OT_CancelMaterialLibrary(Operator):
    bl_idname = 'mmd_tools.cancel_material_library'
    bl_label = 'Cancel material library'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cancel_mat_lib()
        return {'FINISHED'}


class OT_SyncMaterialLibrary(Operator):
    bl_idname = 'mmd_tools.sync_material_library'
    bl_label = 'Sync material library'
    bl_options = {'REGISTER', 'UNDO'}

    only_select: BoolProperty(default=False)

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop
        sync_mat_lib(prop, self.only_select)
        return {'FINISHED'}


class OT_SaveMaterialLibrary(Operator):
    bl_idname = 'mmd_tools.save_material_library'
    bl_label = 'Save material library'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prop = context.scene.mmd_material_library_prop
        save_mat_lib(prop)
        return {'FINISHED'}


# -----------------------------------------------------------------------------------------


class OT_MaterialSlotSelect(Operator):
    bl_idname = 'mmd_tools.material_slot_select'
    bl_label = 'Material slot select'
    bl_options = {'REGISTER', 'UNDO'}

    select_type:   EnumProperty(
        default='SELECT_ALL', description='Select type',
        items=[('SELECT_ALL', 'SELECT_ALL', ''), ('DESELECT_ALL', 'DESELECT_ALL', ''), ('SELECT_INVERT', 'SELECT_INVERT', '')]
    )

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop
        mat_lib_obj: bpy.types.Object = get_active_mat_lib(prop)

        if mat_lib_obj is None:
            return {'FINISHED'}

        for slot in mat_lib_obj.material_slots:
            if slot.material is None:
                continue

            if self.select_type == 'SELECT_ALL':
                slot.material.mmd_material.is_select = True
            elif self.select_type == 'DESELECT_ALL':
                slot.material.mmd_material.is_select = False
            elif self.select_type == 'SELECT_INVERT':
                slot.material.mmd_material.is_select = not slot.material.mmd_material.is_select

        return {'FINISHED'}


class OT_SyncMaterialSlot(Operator):
    bl_idname = 'mmd_tools.sync_material_slot'
    bl_label = 'Sync material slot'
    bl_options = {'REGISTER', 'UNDO'}

    only_select: BoolProperty(default=False)

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop
        self.report({'ERROR'}, 'Not implemented yet.')
        return {'CANCELLED'}


class OT_ResetAllLinkMaterialSlot(Operator):
    bl_idname = 'mmd_tools.reset_all_link_material_slot'
    bl_label = 'Reset all link material slot'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_library_prop
        mat_lib = get_active_mat_lib(prop)
        if mat_lib is not None:
            for slot in mat_lib.material_slots:
                slot.link = 'OBJECT'
        
        return {'FINISHED'}



# -------------------------------------------------------------------------------


def register():
    Scene.mmd_material_library_prop = PointerProperty(type=MMD_MaterialLibrary_Prop, options={'SKIP_SAVE'})

def unregister():
    pass
