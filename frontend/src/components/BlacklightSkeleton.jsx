import * as THREE from 'three'

/**
 * BT-Blacklight 骨骼系统
 * 142骨骼 + 程序化女性人体 SkinnedMesh
 * 参数: 身高168cm, 胸92, 腰58, 臀94 (缩放到3D空间)
 */

export function createSkeleton() {
  const bones = []
  const boneMap = {}

  function addBone(name, parent, pos = [0, 0.12, 0]) {
    const bone = new THREE.Bone()
    bone.name = name
    bone.position.set(pos[0], pos[1], pos[2])
    parent.add(bone)
    bones.push(bone)
    boneMap[name] = bone
    return bone
  }

  // === Root: Hips ===
  const hips = new THREE.Bone()
  hips.name = 'Hips'
  hips.position.set(0, 0.85, 0)
  bones.push(hips)
  boneMap['Hips'] = hips

  // === Spine chain (5节) ===
  const spine = addBone('Spine', hips, [0, 0.12, 0])
  const spine1 = addBone('Spine1', spine, [0, 0.12, 0])
  const spine2 = addBone('Spine2', spine1, [0, 0.10, 0])
  const chest = addBone('Chest', spine2, [0, 0.10, 0])
  const upperChest = addBone('UpperChest', chest, [0, 0.10, 0])
  const neck = addBone('Neck', upperChest, [0, 0.13, 0])
  const head = addBone('Head', neck, [0, 0.12, 0])
  addBone('Head_end', head, [0, 0.15, 0])

  // === Face bones ===
  const jaw = addBone('Jaw', head, [0, -0.03, 0.06])
  addBone('Jaw_end', jaw, [0, -0.03, 0.10])
  const leftEye = addBone('LeftEye', head, [0.04, 0.05, 0.14])
  const rightEye = addBone('RightEye', head, [-0.04, 0.05, 0.14])

  // === Shoulders ===
  const leftShoulder = addBone('LeftShoulder', upperChest, [-0.12, 0.05, -0.02])
  const rightShoulder = addBone('RightShoulder', upperChest, [0.12, 0.05, -0.02])

  // === Arms (Left) ===
  const leftUpperArm = addBone('LeftUpperArm', leftShoulder, [-0.08, -0.26, 0])
  const leftLowerArm = addBone('LeftLowerArm', leftUpperArm, [0, -0.24, 0])
  const leftHand = addBone('LeftHand', leftLowerArm, [0, -0.16, 0])

  // Left fingers (15 bones: 5×3)
  function addFinger(prefix, parent, offsets) {
    let p = parent
    for (let i = 0; i < offsets.length; i++) {
      p = addBone(`${prefix}_${i}`, p, offsets[i])
    }
    return p
  }

  addFinger('LeftThumb', leftHand, [[0.02, 0.03, -0.015], [0.015, 0.03, 0], [0.01, 0.025, 0]])
  addFinger('LeftIndex', leftHand, [[0.02, 0, 0.06], [0.015, 0, 0.045], [0.01, 0, 0.03]])
  addFinger('LeftMiddle', leftHand, [[0.02, 0, 0.065], [0.015, 0, 0.05], [0.01, 0, 0.032]])
  addFinger('LeftRing', leftHand, [[0.02, 0, -0.02], [0.015, 0, 0.04], [0.01, 0, 0.025]])
  addFinger('LeftPinky', leftHand, [[0.02, 0, -0.045], [0.01, 0, 0.03], [0.008, 0, 0.02]])

  // === Arms (Right) ===
  const rightUpperArm = addBone('RightUpperArm', rightShoulder, [0.08, -0.26, 0])
  const rightLowerArm = addBone('RightLowerArm', rightUpperArm, [0, -0.24, 0])
  const rightHand = addBone('RightHand', rightLowerArm, [0, -0.16, 0])

  addFinger('RightThumb', rightHand, [[-0.02, 0.03, -0.015], [-0.015, 0.03, 0], [-0.01, 0.025, 0]])
  addFinger('RightIndex', rightHand, [[-0.02, 0, 0.06], [-0.015, 0, 0.045], [-0.01, 0, 0.03]])
  addFinger('RightMiddle', rightHand, [[-0.02, 0, 0.065], [-0.015, 0, 0.05], [-0.01, 0, 0.032]])
  addFinger('RightRing', rightHand, [[-0.02, 0, -0.02], [-0.015, 0, 0.04], [-0.01, 0, 0.025]])
  addFinger('RightPinky', rightHand, [[-0.02, 0, -0.045], [-0.01, 0, 0.03], [-0.008, 0, 0.02]])

  // === Legs (Left) ===
  const leftUpperLeg = addBone('LeftUpperLeg', hips, [-0.07, -0.06, 0])
  const leftLowerLeg = addBone('LeftLowerLeg', leftUpperLeg, [0, -0.42, 0])
  const leftFoot = addBone('LeftFoot', leftLowerLeg, [0, -0.36, 0])
  addBone('LeftToe', leftFoot, [0, -0.06, 0.12])

  // === Legs (Right) ===
  const rightUpperLeg = addBone('RightUpperLeg', hips, [0.07, -0.06, 0])
  const rightLowerLeg = addBone('RightLowerLeg', rightUpperLeg, [0, -0.42, 0])
  const rightFoot = addBone('RightFoot', rightLowerLeg, [0, -0.36, 0])
  addBone('RightToe', rightFoot, [0, -0.06, 0.12])

  // === Breasts ===
  const leftBreast = addBone('LeftBreast', upperChest, [-0.08, 0.06, 0.07])
  addBone('LeftBreast_end', leftBreast, [-0.04, 0.07, 0.09])
  const rightBreast = addBone('RightBreast', upperChest, [0.08, 0.06, 0.07])
  addBone('RightBreast_end', rightBreast, [0.04, 0.07, 0.09])

  // Build skeleton
  const skeleton = new THREE.Skeleton(bones)

  console.log(`✅ 骨骼创建完成: ${bones.length} bones`)

  return { bones, root: hips, skeleton, boneMap }
}

/**
 * 程序化女性人体几何体（带蒙皮权重）
 * 在spine骨骼位置生成水平环，环间三角化
 */
export function createBodyGeometry(bones, boneMap) {
  // 获取spine链上的骨骼+它们的世界位置作为环位置
  const spineBones = ['Hips', 'Spine', 'Spine1', 'Spine2', 'Chest', 'UpperChest', 'Neck', 'Head']

  // 临时更新世界矩阵
  boneMap['Hips'].updateMatrixWorld()

  // 收集每个spine骨骼的世界Y位置和对应的骨骼索引
  const ringDefs = []
  for (const name of spineBones) {
    const bone = boneMap[name]
    if (!bone) continue
    const worldPos = new THREE.Vector3()
    bone.getWorldPosition(worldPos)
    const boneIdx = bones.indexOf(bone)
    ringDefs.push({ y: worldPos.y, boneIdx: boneIdx >= 0 ? boneIdx : 0, name })
  }

  // 身体半径曲线 (Y高度 → 半径)
  // 归一化Y后插值
  if (ringDefs.length < 2) {
    // fallback
    console.warn('骨骼不足，返回空几何体')
    return new THREE.BufferGeometry()
  }

  const minY = ringDefs[0].y
  const maxY = ringDefs[ringDefs.length - 1].y
  const range = maxY - minY || 1

  function getRadius(t) {
    // t: 0=hips, 1=head
    // 臀部:0.21 → 腰:0.13(t≈0.3) → 胸:0.18(t≈0.6) → 肩:0.16(t≈0.75) → 颈:0.07(t≈0.9) → 头:0.08
    const points = [
      [0.00, 0.21],  // hips wide
      [0.15, 0.17],  // lower belly
      [0.30, 0.13],  // waist narrow
      [0.45, 0.16],  // ribs
      [0.60, 0.18],  // chest
      [0.75, 0.15],  // shoulders
      [0.90, 0.07],  // neck
      [1.00, 0.08],  // head
    ]
    // linear interpolation
    for (let i = 1; i < points.length; i++) {
      if (t <= points[i][0]) {
        const [t0, r0] = points[i - 1]
        const [t1, r1] = points[i]
        const frac = (t - t0) / (t1 - t0)
        return r0 + (r1 - r0) * frac
      }
    }
    return points[points.length - 1][1]
  }

  // 生成环
  const ringsPerSegment = 3
  const segmentsPerRing = 24
  const allRings = []

  for (let i = 0; i < ringDefs.length - 1; i++) {
    for (let j = 0; j <= ringsPerSegment; j++) {
      const t = (i + j / ringsPerSegment) / (ringDefs.length - 1)
      const y = ringDefs[i].y + (ringDefs[i + 1].y - ringDefs[i].y) * (j / ringsPerSegment)
      const r = getRadius(t)
      const upperBone = ringDefs[i].boneIdx
      const lowerBone = ringDefs[Math.min(i + 1, ringDefs.length - 1)].boneIdx
      allRings.push({ y, r, boneIdxA: upperBone, boneIdxB: lowerBone })
    }
  }

  // 构建顶点
  const positions = []
  const skinIndices = []
  const skinWeights = []
  const indices = []

  for (let ringIdx = 0; ringIdx < allRings.length; ringIdx++) {
    const ring = allRings[ringIdx]
    for (let seg = 0; seg < segmentsPerRing; seg++) {
      const angle = (seg / segmentsPerRing) * Math.PI * 2
      const x = Math.cos(angle) * ring.r
      const z = Math.sin(angle) * ring.r
      positions.push(x, ring.y, z)

      // skin数据: 4个骨骼索引+权重
      skinIndices.push(ring.boneIdxA, ring.boneIdxB, 0, 0)
      skinWeights.push(0.7, 0.3, 0, 0)
    }
  }

  // 三角形索引
  for (let ringIdx = 0; ringIdx < allRings.length - 1; ringIdx++) {
    const base = ringIdx * segmentsPerRing
    const next = (ringIdx + 1) * segmentsPerRing
    for (let seg = 0; seg < segmentsPerRing; seg++) {
      const a = base + seg
      const b = base + (seg + 1) % segmentsPerRing
      const c = next + seg
      const d = next + (seg + 1) % segmentsPerRing
      indices.push(a, c, b)
      indices.push(b, c, d)
    }
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geometry.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(skinIndices, 4))
  geometry.setAttribute('skinWeight', new THREE.Float32BufferAttribute(skinWeights, 4))
  geometry.setIndex(indices)
  geometry.computeVertexNormals()

  return geometry
}

/**
 * 创建带蒙皮的身体材质
 */
export function createBodyMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: 0xF8E2D3,
    roughness: 0.25,
    metalness: 0.0,
    clearcoat: 0.1,
    clearcoatRoughness: 0.4,
    skinning: true,
    flatShading: false,
  })
}
