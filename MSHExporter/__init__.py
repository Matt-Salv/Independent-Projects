import bpy
import bpy_extras.io_utils
from bpy.props import (
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty,
    EnumProperty,
)
import struct
import os
import re
import sys
# Add the directory containing the ExportMSH.py file to sys.path
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(dir_path, 'MSHExporter'))

# Import the ExportMSH module
from .ExportMSH import *

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

#!!!!! IMPORTANT: RENAME THE BLEND FILE NAME TO MATCH THE DESIRED .MSH FILE NAME !!!!!!!
file_path = bpy.data.filepath
def readMSH(file_path):
    with open(file_path, "rb") as originalFile:
        version = read_int(originalFile, num=1)
        print(version)

class ExportMSH(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "export_msh.dragon_nest"
    bl_label = "Export Dragon Nest Model"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".msh"
    filter_glob: StringProperty(
        default="*.msh", 
        options={'HIDDEN'},
        maxlen=255, #max internal buffer
        )
    filepath: StringProperty(
        name="File Path",
        description="Filepath used for exporting the .msh file",
        maxlen=1024,
        default="",
    )
    # New property to specify a different output filepath and name
    output_filepath = StringProperty(
        pathName="Output File Path",
        description="File path to save the exported data",
        maxlen=1024,
        default="",
    )

    def execute (self, context):
        readMSH()

def menu_func_export(self, context):
    self.layout.operator(ExportMSH.bl_idname,
                        text="Dragon Nest Model (.msh)")

def register ():
        bpy.utils.register_class(ExportMSH)
        bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportMSH)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()