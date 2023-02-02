import bpy
import bpy_extras.io_utils
from bpy.props import (
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty,
    EnumProperty,
)
from bpy_extras.io_utils import ExportHelper
import struct
import os
import re
import sys
from . binary_reader import *
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
class ExportMSH(bpy.types.Operator, ExportHelper):
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
    export_target: EnumProperty(name="Export Target",
                                description="What to export.",
                                items=(
                                    ('SCENE', "Scene", "Export the current active scene."),
                                    ('SELECTED', "Selected", "Export the currently selected objects and their parents."),
                                    ('SELECTED_WITH_CHILDREN', "Selected with Children", "Export the currently selected objects with their children and parents.")
                                ),
                                default='SCENE')
    def execute (self, context):
        if 'SELECTED' in self.export_target and len(bpy.context.selected_objects) == 0:
            raise Exception("{} was chosen, but you have not selected any objects. "
                            " Don't forget to unhide all the objects you wish to select!".format(self.export_target))  
        with open(self.filepath, 'rb') as f:
            header_data = f.read(1024)
            name, version, meshCount, unknown1, unknown2, bbMin_x, bbMin_y, bbMin_z, bbMax_x, bbMax_y, bbMax_z, boneCount, Attributes, AttachmentPoints, padding = struct.unpack("256s4i3f3fii4s716s", header_data)
            empty = padding + b"\0" * 716
            bbMin = (bbMin_x, bbMin_y, bbMin_z)
            bbMax = (bbMax_x, bbMax_y, bbMax_z)
            header = HeaderClass(name, version, meshCount, unknown1, unknown2, bbMin, bbMax, boneCount, Attributes, AttachmentPoints, empty)
            f.seek(1344)
            firstBoneData = BoneData()
            firstBoneData.boneName = f.read(256)
            firstBoneData.transformMatrix = f.read(64)
            firstBoneData.boneName = struct.unpack("256s", firstBoneData.boneName)[0].strip(b'\0')
            firstBoneData.transformMatrix = struct.unpack("16f", firstBoneData.transformMatrix)
            print("First Bone Name:", firstBoneData.boneName)
            print("First Bone T-Matrix:", firstBoneData.transformMatrix)
            
        
        file_name, file_ext = os.path.splitext(self.filepath)
        new_file_name = file_name + "_UPDATED" + file_ext
        meshCount = len(bpy.data.meshes)
        armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
        boneCount = sum(len(armature.data.bones) for armature in armatures)
        '''To access the number of attributes and attachment points, you will need to know what data structure stores this information in Blender, 
        and what the names of these variables are. You may need to consult Blender's API documentation or ask the developers of the file format you
         are trying to export to.
         COME BACK TO THIS LATER'''
        
        bone_data_list = []
        for armature in armatures:
            for bone in armature.data.bones:
                bone_data = BoneData()
                bone_data.boneName = bone.name.encode()[:256]
                bone_matrix = armature.matrix_world @ bone.matrix_local
                bone_data.transformMatrix = [list(row) for row in bone_matrix]
                bone_data_list.append(bone_data)


        with open(new_file_name, "wb") as outfile:    
            #Write MSH Header information to file
            outfile.write(struct.pack("256s4i3f3fii4s716s", header.name, header.version, header.meshCount, header.unknown1, header.unknown2, header.bbMin[0], header.bbMin[1], header.bbMin[2], header.bbMax[0], header.bbMax[1], header.bbMax[2], header.boneCount, header.Attributes, header.AttachmentPoints, header.empty))
            #Write bone name and transform matrix to file, working but incorrectly... need to figure out why values from OG file are different
            for armature in armatures:
                for bone in armature.data.bones:
                    bone_data = BoneData()
                    bone_data.boneName = bone.name.encode("utf-8").ljust(256, b'\0')
                    bone_data.transformMatrix = armature.matrix_world @ bone.matrix_local
                    bone_matrix = list(bone_data.transformMatrix)
                    bone_matrix[1][:3] = [-bone_matrix[1][0], -bone_matrix[1][1], -bone_matrix[1][2]]
                    bone_matrix[2][:3] = [-bone_matrix[2][0], -bone_matrix[2][1], -bone_matrix[2][2]]
                    bone_matrix[0][1], bone_matrix[1][0] = bone_matrix[1][0], bone_matrix[0][1]
                    bone_matrix[0][2], bone_matrix[2][0] = bone_matrix[2][0], bone_matrix[0][2]
                    bone_matrix[1][2], bone_matrix[2][1] = bone_matrix[2][1], bone_matrix[1][2]
                    bone_data.transformMatrix = bone_matrix
                    outfile.write(bone_data.boneName)
                    outfile.write(struct.pack("16f", *[x for y in bone_data.transformMatrix for x in y]))
                    print("Bone name:", bone.name)
                    print("Bone transform matrix:", bone_data.transformMatrix)

        
        print("Name:", name)
        print("Version:", version)
        print("Mesh count:", meshCount)
        print("Unknown1:", unknown1)
        print("Unknown2:", unknown2)
        print("Bounding box min:", bbMin)
        print("Bounding box max:", bbMax)
        print("Bone count:", boneCount)
        print("Attributes:", Attributes)
        print("Attachment points:", AttachmentPoints)
        print("Empty:", empty)
        print("Done")

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