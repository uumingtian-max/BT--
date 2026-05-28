import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { BLACKLIGHT_THEME } from '../theme/blacklight_theme'

export default function BlacklightCore({ state }) {
  const meshRef = useRef()
  const ringRef = useRef()

  useFrame(({ clock }) => {
    const t = clock.elapsedTime
    if (meshRef.current) {
      const pulse = 0.5 + Math.sin(t * 2) * 0.3
      meshRef.current.material.emissiveIntensity = state === 'activating' ? 1.5 + Math.sin(t*12)*0.6 : pulse
      meshRef.current.rotation.y += 0.003
      meshRef.current.rotation.x = Math.sin(t * 0.5) * 0.1
    }
    if (ringRef.current) {
      ringRef.current.rotation.z += 0.005
      ringRef.current.rotation.x += 0.003
      ringRef.current.scale.setScalar(1 + Math.sin(t * 0.8) * 0.1)
    }
  })

  const purple = new THREE.Color(BLACKLIGHT_THEME.spectrum.base)
  const dark = new THREE.Color(BLACKLIGHT_THEME.bg.dark)

  return (
    <group>
      {/* 核心二十面体 — 黑光能量核心 */}
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[1.5, 1]} />
        <meshStandardMaterial
          color={dark}
          metalness={0.95}
          roughness={0.05}
          emissive={purple}
          emissiveIntensity={0.7}
        />
      </mesh>
      {/* 外层光环 — 黑光脉动环 */}
      <mesh ref={ringRef}>
        <torusGeometry args={[1.9, 0.04, 16, 80]} />
        <meshStandardMaterial
          color={purple}
          emissive={purple}
          emissiveIntensity={1.2}
          metalness={0.3}
          roughness={0.1}
        />
      </mesh>
      {/* 内环 */}
      <mesh rotation={[Math.PI/2, 0, 0]}>
        <torusGeometry args={[1.7, 0.03, 16, 64]} />
        <meshStandardMaterial
          color={BLACKLIGHT_THEME.spectrum.light}
          emissive={BLACKLIGHT_THEME.spectrum.light}
          emissiveIntensity={0.8}
          transparent
          opacity={0.6}
          metalness={0.2}
          roughness={0.2}
        />
      </mesh>
    </group>
  )
}
