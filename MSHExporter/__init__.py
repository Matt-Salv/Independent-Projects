import bpy
import bpy_extras.io_utils
import struct
import os
from bpy.props import (
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty,
    EnumProperty,
)

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

class Header:
    def __init__(self):
        self.name = bytearray(256) #Eternity Engine Mesh File 0.1
        self.version = 0
        self.meshCount = 0
        self.unknown1 = 0x1
        self.unknown2 = 0x0
        self.bbMax = [0.0, 0.0, 0.0]
        self.bbMin = [0.0, 0.0, 0.0]
        self.boneCount = 0
        self.unknown2 = 0x1 or 0x0
        self.otherCount = 0

class BoneData:
    def __init__(self):
        self.boneName = bytearray(256) #Bone name
        self.transformMatrix = [[0.0 for _ in range(4)] for _ in range(4)]

class MeshInfo:
    def __init__(self):
        self.sceneName = bytearray(256)
        self.meshName = bytearray(256)
        self.vertexCount = 0
        self.indexCount = 0
        self.unknown = 0
        self.renderMode = 0
        self.empty = bytearray(512 - 16)

class MeshDataPointer:
    def __init__(self, bone_data_list):
        self.pFaceIndex = None  # 0x2(unsigned short) * indexCount
        self.pVertexData = None  # 0x4(float) * 3 * vertexCount
        self.pNormalData = None  # 0x4(float) * 3 * vertexCount
        self.pUVData = None  # 0x4(float) * 2 * vertexCount
        self.pBoneIndex = None  # 0x2(unsigned short) * 4 vertexCount
        self.pBoneWeight = None  # 0x4(float) * 4 * vertexCount
        self.pBoneCount = None  # The number of Bone bound by Mesh
        self.pBoneName = None  # 0x100(char [256]) * boneCount
        self.bone_data_list = bone_data_list

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
        
        header = Header()
        header.name = b'Eternity Engine Mesh File 0.1'
        header.version = 1
        header.meshCount = len(bpy.context.selected_objects)
        header.unknown1 = 1
        header.unknown2 = 0
        header.bbMax = [0.0, 0.0, 0.0]
        header.bbMin = [0.0, 0.0, 0.0]
        header.boneCount = 0
        header.otherCount = 0
            
        meshes = []
        bone_data_list = []
        for armature in bpy.data.armatures:
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH':
                    mesh = obj.data
                    header.meshCount += 1
                    armature = obj.find_armature()
                    if armature is not None:
                        for bone in armature.data.bones:
                            bone_data = BoneData()
                            bone_data.boneName = bone.name
                            bone_data.transformMatrix = bone.matrix
                            bone_data_list.append(bone_data)
            header.boneCount = len(bone_data_list)
            for armature in obj.modifiers: #iterate over armatures linked to object
                        header.boneCount += len(bone_data_list)
                        if armature.type == 'ARMATURE':
                            armature_obj = armature.object #iterate over bones in armature
                            for bone in mesh.data.bones:
                                bone_data = BoneData()
                                bone_data.boneName = bone.name
                                bone_data.transformMatrix = bone.matrix
                                bone_data_list.append(bone_data)
            if obj.type == 'MESH':
                    for vertex in obj.data.vertices:
                        if vertex.select:
                            for coord_index, coord in enumerate(vertex.co):
                                if coord > header.bbMax[coord_index]:
                                    header.bbMax[coord_index] = coord
                                if coord < header.bbMin[coord_index]:
                                    header.bbMin[coord_index] = coord
                    meshes.append(obj)
        header.boneCount = len(bone_data_list)
        MeshDataPointer = MeshDataPointer(bone_data_list)
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