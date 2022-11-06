import bpy
from bpy.types import Operator
from mmd_tools.core.material_custom_node import FnCustomNode


class OT_RefreshCustomNodeTreeList(Operator):
    bl_idname = 'mmd_tools.refresh_custom_node_tree_list'
    bl_label = 'Refresh custom node tree list'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_custom_node_prop

        prop.custom_nodetree_list.clear()

        nodetree_names = FnCustomNode.get_all_custom_nodetree_names()
        for name in nodetree_names:
            item = prop.custom_nodetree_list.add()
            item.name = name
        
        if prop.custom_nodetree_active not in nodetree_names:
            prop.custom_nodetree_active = ''

        return {'FINISHED'}


class OT_AddCustomNode(Operator):
    bl_idname = 'mmd_tools.add_material_custom_node'
    bl_label = 'Add custom node'
    bl_options = {'REGISTER', 'UNDO'}

    use_other_link:         bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        scene = context.scene
        prop = scene.mmd_material_custom_node_prop

        nodetree_names = FnCustomNode.get_all_custom_nodetree_names()
        name = prop.custom_nodetree_active
        return name in nodetree_names

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_custom_node_prop

        nodetree_names = FnCustomNode.get_all_custom_nodetree_names()
        name = prop.custom_nodetree_active
        if name not in nodetree_names:
            self.report({'ERROR'}, 'Invalid custom node.')
            return {'CANCELLED'}
        
        mat = bpy.context.active_object.active_material
        FnCustomNode.add_custom_node(mat.node_tree, bpy.data.node_groups[name], use_other_link=self.use_other_link)
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OT_ResetLinkCustomNode(Operator):
    bl_idname = 'mmd_tools.reset_link_material_custom_node'
    bl_label = 'Reset link custom node'
    bl_options = {'REGISTER', 'UNDO'}

    node_name:              bpy.props.StringProperty(options={'HIDDEN'})
    use_other_link:         bpy.props.BoolProperty(default=True)
    ignore_linked_socket:   bpy.props.BoolProperty(default=False)
    remove_unpair_link:     bpy.props.BoolProperty(default=True)

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_custom_node_prop

        mat = bpy.context.active_object.active_material
        FnCustomNode.reset_link_custom_node(mat.node_tree, mat.node_tree.nodes[self.node_name],
            use_other_link=self.use_other_link,
            ignore_linked_socket=self.ignore_linked_socket,
            remove_unpair_link=self.remove_unpair_link
        )
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OT_RemoveCustomNode(Operator):
    bl_idname = 'mmd_tools.remove_material_custom_node'
    bl_label = 'Remove custom node'
    bl_options = {'REGISTER', 'UNDO'}

    node_name: bpy.props.StringProperty(default='', options={'HIDDEN'})

    def execute(self, context):
        scene = context.scene
        prop = scene.mmd_material_custom_node_prop

        mat = bpy.context.active_object.active_material
        FnCustomNode.remove_custom_node(mat.node_tree, mat.node_tree.nodes[self.node_name])
        
        return {'FINISHED'}