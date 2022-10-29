import bpy

from mmd_tools.core import model
from mmd_tools.bpyutils import SceneOp, activate_layer_collection


# ----------------------------------------------------------------------------


def get_mmd_root():
    active_obj: bpy.types.Object = bpy.context.active_object
    mmd_root_obj = model.Model.findRoot(active_obj)
    return mmd_root_obj


def get_active_collect(obj):
    with activate_layer_collection(obj) as layer_collect:
        return layer_collect.collection


def create_empty_obj(name='empty',
        display_type='PLAIN_AXES',
        display_size=1,
        parent=None,
        collect=None):

    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = display_type
    obj.empty_display_size = display_size
    if collect is not None:
        collect.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def create_empty_mesh_obj(name='mesh', parent=None, collect=None):
    data = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, data)
    if collect is not None:
        collect.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


# ----------------------------------------------------------------------------


def get_mat_lib_root():
    mmd_root_obj = get_mmd_root()
    if mmd_root_obj is None:
        return None
    
    for child in mmd_root_obj.children:
        if child.name.startswith('mat_lib_root') and child.type == 'EMPTY':
            return child
    return None


def create_mat_lib_root():
    mmd_root_obj = get_mmd_root()
    if mmd_root_obj is None:
        return None

    mat_lib_root_obj = get_mat_lib_root()
    if mat_lib_root_obj is not None:
        return mat_lib_root_obj
    
    with activate_layer_collection(mmd_root_obj) as layer_collect:
        obj = create_empty_obj('mat_lib_root', display_size=0.25, parent=mmd_root_obj, collect=layer_collect.collection)
    obj.lock_location = obj.lock_rotation = obj.lock_scale = (True,True,True)
    obj.lock_rotation_w = True
    return obj


def unique_mesh_data_mat(mesh_obj):
    seen_mat = set()
    for mat_i, mat in enumerate(mesh_obj.data.materials):
        if mat is None:
            mesh_obj.data.materials[mat_i] = bpy.data.materials.new('Material')
        elif mat in seen_mat:
            mesh_obj.data.materials[mat_i] = mat.copy()
        else:
            seen_mat.add(mat)


def get_all_mat_lib():
    mat_lib_root_obj = get_mat_lib_root()
    if mat_lib_root_obj is None:
        return
    
    mat_lib_obj_list = []
    for obj in mat_lib_root_obj.children_recursive:
        if obj.type == 'MESH':
            mat_lib_obj_list.append(obj)

    return mat_lib_obj_list


def get_active_mat_lib(prop):
    mat_lib_obj: bpy.types.Object = None
    mat_lib_idx = prop.mat_lib_active
    if mat_lib_idx < len(prop.mat_lib_list):
        name = prop.mat_lib_list[mat_lib_idx].mat_lib_name
        if name in bpy.data.objects:
            mat_lib_obj = bpy.data.objects[name]
    return mat_lib_obj


def get_select_mat_lib(prop):
    select_mat_lib_list = []
    for item in prop.mat_lib_list:
        if item.is_select and item.mat_lib_name in bpy.data.objects:
            select_mat_lib_list.append(bpy.data.objects[item.mat_lib_name])
    return select_mat_lib_list


def get_mat_map_data_to_obj(obj: bpy.types.Object, keep_ori_link):
    mat_map = {}
    for slot_i, slot in enumerate(obj.material_slots):
        if obj.data.materials[slot_i] is None:
            continue
        ori_link = slot.link
        slot.link = 'OBJECT'
        # Only record first pair. The repeat pair will ignore.
        mat_map.setdefault(obj.data.materials[slot_i], slot.material)
        if keep_ori_link:
            slot.link = ori_link

    return mat_map


def ensure_number_mat_slots(obj, n_slot):
    while len(obj.data.materials) > n_slot:
        obj.data.materials.pop(index=-1)

    while len(obj.data.materials) < n_slot:
        obj.data.materials.append(None)

    assert len(obj.data.materials) == n_slot


# ----------------------------------------------------------------------------


def new_mat_lib(name='preset'):
    mat_lib_root_obj = get_mat_lib_root()
    if mat_lib_root_obj is None:
        return

    active_collect = get_active_collect(mat_lib_root_obj)
    mmd_lib = create_empty_mesh_obj(name, parent=mat_lib_root_obj, collect=active_collect)
    
    mmd_root_obj = get_mmd_root()

    mat_list = {}
    for mesh_obj in model.Model(mmd_root_obj).meshes():
        # # This step will make mesh_obj's slot have unique mat
        # unique_mesh_data_mat(mesh_obj)
        for mat in mesh_obj.data.materials:
            mat_list.setdefault(mat, None)
    mat_list = list(mat_list.keys())

    for m_i, m in enumerate(mat_list):
        mmd_lib.data.materials.append(m)
        mmd_lib.material_slots[m_i].link = 'OBJECT'
        m_ori_name = m.name
        m = m.copy()
        m.name = mmd_lib.name + '.' + m_ori_name
        mmd_lib.material_slots[m_i].material = m

    return mmd_lib


def remove_mat_lib(prop, only_active):
    if only_active:
        obj = get_active_mat_lib(prop)
        if obj is None:
            return
        mat_lib_list = [obj]
    else:
        mat_lib_list = get_select_mat_lib(prop)
    
    active_collect = get_active_collect(get_mat_lib_root())

    for obj in mat_lib_list:
        # Use auto delete. Not force delete.
        # When a mat_lib share in multi mmd model. (Rare case)
        # Or in multi collect.
        obj.parent = None
        active_collect.objects.unlink(obj)
        # bpy.data.objects.remove(obj)


def repair_mat_lib():
    pass


def apply_mat_lib(prop):
    mat_lib_obj = get_active_mat_lib(prop)

    if mat_lib_obj is None:
        # print('No1')
        return
    
    mat_map = {}
    for slot_i in range(len(mat_lib_obj.data.materials)):
        # print('No2')
        
        if mat_lib_obj.material_slots[slot_i].link != 'OBJECT':
            mat_lib_obj.material_slots[slot_i].link = 'OBJECT'
        mat_map[mat_lib_obj.data.materials[slot_i]] = mat_lib_obj.material_slots[slot_i].material

    # for k, v in mat_map.items():
    #     print(k.name, v.name)

    mmd_root_obj = get_mmd_root()
    for mesh in model.Model(mmd_root_obj).meshes():
        # print('No3')
        
        data_mats = mesh.data.materials
        for slot_i, slot in enumerate(mesh.material_slots):
            # print('No3-1', data_mats[slot_i].name)
            
            if data_mats[slot_i] is None:
                # print('No3-2')
                continue
            if data_mats[slot_i] in mat_map:
                # print('No3-3')
                slot.link = 'OBJECT'
                slot.material = mat_map[data_mats[slot_i]]

    # print('No4')


def cancel_mat_lib():
    mmd_root_obj = get_mmd_root()
    for mesh in model.Model(mmd_root_obj).meshes():
        for slot in mesh.material_slots:
            slot.link = 'OBJECT'
            slot.material = None
            slot.link = 'DATA'


def sync_mat_lib(prop, only_select):
    mmd_root_obj = get_mmd_root()
    if mmd_root_obj is None:
        return

    mat_lib_root_obj = get_mat_lib_root()
    if mat_lib_root_obj is None:
        return
    
    mesh_data_mats = {}
    for mesh in model.Model(mmd_root_obj).meshes():
        for mat in mesh.data.materials:
            mesh_data_mats.setdefault(mat, None)
    mesh_data_mats = list(mesh_data_mats.keys())
    
    if only_select:
        mat_lib_list = get_select_mat_lib(prop)
    else:
        mat_lib_list = get_all_mat_lib()

    for mat_lib in mat_lib_list:
        # get data_mat to obj_mat pair
        mat_map = get_mat_map_data_to_obj(mat_lib, keep_ori_link=False)
        
        # sync mat_lib slot num
        ensure_number_mat_slots(mat_lib, len(mesh_data_mats))

        # sync mat_lib order and content
        for slot_i, slot in enumerate(mat_lib.material_slots):
            slot.link = 'OBJECT'
            mat_lib.data.materials[slot_i] = mesh_data_mats[slot_i]
            if mesh_data_mats[slot_i] in mat_map:
                slot.material = mat_map[mesh_data_mats[slot_i]]
            else:
                slot.material = mesh_data_mats[slot_i].copy()
                slot.material.name = mesh_data_mats[slot_i].name + '.copy'

    return


def save_mat_lib(prop):
    mmd_root_obj = get_mmd_root()
    if mmd_root_obj is None:
        return

    mat_lib = get_active_mat_lib(prop)
    if mat_lib is None:
        return
    
    meshes_mat_map = {}
    for mesh in model.Model(mmd_root_obj).meshes():
        mat_map = get_mat_map_data_to_obj(mesh, keep_ori_link=True)
        for k in list(mat_map.keys()):
            if k in meshes_mat_map:
                # Remove not first match.
                mat_map.pop(k)
            elif mat_map[k] is None:
                # Make a copy when matched obj_mat is None.
                m = k.copy()
                m.name = k.name + '.copy'
                mat_map[k] = m
        meshes_mat_map.update(mat_map)
    
    ensure_number_mat_slots(mat_lib, len(meshes_mat_map))

    data_mats = list(meshes_mat_map.keys())
    obj_mats = list(meshes_mat_map.values())

    # sync mat_lib order and content
    for slot_i, slot in enumerate(mat_lib.material_slots):
        slot.link = 'OBJECT'
        mat_lib.data.materials[slot_i] = data_mats[slot_i]
        slot.material = obj_mats[slot_i]

    return