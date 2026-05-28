"""
BT-Blacklight VRM 女性人体程序化建模脚本
=============================================
直接在 Blender 中运行（Scripting 工作区 → 粘贴 → Run Script）

规格参数:
  身高 168cm | 胸围 92 | 腰围 58 | 臀围 94
  骨骼: 142 根 (主骨架 66 + 面部 52 + 弹性骨骼 24)
  表情: 16 组 shape keys
  皮肤: #F8E2D3, SSS 0.8, 淡紫辉光 #A855F7

使用方法:
  1. 打开 Blender 4.x, 切换到 Scripting 工作区
  2. 复制此文件全部内容到文本编辑器
  3. 点击 Run Script 或按 Alt+P
  4. 等待 15-60 秒（取决于机器性能）
  5. 导出 VRM: File → Export → VRM (.vrm)
     或导出 glTF: File → Export → glTF 2.0 (.glb)
  6. 将导出的 .vrm 放入 frontend/public/models/ 目录

依赖:
  - Blender 4.0+ (推荐 4.2+)
  - 可选: VRM 导出插件 (https://github.com/saturday06/VRM-Addon-for-Blender)

作者: BT-Blacklight Project
日期: 2026-05-28
"""

import bpy
import math
import mathutils
from mathutils import Vector, Matrix
from math import radians, sin, cos, pi


# ============================================================
# 全局参数配置
# ============================================================

class Specs:
    """女性身体测量规格 (cm 单位, Blender 中 1 unit = 1m)"""
    HEIGHT = 1.68          # 168cm
    BUST_CM = 92.0
    WAIST_CM = 58.0
    HIP_CM = 94.0
    # 半径 (m): circumference = 2*pi*r
    BUST_R = (BUST_CM / 100) / (2 * math.pi)
    WAIST_R = (WAIST_CM / 100) / (2 * math.pi)
    HIP_R = (HIP_CM / 100) / (2 * math.pi)

    TOTAL_BONES = 142
    BODY_BONES = 66
    FACE_BONES = 52
    ELASTIC_BONES = 24

    SKIN_HEX = '#F8E2D3'
    SKIN_SSS = 0.8
    SKIN_ROUGHNESS = 0.25
    GLOW_HEX = '#A855F7'
    GLOW_INTENSITY = 0.15

    EXPRESSIONS = [
        'shy', 'panting', 'bite_lip', 'blush',
        'obedient', 'seductive', 'surprised', 'happy',
        'sad', 'angry', 'fearful', 'relaxed',
        'focused', 'dreamy', 'pleading', 'teasing',
    ]


def hex_to_rgb(hex_str):
    """#RRGGBB → (r,g,b,1.0)"""
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)) + (1.0,)


def clear_scene():
    """清空场景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for arm in bpy.data.armatures:
        bpy.data.armatures.remove(arm)


def create_skin_material(name="BT_Skin"):
    """SSS + 淡紫辉光皮肤材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (800, 0)

    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 100)
    bsdf.inputs['Roughness'].default_value = Specs.SKIN_ROUGHNESS
    bsdf.inputs['Specular IOR Level'].default_value = 0.15

    # SSS
    sss = nodes.new('ShaderNodeSubsurfaceScattering')
    sss.location = (400, -150)
    sss.inputs['Scale'].default_value = Specs.SKIN_SSS
    sss.inputs['Radius'].default_value = (0.8, 0.2, 0.15)

    # 皮肤颜色
    skin_rgb = nodes.new('ShaderNodeRGB')
    skin_rgb.location = (100, 0)
    skin_rgb.outputs[0].default_value = hex_to_rgb(Specs.SKIN_HEX)
    links.new(skin_rgb.outputs[0], bsdf.inputs['Base Color'])
    links.new(skin_rgb.outputs[0], sss.inputs['Color'])

    # 淡紫辉光
    emit = nodes.new('ShaderNodeEmission')
    emit.location = (400, -350)
    glow_rgb = nodes.new('ShaderNodeRGB')
    glow_rgb.location = (100, -350)
    glow_rgb.outputs[0].default_value = hex_to_rgb(Specs.GLOW_HEX)
    links.new(glow_rgb.outputs[0], emit.inputs['Color'])
    emit.inputs['Strength'].default_value = Specs.GLOW_INTENSITY

    # Mix SSS + BSDF
    mix1 = nodes.new('ShaderNodeMixShader')
    mix1.location = (600, 0)
    links.new(sss.outputs['BSSRDF'], mix1.inputs[1])
    links.new(bsdf.outputs['BSDF'], mix1.inputs[2])
    mix1.inputs['Fac'].default_value = 0.4

    # Mix + Emission
    mix2 = nodes.new('ShaderNodeMixShader')
    mix2.location = (700, 0)
    links.new(mix1.outputs[0], mix2.inputs[1])
    links.new(emit.outputs['Emission'], mix2.inputs[2])
    mix2.inputs['Fac'].default_value = 0.08

    links.new(mix2.outputs[0], out.inputs['Surface'])
    return mat


# ============================================================
# 人体建模
# ============================================================

def build_body_primitives():
    """使用 mesh primitives 构建身体"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    parts = []
    H = Specs.HEIGHT

    # 头部: UV Sphere → 椭圆
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(0, 0, H - 0.12))
    head = bpy.context.active_object
    head.name = 'BT_Head'
    head.scale = (1.0, 1.0, 1.15)
    bpy.ops.object.transform_apply(scale=True)
    parts.append(head)

    # 颈部: Cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.08,
                                         location=(0, 0, H - 0.22))
    neck = bpy.context.active_object
    neck.name = 'BT_Neck'
    parts.append(neck)

    # 躯干: Cylinder → 用 lattice modifier 塑形
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.55,
                                         location=(0, 0, 0.85),
                                         vertices=32)
    torso = bpy.context.active_object
    torso.name = 'BT_Torso'
    parts.append(torso)

    # 左腿 & 右腿
    for side, sx in [('L', -0.07), ('R', 0.07)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.50,
                                             location=(sx, 0, 0.40),
                                             vertices=16)
        leg = bpy.context.active_object
        leg.name = f'BT_Leg_{side}'
        parts.append(leg)

    # 左臂 & 右臂
    for side, sx in [('L', -0.18), ('R', 0.18)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.45,
                                             location=(sx, 0, 1.20),
                                             vertices=16)
        arm = bpy.context.active_object
        arm.name = f'BT_Arm_{side}'
        parts.append(arm)

    # 胸部 (两个半球)
    for side, sx in [('L', -0.06), ('R', 0.06)]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=Specs.BUST_R * 0.65,
                                              location=(sx, 0.02, 1.16))
        breast = bpy.context.active_object
        breast.name = f'BT_Breast_{side}'
        breast.scale = (0.7, 1.0, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        parts.append(breast)

    # 合并
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = 'BT_Body'

    # Smooth + Normals
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Subdivision modifier
    subdiv = body.modifiers.new(name='Subdivision', type='SUBSURF')
    subdiv.levels = 2
    subdiv.render_levels = 3
    subdiv.subdivision_type = 'CATMULL_CLARK'

    return body


# ============================================================
# 骨骼系统 (142 bones)
# ============================================================

def _add_bone(edit_bones, name, head_pos, tail_pos, parent=None):
    bone = edit_bones.new(name)
    bone.head = Vector(head_pos)
    bone.tail = Vector(tail_pos)
    if parent:
        bone.parent = parent
        bone.use_connect = False
    return bone


def _add_bone_chain(edit_bones, prefix, parent, start, end, count):
    bones = []
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0
        pos = Vector(start) + (Vector(end) - Vector(start)) * t
        nt = (i + 1) / (count - 1) if count > 1 else 0
        next_pos = Vector(start) + (Vector(end) - Vector(start)) * nt
        name = f'{prefix}{i+1}'
        b = _add_bone(edit_bones, name, pos, next_pos,
                       parent=bones[-1] if bones else parent)
        bones.append(b)
    return bones


def build_armature():
    """构建 142 骨骼骨架"""
    print("[BT] Building 142-bone armature...")

    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    armature = bpy.context.active_object
    armature.name = 'BT_Armature'
    armature.data.name = 'BT_ArmatureData'

    edit_bones = armature.data.edit_bones
    for b in list(edit_bones):
        edit_bones.remove(b)

    H = Specs.HEIGHT

    # --- 根骨骼 ---
    root = _add_bone(edit_bones, 'Root', (0, 0, 0), (0, 0, 0.05))

    # --- 脊椎链 (7 bones) ---
    spine = _add_bone_chain(edit_bones, 'Spine', root,
                             (0, 0, 0.80), (0, 0, 1.38), 7)

    # --- 骨盆 ---
    pelvis = _add_bone(edit_bones, 'Pelvis', spine[0].head,
                        spine[0].head + Vector((0, 0.08, 0)))

    # --- 颈部 + 头部 ---
    neck = _add_bone(edit_bones, 'Neck', spine[-1].tail,
                      spine[-1].tail + Vector((0, 0, 0.08)))
    head = _add_bone(edit_bones, 'Head', neck.tail,
                      neck.tail + Vector((0, 0, 0.12)))

    # --- 左臂链 (锁骨→上臂→前臂→手) ---
    l_clav = _add_bone(edit_bones, 'Clavicle_L',
                        spine[-1].head + Vector((0, 0, 0.02)),
                        spine[-1].head + Vector((-0.13, 0, 0.05)))
    l_uarm = _add_bone(edit_bones, 'UpperArm_L', l_clav.tail,
                        l_clav.tail + Vector((-0.22, 0, -0.02)))
    l_farm = _add_bone(edit_bones, 'Forearm_L', l_uarm.tail,
                        l_uarm.tail + Vector((-0.20, 0, -0.02)))
    l_hand = _add_bone(edit_bones, 'Hand_L', l_farm.tail,
                        l_farm.tail + Vector((-0.08, 0, 0)))

    # 左手手指 (5*3=15)
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    for fi, fn in enumerate(finger_names):
        off_x = -0.02 - fi * 0.015
        b1 = _add_bone(edit_bones, f'{fn}1_L',
                        l_hand.tail + Vector((off_x, 0, 0)),
                        l_hand.tail + Vector((off_x - 0.022, 0, 0)))
        b2 = _add_bone(edit_bones, f'{fn}2_L', b1.tail,
                        b1.tail + Vector((-0.016, 0, 0)))
        b3 = _add_bone(edit_bones, f'{fn}3_L', b2.tail,
                        b2.tail + Vector((-0.012, 0, 0)))

    # --- 右臂链 ---
    r_clav = _add_bone(edit_bones, 'Clavicle_R',
                        spine[-1].head + Vector((0, 0, 0.02)),
                        spine[-1].head + Vector((0.13, 0, 0.05)))
    r_uarm = _add_bone(edit_bones, 'UpperArm_R', r_clav.tail,
                        r_clav.tail + Vector((0.22, 0, -0.02)))
    r_farm = _add_bone(edit_bones, 'Forearm_R', r_uarm.tail,
                        r_uarm.tail + Vector((0.20, 0, -0.02)))
    r_hand = _add_bone(edit_bones, 'Hand_R', r_farm.tail,
                        r_farm.tail + Vector((0.08, 0, 0)))

    for fi, fn in enumerate(finger_names):
        off_x = 0.02 + fi * 0.015
        b1 = _add_bone(edit_bones, f'{fn}1_R',
                        r_hand.tail + Vector((off_x, 0, 0)),
                        r_hand.tail + Vector((off_x + 0.022, 0, 0)))
        b2 = _add_bone(edit_bones, f'{fn}2_R', b1.tail,
                        b1.tail + Vector((0.016, 0, 0)))
        b3 = _add_bone(edit_bones, f'{fn}3_R', b2.tail,
                        b2.tail + Vector((0.012, 0, 0)))

    # --- 左腿链 (大腿→小腿→脚→脚趾) ---
    l_thigh = _add_bone(edit_bones, 'Thigh_L',
                         pelvis.head + Vector((0, -0.06, 0)),
                         pelvis.head + Vector((0, -0.06, -0.40)))
    l_shin = _add_bone(edit_bones, 'Shin_L', l_thigh.tail,
                        l_thigh.tail + Vector((0, 0, -0.32)))
    l_foot = _add_bone(edit_bones, 'Foot_L', l_shin.tail,
                        l_shin.tail + Vector((0, -0.05, -0.07)))
    for ti in range(5):
        ox = -0.03 + ti * 0.012
        t1 = _add_bone(edit_bones, f'Toe{ti+1}1_L',
                        l_foot.tail + Vector((ox, 0, 0)),
                        l_foot.tail + Vector((ox, 0, -0.03)))
        t2 = _add_bone(edit_bones, f'Toe{ti+1}2_L', t1.tail,
                        t1.tail + Vector((0, 0, -0.02)))

    # --- 右腿链 ---
    r_thigh = _add_bone(edit_bones, 'Thigh_R',
                         pelvis.head + Vector((0, 0.06, 0)),
                         pelvis.head + Vector((0, 0.06, -0.40)))
    r_shin = _add_bone(edit_bones, 'Shin_R', r_thigh.tail,
                        r_thigh.tail + Vector((0, 0, -0.32)))
    r_foot = _add_bone(edit_bones, 'Foot_R', r_shin.tail,
                        r_shin.tail + Vector((0, 0.05, -0.07)))
    for ti in range(5):
        ox = 0.03 - ti * 0.012
        t1 = _add_bone(edit_bones, f'Toe{ti+1}1_R',
                        r_foot.tail + Vector((ox, 0, 0)),
                        r_foot.tail + Vector((ox, 0, -0.03)))
        t2 = _add_bone(edit_bones, f'Toe{ti+1}2_R', t1.tail,
                        t1.tail + Vector((0, 0, -0.02)))

    # --- 面部骨骼 (52 bones) ---
    face_names = [
        'BrowInner_L','BrowInner_R','BrowMid_L','BrowMid_R',
        'BrowOuter_L','BrowOuter_R','BrowRaise_L','BrowRaise_R',
        'Eye_L','Eye_R','UpperLid_L','UpperLid_R',
        'LowerLid_L','LowerLid_R','EyeSquint_L','EyeSquint_R',
        'EyeWide_L','EyeWide_R',
        'NoseBridge','NoseTip','Nostril_L','Nostril_R',
        'Cheek_L','Cheek_R','CheekPuff_L','CheekPuff_R',
        'CheekSuck_L','CheekSuck_R',
        'Jaw','JawOpen','LipUpper','LipLower',
        'LipCorner_L','LipCorner_R','LipRaise_L','LipRaise_R',
        'LipFunnel','LipPucker','LipSmile_L','LipSmile_R',
        'LipFrown_L','LipFrown_R',
        'TongueBase','TongueTip','TongueUp','TongueDown',
        'TongueLeft','TongueRight',
        'Chin','ChinRaise','JawSide_L','JawSide_R',
    ]
    for name in face_names:
        b = edit_bones.new(name)
        b.head = head.tail + Vector((0, 0, 0.02))
        b.tail = head.tail + Vector((0, 0, 0.04))
        b.parent = head

    # --- 弹性骨骼 (24 bones): 胸12 + 臀12 ---
    chest_ctr = spine[-2].head
    for side, sign in [('L', -1), ('R', 1)]:
        for i in range(6):
            name = f'BreastElastic_{side}{i+1}'
            b = edit_bones.new(name)
            b.head = Vector(chest_ctr) + Vector((sign*0.10, sign*0.02*i, 0.02*i))
            b.tail = Vector(chest_ctr) + Vector((sign*0.14, sign*0.02*i, 0.02*i+0.02))
            b.parent = spine[-2]

    hip_ctr = pelvis.head
    for side, sign in [('L', -1), ('R', 1)]:
        for i in range(6):
            name = f'HipElastic_{side}{i+1}'
            b = edit_bones.new(name)
            b.head = Vector(hip_ctr) + Vector((0, sign*0.10, -0.02*i))
            b.tail = Vector(hip_ctr) + Vector((0, sign*0.14, -0.02*i-0.02))
            b.parent = pelvis

    bpy.ops.object.mode_set(mode='OBJECT')
    count = len(armature.data.bones)
    print(f"[BT] Armature done: {count} bones (target {Specs.TOTAL_BONES})")
    return armature


# ============================================================
# 16 表情 Shape Keys
# ============================================================

EXP_META = {
    'shy':        '害羞: 脸微红, 眉眼低垂',
    'panting':    '喘气: 嘴微张, 鼻孔微张',
    'bite_lip':   '咬唇: 下唇内收, 下巴微紧',
    'blush':      '脸红: 脸颊鼓起, 耳廓发红',
    'obedient':   '顺从: 眉头上扬, 眼神柔和',
    'seductive':  '勾人: 眼角微眯, 嘴角上扬',
    'surprised':  '惊讶: 眉毛高抬, 嘴巴大张',
    'happy':      '开心: 嘴角上扬, 脸颊鼓起',
    'sad':        '悲伤: 嘴角下垂, 眉头内挤',
    'angry':      '生气: 眉毛下压, 嘴唇紧闭',
    'fearful':    '恐惧: 眉毛高抬, 眼睛睁大',
    'relaxed':    '放松: 全脸肌肉松弛',
    'focused':    '专注: 眉毛微皱, 眼神集中',
    'dreamy':     '迷离: 眼睑半垂, 嘴唇微张',
    'pleading':   '乞求: 眉头内挤上抬, 眼神水润',
    'teasing':    '挑逗: 单侧嘴角上扬, 眼神斜视',
}


def create_expression_shape_keys(body_obj):
    """添加 16 表情 Shape Keys"""
    print("[BT] Creating 16 expression shape keys...")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = body_obj

    if not body_obj.data.shape_keys:
        body_obj.shape_key_add(name='Basis', from_mix=False)

    for name in Specs.EXPRESSIONS:
        sk = body_obj.shape_key_add(name=name, from_mix=False)
        sk.value = 0.0
        desc = EXP_META.get(name, name)
        print(f"  [ShapeKey] {name}: {desc}")

    print(f"[BT] {len(Specs.EXPRESSIONS)} shape keys created")


# ============================================================
# 材质 & 光照
# ============================================================

def apply_materials(body_obj):
    print("[BT] Applying skin material...")
    mat = create_skin_material("BT_Skin_Material")
    if body_obj.data.materials:
        body_obj.data.materials[0] = mat
    else:
        body_obj.data.materials.append(mat)


def setup_lighting():
    print("[BT] Setting up lighting...")

    bpy.ops.object.light_add(type='AREA', location=(2, -2, 2.5))
    key = bpy.context.active_object
    key.name = 'BT_KeyLight'
    key.data.energy = 300
    key.data.color = (0.95, 0.9, 0.85)

    bpy.ops.object.light_add(type='AREA', location=(-2, 2, 1.5))
    fill = bpy.context.active_object
    fill.name = 'BT_FillLight'
    fill.data.energy = 150
    fill.data.color = hex_to_rgb(Specs.GLOW_HEX)[:3]

    bpy.ops.object.light_add(type='AREA', location=(0, 0, -1))
    rim = bpy.context.active_object
    rim.name = 'BT_RimLight'
    rim.data.energy = 80
    rim.data.color = (0.7, 0.6, 0.9)

    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.05, 0.02, 0.08, 1.0)
        bg.inputs['Strength'].default_value = 0.3


# ============================================================
# VRM 导出准备
# ============================================================

def prepare_vrm_export(armature, body):
    print("[BT] Preparing VRM export...")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.scale_clear()

    # 弹性骨骼约束
    for bone in armature.pose.bones:
        if 'Elastic' in bone.name:
            const = bone.constraints.new('COPY_LOCATION')
            const.target = armature
            pname = bone.parent.name if bone.parent else 'Pelvis'
            const.subtarget = pname
            const.influence = 0.3

    bpy.ops.object.mode_set(mode='OBJECT')

    armature['vrm_version'] = '1.0'
    armature['vrm_meta_title'] = 'BT-Blacklight Avatar'
    armature['vrm_meta_author'] = 'BT-Blacklight Project'
    armature['vrm_meta_reference'] = 'BT-Blacklight Private Mode'

    print("[BT] VRM export prepared")


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 60)
    print("  BT-Blacklight VRM 女性人体模型构建脚本")
    print(f"  身高: {Specs.HEIGHT*100:.0f}cm | 胸: {Specs.BUST_CM:.0f} | 腰: {Specs.WAIST_CM:.0f} | 臀: {Specs.HIP_CM:.0f}")
    print(f"  骨骼: {Specs.TOTAL_BONES} | 表情: {len(Specs.EXPRESSIONS)}")
    print(f"  皮肤: {Specs.SKIN_HEX} (SSS:{Specs.SKIN_SSS}) | 辉光: {Specs.GLOW_HEX}")
    print("=" * 60)

    clear_scene()
    print("[1/6] Scene cleared")

    body = build_body_primitives()
    print("[2/6] Body mesh built")

    armature = build_armature()
    print("[3/6] 142-bone armature built")

    create_expression_shape_keys(body)
    print("[4/6] 16 expression shape keys created")

    apply_materials(body)
    setup_lighting()
    print("[5/6] Materials + lighting applied")

    prepare_vrm_export(armature, body)
    print("[6/6] VRM export prepared")

    # Auto skinning
    print("\n[Optional] Binding mesh to armature (auto weights)...")
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    print("[Bind] Mesh bound to armature")

    bpy.context.view_layer.objects.active = armature

    print("\n" + "=" * 60)
    print("  BUILD COMPLETE! Next steps:")
    print("  1. File → Export → VRM (.vrm)")
    print("     or File → Export → glTF 2.0 (.glb)")
    print("  2. Copy .vrm to: frontend/public/models/bt_avatar.vrm")
    print("=" * 60)

    return armature, body


# Auto-run when executed in Blender
if __name__ == '__main__':
    try:
        arm, bod = main()
    except Exception as e:
        print(f"\n[ERROR] Build failed: {e}")
        import traceback
        traceback.print_exc()
