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
        file_name, file_ext = os.path.splitext(self.filepath)
        new_file_name = file_name + "_UPDATED" + file_ext
        
        with open(self.filepath, 'rb') as f:
            header_data = f.read(1024)
            name, version, meshCount, unknown1, unknown2, bbMin_x, bbMin_y, bbMin_z, bbMax_x, bbMax_y, bbMax_z, boneCount, Attributes, AttachmentPoints, padding = struct.unpack("256s4i3f3fii4s716s", header_data)
            empty = padding + b"\0" * 716
            bbMin = (bbMin_x, bbMin_y, bbMin_z)
            bbMax = (bbMax_x, bbMax_y, bbMax_z)
            header = HeaderClass(name, version, meshCount, unknown1, unknown2, bbMin, bbMax, boneCount, Attributes, AttachmentPoints, empty)
            #meshCount = len(bpy.data.meshes)
            armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
            #boneCount = sum(len(armature.data.bones) for armature in armatures)
            
            bone_data_list = []
            for i in range(boneCount):
                bone_data = f.read(256+16*4)
                bone_name, *transform_matrix = struct.unpack("256s" + 16 * "f", bone_data)  
                bone_data_dict = {
                    "bone_name": bone_name.strip().decode("utf-8"),
                    "transform_matrix": list(transform_matrix)
                }
                bone_data_list.append(bone_data_dict)

            meshEntries = []
            boneNames = []
            for i in range(meshCount):
                sceneName = f.read(256).strip(b'\0').decode("utf-8")
                meshName = f.read(256).strip(b'\0').decode("utf-8")
                numVertices, numIndices, unknownA, bitflag = struct.unpack("4i", f.read(16))
                padding = f.read(496) # padding
                faceIndices = struct.unpack("{}h".format(numIndices), f.read(numIndices * 2))
                vertices = struct.unpack("{}f".format(numVertices * 3), f.read(numVertices * 3 * 4))
                normals = struct.unpack("{}f".format(numVertices * 3), f.read(numVertices * 3 * 4))
                textureCoords = struct.unpack("{}f".format(numVertices * 2), f.read(numVertices * 2 * 4))
                unknown3 = struct.unpack("{}i".format(numVertices), f.read(numVertices * 4))
                boneIndices = struct.unpack("{}h".format(numVertices * 4), f.read(numVertices * 4 * 2))
                boneWeights = struct.unpack("{}f".format(numVertices * 4), f.read(numVertices * 4 * 4))
                numBoneNames, = struct.unpack("i", f.read(4))
                bone_names = []
                for j in range(numBoneNames):
                    boneName = f.read(256).strip(b'\0').decode("utf-8")
                    bone_names.append(boneName)

            for j in range(numBoneNames):
                boneName = f.read(256)
                boneNames.append(struct.unpack("256s", boneName)[0].strip(b'\0').decode("utf-8"))

                meshEntry = MeshEntry(
                    sceneName,
                    meshName,
                    numVertices,
                    numIndices,
                    unknownA,
                    bitflag,
                    padding,
                    faceIndices,
                    vertices,
                    normals,
                    textureCoords,
                    unknown3,
                    boneIndices,
                    boneWeights,
                    numBoneNames,
                    bone_names
                )
                meshEntries.append(meshEntry)

        with open(new_file_name, "wb") as outfile:    
            #Write MSH Header information to file
            outfile.write(struct.pack("256s4i3f3fii4s716s", header.name, header.version, header.meshCount, header.unknown1, header.unknown2, header.bbMin[0], header.bbMin[1], header.bbMin[2], header.bbMax[0], header.bbMax[1], header.bbMax[2], header.boneCount, header.Attributes, header.AttachmentPoints, header.empty))
            for armature in armatures:
                for bone_data in bone_data_list:
                    if armature.data.bones.get(bone_data["bone_name"]) is not None:
                         # Write the bone information if the bone exists in the armature's edit bones
                        outfile.write(struct.pack("256s" + 16 * "f", bone_data["bone_name"].encode("utf-8"), *bone_data["transform_matrix"]))
                        print("Bone name:", bone_data["bone_name"])
                        print("Transform matrix:", bone_data["transform_matrix"])
            for meshEntry in meshEntries:
                outfile.write(struct.pack("256s", meshEntry.SceneName.encode("utf-8")))
                outfile.write(struct.pack("256s", meshEntry.MeshName.encode("utf-8")))
                outfile.write(struct.pack("4i", meshEntry.NumVertices, meshEntry.NumIndices, meshEntry.UnknownA, meshEntry.Bitflag))
                outfile.write(meshEntry.Padding)
                outfile.write(struct.pack("{}h".format(meshEntry.NumIndices), *meshEntry.FaceIndices))
                outfile.write(struct.pack("{}f".format(meshEntry.NumVertices * 3), *meshEntry.Vertices))
                outfile.write(struct.pack("{}f".format(meshEntry.NumVertices * 3), *meshEntry.Normals))
                outfile.write(struct.pack("{}f".format(meshEntry.NumVertices * 2), *meshEntry.TextureCoords))
                outfile.write(struct.pack("{}i".format(meshEntry.NumVertices), *meshEntry.Unknown3))
                outfile.write(struct.pack("{}h".format(meshEntry.NumVertices * 4), *meshEntry.BoneIndices))
                outfile.write(struct.pack("{}f".format(meshEntry.NumVertices * 4), *meshEntry.BoneWeights))
                outfile.write(struct.pack("i", meshEntry.NumBoneNames))
                for boneName in meshEntry.NumBoneNames:
                    outfile.write(struct.pack("256s", boneName.encode("utf-8")))

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
        for meshEntry in meshEntries:
            print("Scene Name:", sceneName)
            print("Mesh Name:", meshName)
            print("Num Vertices:", numVertices)
            print("Num Indices:", numIndices)
            print("UnknownA", unknownA)
            print("Bitflag:", bitflag)
            print("Padding:", padding)
            print("Face Indices:", faceIndices)
            print("Vertices:", vertices)
            print("Normals:", normals)
            print("Texture Coords:", textureCoords)
            print("Unknown 3:", unknown3)
            print("Bone Indices:", boneIndices)
            print("Bone Weights:", boneWeights)
            print("Num Bone Names:", numBoneNames)
            print("Bone Names:", boneNames)
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