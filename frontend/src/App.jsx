import { Canvas } from '@react-three/fiber'
import { EffectComposer, Bloom, ChromaticAberration } from '@react-three/postprocessing'
import { Suspense, useRef } from 'react'
import BlacklightCore from './components/BlacklightCore'
import BlacklightPrivate from './components/BlacklightPrivate'
import { BlacklightOverlay } from './components/BlacklightUI'
import BlacklightParticles from './components/BlacklightParticles'
import { CommandController } from './logic/Command_Control'
import { BLACKLIGHT_THEME } from './theme/blacklight_theme'
import { useState, useEffect } from 'react'

function FallbackCore() {
  return (
    <mesh>
      <icosahedronGeometry args={[1.5, 2]} />
      <meshStandardMaterial color={BLACKLIGHT_THEME.bg.dark} metalness={0.95} roughness={0.05}
        emissive={BLACKLIGHT_THEME.spectrum.base} emissiveIntensity={0.8} wireframe />
    </mesh>
  )
}

function PrivateEnvironment() {
  return (
    <>
      {/* Warm ambient for real feel */}
      <ambientLight intensity={0.8} color="#fff5f0" />
      <directionalLight position={[5, 8, 5]} intensity={1.2} color="#ffeedd" castShadow />
      <pointLight position={[-3, 2, 3]} intensity={0.6} color={BLACKLIGHT_THEME.spectrum_light} />
      {/* Subtle ground reference */}
      <mesh rotation={[-Math.PI/2, 0, 0]} position={[0, -3.5, 0]} receiveShadow>
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial color="#0a0616" roughness={0.9} />
      </mesh>
    </>
  )
}

function App() {
  const [mode, setMode] = useState('core')
  const [agentState, setAgentState] = useState('idle')
  const [emotion, setEmotion] = useState('idle')
  const [action, setAction] = useState(null)
  const [evolutionLevel, setEvolutionLevel] = useState(1)
  const ccRef = useRef(null)

  useEffect(() => {
    ccRef.current = new CommandController(setMode, setEmotion, setAction)
    const handler = (e) => {
      const cmd = e.detail.trim()
      if (ccRef.current?.execute(cmd)) return
      if (cmd === '\u8c46\u5305\u9a9a\u903c') {
        setMode('private')
        setEmotion('idle')
        setAction(null)
      }
      if (cmd === '\u56de\u5230\u9ed1\u5149') {
        setMode('core')
        setEmotion('normal')
        setAction(null)
      }
    }
    window.addEventListener('bt-blacklight-cmd', handler)
    return () => window.removeEventListener('bt-blacklight-cmd', handler)
  }, [])

  const isPrivate = mode === 'private'

  return (
    <div style={{ width: '100vw', height: '100vh', background: isPrivate ? '#0a0616' : BLACKLIGHT_THEME.bg.dark }}>
      <Canvas camera={{ position: isPrivate ? [0, 1.5, 4] : [0, 0, 8], fov: isPrivate ? 50 : 45 }}>
        <color attach="background" args={[isPrivate ? '#0d0620' : BLACKLIGHT_THEME.bg.dark]} />

        {isPrivate ? (
          <PrivateEnvironment />
        ) : (
          <>
            <fog attach="fog" args={[BLACKLIGHT_THEME.bg.dark, 5, 20]} />
            <ambientLight intensity={0.4} color={BLACKLIGHT_THEME.spectrum.deep} />
            <pointLight position={[5,5,5]} intensity={2} color={BLACKLIGHT_THEME.spectrum.light} />
            <pointLight position={[-5,3,5]} intensity={1} color={BLACKLIGHT_THEME.spectrum.base} />
          </>
        )}

        <Suspense fallback={<FallbackCore />}>
          {isPrivate ? (
            <BlacklightPrivate emotion={emotion} evolutionLevel={evolutionLevel} action={action} />
          ) : (
            <BlacklightCore state={agentState} />
          )}
        </Suspense>

        <BlacklightParticles mode={mode} />

        <EffectComposer>
          <Bloom intensity={isPrivate ? 0.6 : 1.8} luminanceThreshold={0.15} />
          {!isPrivate && <ChromaticAberration offset={[0.003, 0.006]} />}
        </EffectComposer>
      </Canvas>

      <BlacklightOverlay mode={mode} onStateChange={setAgentState} onEmotionChange={setEmotion}
        evolutionLevel={evolutionLevel} apiUrl="http://localhost:8000/chat" />
    </div>
  )
}

export default App
