import bpy

bl_info = {
    "name": "Dragon Nest MSH Exporter",
    "author": "Matt-Salv",
    "Version": (1, 0),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Export DN model (.msh)",
    "warning": "",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export",

}

obj = bpy.context.active_object #grab the active object

vertices = obj.data.vertices #access vertices
faces = obj.data.polygons #access faces
normals = obj.data.normals #access normals
uv_layers = obj.data.uv_layers #access UV coordinates
materials = obj.material_slots #access material information
obj.data.shape_keys.key_blocks #access bone weights

for obj in bpy.data.objects: #loop through exporting all objects in scene
    if obj.type == 'MESH':
        export_path = bpy.path.abspath("//") + obj.name + ".msh"
        bpy.ops.export_mesh.msh(filepath=export_path)

print("Done.")