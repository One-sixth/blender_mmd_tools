# -*- coding: utf-8 -*-

import bpy
from mmd_tools.core.material_custom_node import FnCustomNode


def get_select_icon(is_select):
    if is_select:
        return 'RESTRICT_SELECT_OFF'
    else:
        return 'RESTRICT_SELECT_ON'


class MMDMaterialCustomNodePanel(bpy.types.Panel):
    bl_idname = 'MATERIAL_PT_mmd_tools_material_custom_node'
    bl_label = 'MMD Material Custom Node'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj.active_material and obj.mmd_type == 'NONE'

    def draw(self, context):
        material = context.active_object.active_material
        mmd_material = material.mmd_material
        prop = context.scene.mmd_material_custom_node_prop

        layout = self.layout

        col = layout.column(align=True)

        if not material.use_nodes:
            col.label(text='Error! Please enable material node features.')
            col.prop(material, 'use_nodes', icon='NODETREE')
            return

        col.label(text='Custom Node List', icon='PRESET')

        nodes = [n for n in material.node_tree.nodes if n.name.startswith('nya_node.')]
        # Because the node order is easily variable, use the name to fix the order.
        nodes = sorted(nodes, key=lambda a: a.name)

        for node in nodes:
            if not node.name.startswith('nya_node.'):
                continue

            col.separator()
            row = col.row(align=True)
            row.prop(node, 'select', text='', icon=get_select_icon(node.select))
            row.operator('mmd_tools.reset_link_material_custom_node', text='', icon='GRAPH').node_name = node.name
            row.label(text=node.name)
            row.operator('mmd_tools.remove_material_custom_node', text='', icon='X').node_name = node.name
            for inp in node.inputs:
                if not inp.is_linked:
                    row = col.row(align=True)
                    row = row.split(factor=0.4)
                    row.label(text=inp.name)
                    row.prop(inp, 'default_value', text='')
        
        col.separator(factor=1.5)
        col.label(text='Add Node', icon='ADD')
        
        all_nodetree_names = FnCustomNode.get_all_custom_nodetree_names()
        ul_nodetree_names = FnCustomNode.get_ul_custom_nodetree_names(prop)

        if all_nodetree_names != ul_nodetree_names:
            col.label(text='Please click <Refresh> Button.')
            col.operator('mmd_tools.refresh_custom_node_tree_list', text='<Refresh>')
        else:
            col.prop_search(prop, 'custom_nodetree_active', prop, 'custom_nodetree_list', text='', translate=False)
            col.operator('mmd_tools.add_material_custom_node')


# -------------------------------------------------------------------------------


class MMD_Material_CustomNode_UL_Item(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='')

class MMD_Material_CustomNode_Prop(bpy.types.PropertyGroup):
    custom_nodetree_active: bpy.props.StringProperty(default='')
    custom_nodetree_list:   bpy.props.CollectionProperty(type=MMD_Material_CustomNode_UL_Item)

def register():
    bpy.types.Scene.mmd_material_custom_node_prop = bpy.props.PointerProperty(type=MMD_Material_CustomNode_Prop, options={'SKIP_SAVE'})

def unregister():
    pass
