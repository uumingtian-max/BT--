import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { BLACKLIGHT_THEME } from '../theme/blacklight_theme'

export default function BlacklightParticles({ mode }) {
  const ref = useRef()
  const count = mode === 'core' ? 2000 : 200

  const [geo, mat] = useMemo(() => {
    const g = new THREE.BufferGeometry()
    const pos = new Float32Array(count * 3)
    const sizes = new Float32Array(count)
    for (let i = 0; i < count; i++) {
      const r = mode === 'core' ? 10 : 6
      const th = Math.random() * Math.PI * 2
      const ph = Math.random() * Math.PI
      pos[i*3] = r * Math.sin(ph) * Math.cos(th)
      pos[i*3+1] = r * Math.sin(ph) * Math.sin(th)
      pos[i*3+2] = r * Math.cos(ph)
      sizes[i] = Math.random() * (mode === 'core' ? 2 : 0.8) + 0.2
    }
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    g.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
    const m = new THREE.PointsMaterial({
      color: new THREE.Color(BLACKLIGHT_THEME.particle),
      size: 1, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false
    })
    return [g, m]
  }, [count, mode])

  useFrame(({ clock }) => {
    const t = clock.elapsedTime
    const pos = geo.attributes.position.array
    const sizes = geo.attributes.size.array
    for (let i = 0; i < count; i++) {
      const i3 = i * 3
      if (mode === 'core') {
        pos[i3+1] += Math.sin(t * 2 + i) * 0.02
        pos[i3+2] += Math.cos(t * 1.5 + i) * 0.02
        sizes[i] = 1 + Math.sin(t * 5 + i) * 0.5
      } else {
        pos[i3] += Math.sin(t * 0.5 + i * 0.1) * 0.008
        pos[i3+1] += Math.cos(t * 0.4 + i * 0.1) * 0.008
        pos[i3+2] += Math.sin(t * 0.3 + i * 0.1) * 0.005
        sizes[i] = 0.3 + Math.sin(t * 2 + i) * 0.2
      }
    }
    geo.attributes.position.needsUpdate = true
    geo.attributes.size.needsUpdate = true
    ref.current.rotation.y = t * (mode === 'core' ? 0.1 : 0.02)
  })

  return <points ref={ref} geometry={geo} material={mat} />
}
