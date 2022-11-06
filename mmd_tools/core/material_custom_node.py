# -*- coding: utf-8 -*-
import bpy


'''
Naming Recognition

A node_group or node_tree 's name start with "nya_node."

'''

'''
Define

Custon Node Input (Standard)
----------------------
mmd_shader_exist        :type=float
mmd_shader_output       :type=shader
mmd_shader_color        :type=color
mmd_shader_alpha        :type=float

mmd_base_tex_exist      :type=float
mmd_base_tex_uv         :type=vector
mmd_base_tex_color      :type=color
mmd_base_tex_alpha      :type=float

mmd_sphere_tex_exist    :type=float
mmd_sphere_tex_uv       :type=vector
mmd_sphere_tex_color    :type=color
mmd_sphere_tex_alpha    :type=float

mmd_toon_tex_exist      :type=float
mmd_toon_tex_uv         :type=vector
mmd_toon_tex_color      :type=color
mmd_toon_tex_alpha      :type=float

mmd_sub_tex_exist       (No support yet)
mmd_sub_tex_uv          :type=vector
mmd_sub_tex_color       (No support yet)
mmd_sub_tex_alpha       (No support yet)


Custon Node Output (Standard)
----------------------
shader_surface          :type=shader
shader_volume           :type=shader
shader_displacement     :type=vector


Custon Node Other Link (Option)
----------------------
(Auto find and link same sockets)

'''


class FnCustomNode:

    @staticmethod
    def get_all_custom_nodetree_names():
        names = []
        for ng in bpy.data.node_groups:
            if ng.name.startswith('nya_node.'):
                names.append(ng.name)
        return names

    @staticmethod
    def get_ul_custom_nodetree_names(prop):
        names = []
        for item in prop.custom_nodetree_list:
            names.append(item.name)
        return names
        
    @staticmethod
    def get_all_custom_node_names(node_tree: bpy.types.ShaderNodeTree):
        names = []
        for ng in node_tree.nodes:
            if ng.name.startswith('nya_node.'):
                names.append(ng.name)
        
        return names

    @staticmethod
    def find_node_by_name(node_tree: bpy.types.ShaderNodeTree, name):
        # search order
        # first try to find name
        # second try to find name.XXX
        n = None
        ns = []
        for node in node_tree.nodes:
            if node.name == name:
                n = node
            elif node.name.startswith(name):
                ns.append(node)
        if n is not None:
            return n
        if len(ns) > 0:
            return ns[0]
        return None

    @staticmethod
    def get_custom_node_in_out_dict(node_tree: bpy.types.ShaderNodeTree, ignore_nodes: list=None, use_other_link=False):
        exclude_nodes = []
        if ignore_nodes is not None:
            exclude_nodes.extend(ignore_nodes)
        
        mmd_tex_uv = FnCustomNode.find_node_by_name(node_tree, 'mmd_tex_uv')
        mmd_base_tex = FnCustomNode.find_node_by_name(node_tree, 'mmd_base_tex')
        mmd_sphere_tex = FnCustomNode.find_node_by_name(node_tree, 'mmd_sphere_tex')
        mmd_toon_tex = FnCustomNode.find_node_by_name(node_tree, 'mmd_toon_tex')
        mmd_shader = FnCustomNode.find_node_by_name(node_tree, 'mmd_shader')

        output_node = node_tree.get_output_node('ALL')

        # ----------------------
        exclude_nodes.extend([mmd_tex_uv, mmd_base_tex, mmd_toon_tex, mmd_sphere_tex, mmd_shader, output_node])

        other_nodes = []
        for n in node_tree.nodes:
            if n not in exclude_nodes:
                other_nodes.append(n)

        # ----------------------
        in_dict = {}
        if mmd_tex_uv is not None:
            in_dict['mmd_base_tex_uv'] = mmd_tex_uv.outputs['Base UV']
            in_dict['mmd_sphere_tex_uv'] = mmd_tex_uv.outputs['Sphere UV']
            in_dict['mmd_toon_tex_uv'] = mmd_tex_uv.outputs['Toon UV']
            in_dict['mmd_sub_tex_uv'] = mmd_tex_uv.outputs['SubTex UV']

        if mmd_base_tex is not None:
            in_dict['mmd_base_tex_color'] = mmd_base_tex.outputs['Color']
            in_dict['mmd_base_tex_alpha'] = mmd_base_tex.outputs['Alpha']

        if mmd_sphere_tex is not None:
            in_dict['mmd_sphere_tex_color'] = mmd_sphere_tex.outputs['Color']
            in_dict['mmd_sphere_tex_alpha'] = mmd_sphere_tex.outputs['Alpha']

        if mmd_toon_tex is not None:
            in_dict['mmd_toon_tex_color'] = mmd_toon_tex.outputs['Color']
            in_dict['mmd_toon_tex_alpha'] = mmd_toon_tex.outputs['Alpha']

        if mmd_shader is not None:
            in_dict['mmd_shader_color'] = mmd_shader.outputs['Color']
            in_dict['mmd_shader_alpha'] = mmd_shader.outputs['Alpha']
            in_dict['mmd_shader_output'] = mmd_shader.outputs['Shader']
        
        # ----------------------
        out_dict = {}
        if output_node is not None:
            out_dict['shader_surface'] = output_node.inputs['Surface']
            out_dict['shader_volume'] = output_node.inputs['Volume']
            out_dict['shader_displacement'] = output_node.inputs['Displacement']
        
        # ----------------------
        if use_other_link:
            # Only use first match.
            for node in other_nodes:
                for socket in node.outputs:
                    in_dict.setdefault(socket.name, socket)
                for socket in node.inputs:
                    out_dict.setdefault(socket.name, socket)

        return in_dict, out_dict

    @staticmethod
    def remove_socket_all_link(node_tree: bpy.types.ShaderNodeTree, wait_del_links: list):
        for link in wait_del_links:
            node_tree.links.remove(link)

    @staticmethod
    def reset_link_custom_node(node_tree: bpy.types.ShaderNodeTree, node:bpy.types.ShaderNodeGroup,
            use_other_link=False, ignore_linked_socket=False, remove_unpair_link=True
        ):
        # use_other_link. It will allow node link to non-mmd-node by same socket name.
        # ignore_linked_socket. Ignore socket when it has been linked.
        # remove_unpair_link. Remove socket all unmatch link.

        in_dict, out_dict = FnCustomNode.get_custom_node_in_out_dict(node_tree, [node], use_other_link)
        
        for socket in list(node.inputs) + list(node.outputs):
            if socket.is_linked and ignore_linked_socket:
                continue
            if socket.is_linked and socket.name not in in_dict and socket.name not in out_dict and remove_unpair_link:
                FnCustomNode.remove_socket_all_link(node_tree, socket.links)
                continue

            if socket.name in in_dict and socket.name in node.inputs:
                node_tree.links.new(in_dict[socket.name], socket)

            if socket.name in out_dict and socket.name in node.outputs:
                node_tree.links.new(socket, out_dict[socket.name])
        
        if 'mmd_shader_exist' in node.inputs and not node.inputs['mmd_shader_exist'].is_linked:
            node.inputs['mmd_shader_exist'].default_value = float('mmd_shader_color' in in_dict)
            
        if 'mmd_base_tex_exist' in node.inputs and not node.inputs['mmd_base_tex_exist'].is_linked:
            node.inputs['mmd_base_tex_exist'].default_value = float('mmd_base_tex_color' in in_dict)
            
        if 'mmd_sphere_tex_exist' in node.inputs and not node.inputs['mmd_sphere_tex_exist'].is_linked:
            node.inputs['mmd_sphere_tex_exist'].default_value = float('mmd_sphere_tex_color' in in_dict)
        
        if 'mmd_toon_tex_exist' in node.inputs and not node.inputs['mmd_toon_tex_exist'].is_linked:
            node.inputs['mmd_toon_tex_exist'].default_value = float('mmd_toon_tex_color' in in_dict)

    @staticmethod
    def new_loc_for_custom_node(node_tree):
        # 1. Under the MMDShaderDev node.
        # 2. Left the Output node
        # 3. (0, 0)

        new_location = None

        n_custom_node = 0
        for node in node_tree.nodes:
            if node.name.startswith('nya_node.'):
                n_custom_node += 1
        
        x_offset = n_custom_node * 180

        if new_location is None:
            node = FnCustomNode.find_node_by_name(node_tree, 'mmd_shader')
            if node is not None:
                new_location = (node.location[0] + node.width + 50 + x_offset, node.location[1] - 300)
        
        if new_location is None:
            node = node_tree.get_output_node('ALL')
            if node is not None:
                new_location = (node.location[0] - 200 + x_offset, node.location[1])

        if new_location is None:
            new_location = (0, 0)
        
        return new_location

    @staticmethod
    def add_custom_node(node_tree: bpy.types.ShaderNodeTree, node: bpy.types.ShaderNodeGroup, use_other_link=False):
        loc = FnCustomNode.new_loc_for_custom_node(node_tree)
        new_node = node_tree.nodes.new('ShaderNodeGroup')
        new_node.location = loc
        new_node.name = node.name
        new_node.node_tree = node
        FnCustomNode.reset_link_custom_node(node_tree, new_node, use_other_link, False, True)

    @staticmethod
    def remove_custom_node(node_tree: bpy.types.ShaderNodeTree, node: bpy.types.ShaderNodeGroup):
        node_tree.nodes.remove(node)


class MigrationFnCustomNode:
    @staticmethod
    def del_all_aux_prop():
        '''
        Some unimportant auxiliary prop are attached to the scene. Delete them to avoid later compatibility considerations.
        '''
        for scene in bpy.data.scenes:
            if 'mmd_material_custom_node_prop' in scene:
                del scene['mmd_material_custom_node_prop']
