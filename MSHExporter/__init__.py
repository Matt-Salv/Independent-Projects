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
import struct
import os
import re
from bpy.props import (
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty,
    EnumProperty,
)

class Header:               #Msh Header 1024 bytes
    def __init__(self):
        self.name = bytearray(256) #Eternity Engine Mesh File 0.1
        self.version = 0
        self.meshCount = 0
        self.unknown1 = 0x1
        self.unknown2 = 0x0
        self.bbMin = [0.0, 0.0, 0.0]
        self.bbMax = [0.0, 0.0, 0.0]
        self.boneCount = 0 #number of bones
        self.Attributes = 0
        self.AttachmentPoints = 0
        self.empty = bytearray(768 - 52)

    def set_version(self):
        version_string = self.name[192:256:].decode("utf-8")
        version_match = re.search(r"(\d+\.\d+)", version_string)
        if version_match:
            self.version = float(version_match.group(1))

class BoneData:             #256 + 64 / bone
    def __init__(self):
        self.boneName = bytearray(256) #Bone name
        self.transformMatrix = [[0.0 for _ in range(4)] for _ in range(4)]

class MeshInfo:             #Mesh entry header 1024 bytes
    def __init__(self):
        self.sceneName = bytearray(256) 
        self.meshName = bytearray(256)
        self.vertexCount = 0
        self.indexCount = 0
        self.unknown = 0
        self.renderMode = 0
        self.empty = bytearray(512 - 16)

class MeshDataPointer:
    def __init__(self, header):
        self.pFaceIndex = None  # 0x2(unsigned short) * indexCount
        self.pVertexData = None  # 0x4(float) * 3 * vertexCount
        self.pNormalData = None  # 0x4(float) * 3 * vertexCount
        self.pUVData = None  # 0x4(float) * 2 * vertexCount
        self.pUnknown3 = None  # 4x[V] int[V] unknown3
        self.pBoneIndex = None  # 2x4x[V] Short[4][V] bone indices
        self.pBoneWeight = None  # 4x4x[V] Float[4][V] bone weights
        self.pBoneCount = None  # The number of Bone names[N] bound by Mesh
        self.pBoneName = None  # 256x[N] FLString[N] bone names
        self.attribute_type = None # 4 Int attribute type
        self.attribute_type_0 = None  # 4x15 Float[15] Unknown (if attribute type 0)
        self.attribute_type_1 = None  # 4x4 Float[4] Unknown (if attribute type 1)
        self.attribute_type_2 = None  # 4x7 Float[7] Unknown (if attribute type 2)
        self.attribute_type_3 = None  # 4x[3E]x9 Float[3x3][3E] Unknown 3x3 matrices (if attribute type 3)
        self.attributes = []
        self.attachment_points = []
        if header.version >= 0.11:
            for i in range (header.Attributes):
                attribute = Attribute()
                self.attributes.append(attribute) # 4xE int[E] attribute type
        for i in range(header.Attributes):
            attribute = Attribute()
            self.attributes.append(attribute)

class Attribute:
    def __init__(self):
        self.attribute_type = None
        if self.attribute_type is None:
            self.attribute_type = 0
            print(f"{self.name} type not set, default value of 0 used")
        self.parent_name = bytearray(256)
        self.translation = [0.0, 0.0, 0.0]
        self.unknown0 = [0.0 for _ in range(15)]
        self.unknown1 = [0.0 for _ in range(4)]
        self.unknown2 = [0.0 for _ in range(7)]
        self.unknown3_matrices = [[[0.0 for _ in range(3)] for _ in range(3)] for _ in range(3)]
        if Header.version >= 0.12:
            self.parent_name = bytearray(256)  # FLString parent name (if msh.Version >= 11)
            self.translation = [0.0,0.0,0.0]
            if Header.version >= .13:
                Attribute.transform_matrix = [[0.0 for _ in range(4)] for _ in range(4)]
                self.attributes.append(Attribute)

class AttachmentPoint:
    def __init__(self):
        self.name = bytearray(256) #FLString attachment name
        self.translation = [0.0, 0.0, 0.0] # 4x3 Float[3] Translation (if msh.Version >=12)
        self.parent_bone_name = bytearray(256) #FLString parent bone name (if msh.version >=13)
        self.transform_matrix = [[0.0 for _ in range(4)] for _ in range(4)] #4x4x4 Float[4x4] Transform matrix (if msh.Version >= 13)

class Vec2F:
    def __init__(self, vector = None):
        if vector is None:
            self.x = 0.0
            self.y = 0.0
        else:
            self.x = vector.x
            self.y = vector.y

class Vec3F(Vec2F):
    def __init__(self, vector = None):
        super().__init__(vector)
        if vector is None:
            self.z = 0.0
        else:
            self.z = vector.z

class Vec4F(Vec3F):
    def __init__(self, vector = None):
        super().__init__(vector)
        if vector is None:
            self.w = 0.0
        else:
            self.w = vector.w

class ExportMSH(bpy.types.Operator):
    bl_idname = "export_msh.dragon_nest"
    bl_label = "Export Dragon Nest Model"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".msh"
    filter_glob: StringProperty(default="*.msh", options={'HIDDEN'})

    def execute (self, context):
        if not bpy.context.selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}

        header = bpy.context.object.header
        header.set_version()
        header.name = bytearray(256)
        header.meshCount = len(bpy.context.selected_objects)
        header.unknown1 = 1
        header.unknown2 = 0
        header.bbMax = [0.0, 0.0, 0.0]
        header.bbMin = [0.0, 0.0, 0.0]
        header.boneCount = 0
        header.otherCount = 0
        if context.selected_objects:
            print("context.selected_objects is not empty")
        for obj in context.selected_objects:
            print(bpy.types.Object.header)
            print(dir(bpy.types.Object))
            print(dir(bpy.types))
            if not hasattr(bpy.types.Object, "header"):
                bpy.types.Object.header = bpy.props.PointerProperty(type=Header)
            if not hasattr(bpy.types.Object, "bone_data"):
                bpy.types.Object.bone_data = bpy.props.PointerProperty(type=BoneData)
            if not hasattr(bpy.types.Object, "mesh_info"):
                bpy.types.Object.mesh_info = bpy.props.PointerProperty(type=MeshInfo)
            if not hasattr(bpy.types.Object, "mesh_data_pointer"):
                bpy.types.Object.mesh_data_pointer = bpy.props.PointerProperty(type=MeshDataPointer)
        else:
            print("context.selected_objects is empty")
            
            if obj.type == 'MESH':
                print("Selected object is a mesh.")
                obj = bpy.context.object
                mesh = obj
                obj.header = Header()
                if obj.header.version > header.version:
                    header.version = obj.msh.version
            elif obj.type == 'ARMATURE':
                armature = obj
                print("Selected object is an armature.")
            # add additional checks for other object types here
            else:
                print("Selected object is of an unknown type.")
            
        meshes = []
        bone_data_list = [] 
        if armature:
            for bone in armature.data.edit_bones:
                bone_data = BoneData()
                bone_data.boneName = bone.name
                bone_data.transformMatrix = bone.matrix
                bone_data_list.append(bone_data)
        header.boneCount = len(bone_data_list)
        if mesh:
            for vertex in mesh.data.vertices:
                if vertex.select:
                    for coord_index, coord in enumerate(vertex.co):
                        if coord > header.bbMax[coord_index]:
                            header.bbMax[coord_index] = coord
                        if coord < header.bbMin[coord_index]:
                            header.bbMin[coord_index] = coord
            meshes.append(mesh)
        header.boneCount = len(bone_data_list)
        mesh_data_pointer = MeshDataPointer(bone_data_list)
        mesh_data_pointer.bone_data_list = bone_data_list
        mesh_info_list = []
        for mesh in meshes:
            mesh_info = MeshInfo()
            mesh_info.sceneName = mesh.name
            mesh_info.meshName = mesh.name
            mesh_info.vertexCount = len(mesh.data.vertices)
            mesh_info.indexCount = len(mesh.data.polygons)
            mesh_info.unknown = 0
            mesh_info.renderMode = 0
            mesh_info_list.append(mesh_info)
            mesh_data_pointer = MeshDataPointer()
            mesh_data_pointer.pFaceIndex = mesh.data.polygons.indices.tobytes()
            mesh_data_pointer.pVertexData = mesh.data.vertices.foreach_get("co").tobytes()
            mesh_data_pointer.pNormalData = mesh.data.vertices.foreach_get("normal").tobytes()
            mesh_data_pointer.pUVData = mesh.data.uv_layers.active.data.foreach_get("uv").tobytes()
            mesh_data_pointer.pBoneIndex = mesh.data.vertices.foreach_get("groups").tobytes()
            mesh_data_pointer.pBoneWeight = mesh.data.vertices.foreach_get("groups").tobytes()
            mesh_data_pointer.pBoneCount = len(mesh.data.bones)
            mesh_data_pointer.pBoneName = b''.join([bone.name.encode() + b'\x00' for bone in mesh.data.bones])
            mesh_data_pointer_list.append(mesh_data_pointer)
        mesh_data_pointer_list = []
        for mesh in meshes:
            mesh_data_pointer = MeshDataPointer()
            mesh_data_pointer.pFaceIndex = mesh.data.polygons.indices
            mesh_data_pointer.pVertexData = [vertex.co for vertex in mesh.data.vertices]
            mesh_data_pointer.pNormalData = [vertex.normal for vertex in mesh.data.vertices]
            mesh_data_pointer.pUVData = [vertex.uv for vertex in mesh.data.uv_layers.active.data]
            mesh_data_pointer.pBoneIndex = [vertex.groups for vertex in mesh.data.vertices]
            mesh_data_pointer.pBoneWeight = [vertex.groups for vertex in mesh.data.vertices]
            mesh_data_pointer.pBoneCount = len(mesh.data.bones)
            mesh_data_pointer.pBoneName = [bone.name for bone in mesh.data.bones]
            mesh_data_pointer_list.append(mesh_data_pointer)
        vec2f_list = []
        for vertex in mesh.data.vertices:
            vec2f = Vec2F(vertex.co)
            vec2f_list.append(vec2f)
        vec3f_list = []
        for vertex in mesh.data.vertices:
            vec3f = Vec3F(vertex.co)
            vec3f_list.append(vec3f)
        vec4f_list = []
        for vertex in mesh.data.vertices:
            vec4f = Vec4F(vertex.co)
            vec4f_list.append(vec4f)

        with open(self.filepath, 'wb') as f:
            f.write(header.name)
            f.write(struct.pack("i", header.version))
            f.write(struct.pack("i", header.meshCount))
            f.write(struct.pack("i", header.unknown1))
            f.write(struct.pack("i", header.unknown2))
            f.write(struct.pack("3f", *header.bbMax))
            f.write(struct.pack("3f", *header.bbMin))
            f.write(struct.pack("i", header.boneCount))
            f.write(struct.pack("i", header.otherCount))

            # Write bone data to the file
            for bone_data in bone_data_list:
                f.write(bone_data.boneName)
                for row in bone_data.transformMatrix:
                    f.write(struct.pack("4f", *row))

            # Write mesh info to the file
            for mesh_info in mesh_info_list:
                f.write(mesh_info.sceneName)
                f.write(mesh_info.meshName)
                f.write(struct.pack("i", mesh_info.vertexCount))
                f.write(struct.pack("i", mesh_info.indexCount))
                f.write(struct.pack("i", mesh_info.unknown))
                f.write(struct.pack("i", mesh_info.renderMode))
                f.write(mesh_info.empty)

            # Write mesh data pointer to the file
            for mesh_data_pointer in mesh_data_pointer_list:
                f.write(mesh_data_pointer.pFaceIndex)
                f.write(mesh_data_pointer.pVertexData)
                f.write(mesh_data_pointer.pNormalData)
                f.write(mesh_data_pointer.pUVData)
                f.write(mesh_data_pointer.pBoneIndex)
                f.write(mesh_data_pointer.pBoneWeight)
                f.write(struct.pack("i", mesh_data_pointer.pBoneCount))
                f.write(mesh_data_pointer.pBoneName)

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