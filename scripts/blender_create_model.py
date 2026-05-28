"""
BT-Blacklight 程序化女性人体建模脚本
在 Blender 3.6+ 中运行：File > Scripting > 粘贴运行
"""
import bpy
import math

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# ===== 身体参数 (mm) =====
HEIGHT = 1680
BUST = 920
WAIST = 580
HIP = 940

# ===== 创建基础人体 =====
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 1.35))
head = bpy.context.object
head.name = "Head"

# 脖子
bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.15, location=(0, 0, 1.2))
neck = bpy.context.object
neck.name = "Neck"

# 胸部
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 1.05))
chest = bpy.context.object
chest.name = "Chest"
chest.scale = (1, 0.7, 0.9)

# 腰部
bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.3, location=(0, 0, 0.8))
waist = bpy.context.object
waist.name = "Waist"

# 臀部
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(0, 0, 0.55))
hip = bpy.context.object
hip.name = "Hip"
hip.scale = (1, 0.6, 0.8)

# 左腿
bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.5, location=(-0.07, 0, 0.2))
leg_l = bpy.context.object
leg_l.name = "Leg_L"

# 右腿
bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.5, location=(0.07, 0, 0.2))
leg_r = bpy.context.object
leg_r.name = "Leg_R"

# 左臂
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.55, location=(-0.25, 0, 0.9))
arm_l = bpy.context.object
arm_l.name = "Arm_L"
arm_l.rotation_euler = (0, 0, 0.3)

# 右臂
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.55, location=(0.25, 0, 0.9))
arm_r = bpy.context.object
arm_r.name = "Arm_R"
arm_r.rotation_euler = (0, 0, -0.3)

# ===== 材质 =====
mat = bpy.data.materials.new("Skin_Blacklight")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.973, 0.886, 0.827, 1)  # #F8E2D3
bsdf.inputs["Roughness"].default_value = 0.25
bsdf.inputs["Subsurface"].default_value = 0.8
bsdf.inputs["Emission"].default_value = (0.659, 0.333, 0.969, 1)  # #A855F7
bsdf.inputs["Emission Strength"].default_value = 0.2

# 应用到所有身体部件
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.data.materials.append(mat)

# ===== 添加骨架 =====
bpy.ops.object.armature_add(location=(0, 0, 0.8))
armature = bpy.context.object
armature.name = "Armature_Main"
bpy.ops.object.mode_set(mode='EDIT')

# 基础骨骼链
bones = [
    ("Hips", (0, 0, 0.7), None),
    ("Spine", (0, 0, 0.9), "Hips"),
    ("Chest", (0, 0, 1.05), "Spine"),
    ("Neck", (0, 0, 1.2), "Chest"),
    ("Head", (0, 0, 1.35), "Neck"),
]

for name, pos, parent in bones:
    bone = armature.data.edit_bones.new(name)
    bone.head = pos
    bone.tail = (pos[0], pos[1], pos[2] + 0.15)
    if parent:
        bone.parent = armature.data.edit_bones[parent]

bpy.ops.object.mode_set(mode='OBJECT')

print("✅ 模型创建完成！添加细节后导出VRM。")
print("   File > Export > VRM")
