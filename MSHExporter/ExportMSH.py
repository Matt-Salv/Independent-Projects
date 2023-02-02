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
        self.name = name #Eternity Engine Mesh File 0.1
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

    def __init__(self):
        self.SceneName = bytearray(256) 
        self.MeshName = bytearray(256)
        self.NumVertices = 0
        self.NumIndices = 0
        self.Unknown = 0
        self.Bitflag = 0
        self.Padding = bytearray(496) #Including this line, and the preceding ones, this should = 1024 bytes.
        self.FaceIndices = None  # Size 2x[I] short[I]
        self.Vertices = None  # Size 4x[V] Float[V]
        self.Normals = None  # size 4x[V] Float[V]
        self.TextureCoords = None  # Size 4x[V] Float[V]
        self.Unknown3 = None  # Size 4x[V] Int[V]
        self.BoneIndices = None  # 2x4x[V] Short[4][V]
        self.BoneWeights = None  # 4x4x[V] Float[4][V]
        self.NumBoneNames = 0
        self.BoneNames = []  # size 256x[N] FLString[N].

class Attribute:
    def __init__(self, attachment_points):
        self.attributes = []
        self.header = HeaderClass()
        for i in range(attachment_points):
            attribute = Attribute(i)
            self.attributes.append(attribute)
    
    class Attribute:
        def __init__(self, index):
            self.attribute_type = None
            self.parent_name = bytearray(256)
            self.unknown0 = [0.0 for _ in range(15)]
            self.unknown1 = [0.0 for _ in range(4)]
            self.unknown2 = [0.0 for _ in range(7)]
            self.unknown3_matrices = [[[0.0 for _ in range(3)] for _ in range(3)] for _ in range(3)]
            
            if self.header.version >= 0.11:
                self.parent_name = bytearray(256)
                self.translation = [0.0, 0.0, 0.0]
            
            if self.header.version >= 0.12:
                self.transform_matrix = [[0.0 for _ in range(4)] for _ in range(4)]

class AttachmentPoint:
    def __init__(self):
        self.name = bytearray(256)
        self.translation = [0.0, 0.0, 0.0]
        self.parent_bone_name = bytearray(256)
        self.transform_matrix = [[0.0 for _ in range(4)] for _ in range(4)]
        
        if HeaderClass.version >= 0.12:
            self.translation = [0.0,0.0,0.0]
        if HeaderClass.version >= 0.13:
            self.parent_bone_name = bytearray(256)
            self.transform_matrix = [[0.0 for _ in range(4)] for _ in range(4)]

'''class Vec2F:
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
            self.w = vector.w'''