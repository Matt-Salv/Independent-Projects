import bpy
import bpy_extras.io_utils
import struct
import os
import re
from . binary_reader import *
from bpy.props import (
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty,
    EnumProperty,
)

class HeaderClass:               #Msh Header 1024 bytes
    def __init__(self, name, version, meshCount, unknown1, unknown2, bbMin, bbMax, boneCount, Attributes, AttachmentPoints, empty):
        self.name = name  #Eternity Engine Mesh File 0.1
        self.version = version #version number (0.1 = version 10, 0.11 = 11, etc.)
        self.meshCount = meshCount #Number of meshes/entries [E]
        self.unknown1 = unknown1 #unsure the type, 4 bytes
        self.unknown2 = unknown2 #unsure the type, 4 bytes
        self.bbMin = bbMin #bounding box min/max tells the game engine the object's size, visibility, collision for performance optimization
        self.bbMax = bbMax #number of bones [B]
        self.boneCount = boneCount #number of bones [B]
        self.Attributes = Attributes #num attributes [At]
        self.AttachmentPoints = AttachmentPoints #number attachmentpoints [Ap]
        self.empty = empty #keep the 1024 bytes: bytearray(768-52)

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
    def __init__(self, Header):
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
        if Header.version >= 0.11:
            for i in range (Header.Attributes):
                attribute = Attribute()
                self.attributes.append(attribute) # 4xE int[E] attribute type
        for i in range(Header.Attributes):
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
        if HeaderClass.version >= 0.12:
            self.parent_name = bytearray(256)  # FLString parent name (if msh.Version >= 11)
            self.translation = [0.0,0.0,0.0]
            if HeaderClass.version >= .13:
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