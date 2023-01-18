import bpy
import bpy_extras.io_utils
import struct
import os

obj = bpy.context.view_layer.objects.active #grab the active object
    #list(bpy.data.objects) can be used to list object attributes
    #need to write name, vertex, index, normal, map name, coord, node, and weight
export_path = bpy.filepath("//") + obj.name + ".msh"
obj_name = obj.name
vertices = obj.data.vertices #access vertices
faces = obj.data.polygons #access faces
normals = obj.data.normals #access normals
uv_layers = obj.data.uv_layers #access UV coordinates
materials = obj.material_slots #access material information
weights = obj.data.shape_keys.key_blocks #access bone weights

def ExportMSH():
    with open(export_path, 'wb') as file:
        vertices_bytes = struct.pack('<{}f'.format(len(vertices)* 3 ), *[v.co[i] for v in vertices for i in range(3)])
        faces_bytes = struct.pack('<{}i'.format(len(faces) * 3), *[f.vertices[i] for f in faces for i in range(3)])
        normals_bytes = struct.pack('<{}f'.format(len(normals) * 3), *[n[i] for n in normals for i in range(3)])
        uv_layers_bytes = struct.pack('<{}f'.format(len(uv_layers) * 2), *[uv[i] for uv in uv_layers for i in range(2)])
        materials_bytes = struct.pack('<{}i'.format(len(materials)), *[m.material.name for m in materials])
        weights_bytes = struct.pack('<{}f'.format(len(weights)), *[w.value for w in weights])
    file.write(vertices_bytes)
    file.write(faces_bytes)
    file.write(normals_bytes)
    file.write(uv_layers_bytes)
    file.write(materials_bytes)
    file.write(weights_bytes)
    file.write(obj_name.encode())

bpy.ops.export_scene.msh(filepath=export_path, use_selection=True)  