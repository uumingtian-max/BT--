import { useRef, useMemo, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { BLACKLIGHT_THEME } from '../theme/blacklight_theme'
import { createSkeleton, createBodyGeometry, createBodyMaterial } from './BlacklightSkeleton'

export default function BlacklightPrivate({ emotion, evolutionLevel, action }) {
  const groupRef = useRef()
  const headBoneRef = useRef()
  const skeletonRef = useRef()

  // 一次性创建骨骼+几何体
  const { skeleton, boneMap } = useMemo(() => {
    const { skeleton, boneMap } = createSkeleton()
    return { skeleton, boneMap }
  }, [])

  const bodyGeo = useMemo(() => createBodyGeometry(skeleton.bones, boneMap), [skeleton])
  const bodyMat = useMemo(() => createBodyMaterial(), [])

  // 缓存骨骼引用
  useEffect(() => {
    headBoneRef.current = boneMap['Head']
    skeletonRef.current = skeleton
  }, [boneMap, skeleton])

  useFrame(({ clock, camera }) => {
    const t = clock.elapsedTime
    const isIdle = !action

    // === 头跟随相机 ===
    if (headBoneRef.current && camera) {
      const headWorld = new THREE.Vector3()
      headBoneRef.current.getWorldPosition(headWorld)
      const target = camera.position.clone()
      target.y = headWorld.y
      headBoneRef.current.lookAt(target)
    }

    // === 动作系统 (优先级最高) ===
    if (boneMap['Hips'] && boneMap['Spine']) {
      switch (action) {
        case 'kneel':
          boneMap['Hips'].position.y = 0.85 - 0.6
          boneMap['LeftUpperLeg'].rotation.x = 0.8
          boneMap['RightUpperLeg'].rotation.x = 0.8
          break
        case 'lean_forward':
          boneMap['Spine'].rotation.x = 0.3
          boneMap['Hips'].position.z = 0.15
          break
        case 'bend_over':
          boneMap['Spine'].rotation.x = 0.6
          boneMap['Hips'].rotation.x = 0.2
          break
        case 'chest_up':
          boneMap['UpperChest'] && (boneMap['UpperChest'].position.z = -0.08)
          boneMap['Spine'].rotation.x = -0.15
          break
        case 'lean_back':
          boneMap['Spine'].rotation.x = -0.25
          break
        default:
          // 重置动作姿态
          boneMap['Spine'].rotation.x = 0
          boneMap['Hips'].rotation.x = 0
          if (boneMap['UpperChest']) boneMap['UpperChest'].position.z = 0
          if (boneMap['LeftUpperLeg']) boneMap['LeftUpperLeg'].rotation.x = 0
          if (boneMap['RightUpperLeg']) boneMap['RightUpperLeg'].rotation.x = 0
          boneMap['Hips'].position.z = 0
      }
    }

    // === 闲置动画 (仅无动作时) ===
    if (isIdle) {
      if (boneMap['UpperChest'] && boneMap['Chest']) {
        const breath = 1 + Math.sin(t * 2.5) * 0.02
        boneMap['UpperChest'].scale.set(1, breath, 1)
        boneMap['Chest'].scale.set(1, 1 + Math.sin(t * 2.5) * 0.015, 1)
      }

      if (boneMap['Hips']) {
        boneMap['Hips'].rotation.y = Math.sin(t * 0.35) * 0.03
        boneMap['Hips'].position.y = 0.85 + Math.sin(t * 0.4) * 0.03
      }

      if (boneMap['LeftUpperArm']) {
        boneMap['LeftUpperArm'].rotation.z = 0.15 + Math.sin(t * 0.5) * 0.04
      }
      if (boneMap['RightUpperArm']) {
        boneMap['RightUpperArm'].rotation.z = -0.15 + Math.sin(t * 0.5 + 1) * 0.04
      }
    }

    // 整体缓慢旋转
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(t * 0.2) * 0.05
    }
  })

  const skin = '#F8E2D3'
  const cloth = '#1A0D2E'

  return (
    <group ref={groupRef} scale={2.2}>
      {/* === 骨骼蒙皮身体 === */}
      <skinnedMesh
        skeleton={skeleton}
        geometry={bodyGeo}
        material={bodyMat}
        frustumCulled={false}
      />

      {/* === 头部 === */}
      <primitive object={boneMap['Head']}>
        <mesh>
          <sphereGeometry args={[0.1, 48, 48]} />
          <meshPhysicalMaterial color={skin} roughness={0.25} metalness={0.0}
            clearcoat={0.1} clearcoatRoughness={0.4} />
        </mesh>
      </primitive>

      {/* === 左臂 === */}
      <primitive object={boneMap['LeftUpperArm']}>
        <mesh rotation={[0, 0, 0.15]}>
          <capsuleGeometry args={[0.04, 0.5, 8, 16]} />
          <meshStandardMaterial color={skin} roughness={0.25} />
        </mesh>
        <primitive object={boneMap['LeftLowerArm']}>
          <mesh>
            <capsuleGeometry args={[0.035, 0.4, 8, 16]} />
            <meshStandardMaterial color={skin} roughness={0.25} />
          </mesh>
        </primitive>
      </primitive>

      {/* === 右臂 === */}
      <primitive object={boneMap['RightUpperArm']}>
        <mesh rotation={[0, 0, -0.15]}>
          <capsuleGeometry args={[0.04, 0.5, 8, 16]} />
          <meshStandardMaterial color={skin} roughness={0.25} />
        </mesh>
        <primitive object={boneMap['RightLowerArm']}>
          <mesh>
            <capsuleGeometry args={[0.035, 0.4, 8, 16]} />
            <meshStandardMaterial color={skin} roughness={0.25} />
          </mesh>
        </primitive>
      </primitive>

      {/* === 左腿 === */}
      <primitive object={boneMap['LeftUpperLeg']}>
        <mesh>
          <capsuleGeometry args={[0.06, 0.55, 8, 16]} />
          <meshStandardMaterial color={skin} roughness={0.25} />
        </mesh>
        <primitive object={boneMap['LeftLowerLeg']}>
          <mesh>
            <capsuleGeometry args={[0.05, 0.45, 8, 16]} />
            <meshStandardMaterial color={skin} roughness={0.25} />
          </mesh>
          <primitive object={boneMap['LeftFoot']}>
            <mesh>
              <boxGeometry args={[0.06, 0.03, 0.12]} />
              <meshStandardMaterial color={cloth} roughness={0.3} />
            </mesh>
          </primitive>
        </primitive>
      </primitive>

      {/* === 右腿 === */}
      <primitive object={boneMap['RightUpperLeg']}>
        <mesh>
          <capsuleGeometry args={[0.06, 0.55, 8, 16]} />
          <meshStandardMaterial color={skin} roughness={0.25} />
        </mesh>
        <primitive object={boneMap['RightLowerLeg']}>
          <mesh>
            <capsuleGeometry args={[0.05, 0.45, 8, 16]} />
            <meshStandardMaterial color={skin} roughness={0.25} />
          </mesh>
          <primitive object={boneMap['RightFoot']}>
            <mesh>
              <boxGeometry args={[0.06, 0.03, 0.12]} />
              <meshStandardMaterial color={cloth} roughness={0.3} />
            </mesh>
          </primitive>
        </primitive>
      </primitive>

      {/* === 胸部 === */}
      <primitive object={boneMap['LeftBreast']}>
        <mesh>
          <sphereGeometry args={[0.09, 24, 24]} />
          <meshStandardMaterial color={skin} roughness={0.2} />
        </mesh>
      </primitive>
      <primitive object={boneMap['RightBreast']}>
        <mesh>
          <sphereGeometry args={[0.09, 24, 24]} />
          <meshStandardMaterial color={skin} roughness={0.2} />
        </mesh>
      </primitive>

      {/* === Glow Ring === */}
      <primitive object={boneMap['Head']}>
        <mesh>
          <torusGeometry args={[0.16, 0.01, 16, 64]} />
          <meshStandardMaterial
            color={BLACKLIGHT_THEME.spectrum_light}
            emissive={BLACKLIGHT_THEME.spectrum_light}
            emissiveIntensity={0.6} transparent opacity={0.5} />
        </mesh>
      </primitive>
    </group>
  )
}
