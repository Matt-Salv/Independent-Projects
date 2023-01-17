import bpy
import bpy_extras.io_utils
import struct

obj = bpy.context.active_object #grab the active object
#list(bpy.data.objects) can be used to list object attributes
#need to write name, vertex, index, normal, map name, coord, node, and weight
obj_name = obj.name
vertices = obj.data.vertices #access vertices
faces = obj.data.polygons #access faces
normals = obj.data.normals #access normals
uv_layers = obj.data.uv_layers #access UV coordinates
materials = obj.material_slots #access material information
weights = obj.data.shape_keys.key_blocks #access bone weights

with open(filepath, 'wb') as file:
    vertices_bytes = struct.pack('<i', vertices)
    faces_bytes = struct.pack('<i', faces)
    normals_bytes = struct.pack('<i', normals)
    uv_layers_bytes = struct.pack('<i', uv_layers)
    materials_bytes = struct.pack('<i', materials)
    weights_bytes = struct.pack('<i', weights)
    file.write(struct.pack('256s', vertices_bytes, faces_bytes, normals_bytes, uv_layers_bytes, materials_bytes,
                weights_bytes, obj_name.encode())) #continue here tomorrow, goodnight world

for obj in bpy.data.objects: #loop through exporting all objects in scene
    if obj.type == 'MESH':
        export_path = bpy.path.abspath("//") + obj.name + ".msh"
        bpy.ops.export_mesh.msh(filepath=export_path)