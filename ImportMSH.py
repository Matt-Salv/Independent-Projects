import bpy

obj = bpy.context.active_object #grab the active object

vertices = obj.data.vertices #access vertices
faces = obj.data.polygons #access faces
normals = obj.data.normals #access normals
uv_layers = obj.data.uv_layers #access UV coordinates
materials = obj.material_slots #access material information
obj.data.shape_keys.key_blocks #access bone weights

obj = bpy.path.abspath("//") + obj.name + ".msh" #set path for export

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        export_path = path + obj.name + ".msh"
        bpy.ops.export_mesh.msh(filepath=export_path)

print("Done.")