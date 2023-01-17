bl_info = {
    "name": "Dragon Nest MSH Exporter",
    "author": "Matt-Salv",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "File > Export > DN Mesh (.msh)",
    "description": "Export DN model (.msh)",
    "warning": "",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export",
}

import bpy
import bpy_extras.io_utils

class ExportMSH(bpy.types.Operator):
    bl_idname = "export_scene.dragon_nest"
    bl_label = "Export Dragon Nest Model"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".msh"
    filter_glob: StringProperty(default="*.msh", options={'HIDDEN'})

    def execute (self, context):
        from.import ExportMSH 
        #probably need to add more stuff here

def menu_func_export(self, context):
    self.layout.operator(ExportMSH.bl_idname,
                        text="Dragon Nest Model (.msh)")

def register ():
        bpy.utils.register_class(ExportMSH)

def unregister():
    bpy.utils.unregister_class(ExportMSH)

if __name__ == "__main__":
    register()