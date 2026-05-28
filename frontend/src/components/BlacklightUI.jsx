import { BLACKLIGHT_THEME } from '../theme/blacklight_theme'
import { useState, useEffect } from 'react'

export default function BlacklightUI({ mode, onStateChange, onEmotionChange, apiUrl, evolutionLevel }) {
  return null
}

export function BlacklightOverlay({ mode, onStateChange, onEmotionChange, apiUrl, evolutionLevel }) {
  const [input, setInput] = useState('')
  const [voiceOn, setVoiceOn] = useState(true)
  const [memoryCount, setMemoryCount] = useState(0)

  useEffect(() => {
    fetch((apiUrl || 'http://localhost:8000').replace('/chat', '/health'))
      .then(r => r.json())
      .then(() => setMemoryCount(prev => prev + 1))
      .catch(() => {})
  }, [])

  const speak = (text) => {
    if (!voiceOn || !text) return
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'zh-CN'
    u.rate = 1.0
    u.pitch = 1.1
    u.volume = 0.9
    speechSynthesis.cancel()
    speechSynthesis.speak(u)
  }

  const [listening, setListening] = useState(false)

  const startVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return
    const rec = new SpeechRecognition()
    rec.lang = 'zh-CN'
    rec.continuous = false
    rec.interimResults = false
    rec.onresult = (e) => {
      const text = e.results[0][0].transcript
      setInput(text)
      setListening(false)
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('bt-blacklight-cmd', { detail: text }))
        onStateChange?.('thinking')
        fetch((apiUrl || 'http://localhost:8000').replace('/chat', '/agent/run'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        }).then(async r => {
          const t = await r.text()
          const m = t.match(/"final_answer","content":"([^"]+)"/)
          const txt = m ? m[1].replace(/\\n/g,' ') : ''
          const u = new SpeechSynthesisUtterance(txt)
          u.lang = 'zh-CN'; u.rate = 1; u.pitch = 1.1
          speechSynthesis.cancel(); speechSynthesis.speak(u)
        }).catch(() => {})
        setTimeout(() => onStateChange?.('idle'), 1000)
      }, 300)
    }
    rec.onerror = () => setListening(false)
    rec.start()
    setListening(true)
  }

  const send = () => {
    if (!input.trim()) return
    const msg = input.trim()
    window.dispatchEvent(new CustomEvent('bt-blacklight-cmd', { detail: msg }))
    onStateChange?.('thinking')
    fetch((apiUrl || 'http://localhost:8000').replace('/chat', '/agent/run'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    }).then(async r => {
      const text = await r.text()
      const matches = text.match(/"final_answer","content":"([^"]+)"/)
      const txt = matches ? matches[1].replace(/\\n/g, ' ') : ''
      speak(txt)
    }).catch(() => {})
    setInput('')
    setTimeout(() => onStateChange?.('idle'), 1000)
  }

  const T = BLACKLIGHT_THEME

  return (
    <>
      <div style={{
        position: 'fixed', top: 16, left: 16, zIndex: 100,
        display: 'flex', alignItems: 'center', gap: 8,
        fontFamily: "'Inter','Noto Sans SC',sans-serif"
      }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%',
          background: T.spectrum_light,
          boxShadow: `0 0 12px ${T.spectrum.glow}` }} />
        <span style={{ fontSize: 13, color: T.text.primary, opacity: 0.9 }}>
          {mode === 'core' ? 'BT-Blacklight · 进化体' : '● 真人形态'}
        </span>
        <span style={{ fontSize: 11, color: '#A78BFA' }}>
          Lv.{evolutionLevel || 1}
        </span>
        <button onClick={() => setVoiceOn(v => !v)} style={{
          marginLeft: 8, padding: '3px 10px', borderRadius: 8,
          border: `1px solid ${T.spectrum_deep}55`,
          background: voiceOn ? T.spectrum_deep + '33' : 'transparent',
          color: voiceOn ? T.spectrum_light : '#6b5a7a',
          fontSize: 12, cursor: 'pointer',
          fontFamily: "'Inter','Noto Sans SC',sans-serif"
        }}>
          {voiceOn ? '有声' : '静音'}
        <button onClick={startVoice} style={{
          marginLeft: 4, padding: '3px 10px', borderRadius: 8,
          border: '1px solid ' + T.spectrum_deep + '55',
          background: listening ? T.spectrum_deep + '55' : 'transparent',
          color: listening ? '#ff6b9d' : T.spectrum_light,
          fontSize: 12, cursor: 'pointer',
          fontFamily: "'Inter','Noto Sans SC',sans-serif",
          animation: listening ? 'pulse 1s infinite' : 'none'
        }}>
          {listening ? '...' : '麦克风'}
        </button>
        </button>
      </div>

      <div style={{
        position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 100,
        width: 'min(600px, 92vw)',
        background: 'rgba(10,5,24,0.82)',
        backdropFilter: 'blur(22px)',
        border: `1px solid ${T.spectrum_deep}88`,
        boxShadow: `0 0 30px ${T.spectrum.glow}33`,
        borderRadius: 16, padding: '12px 16px', display: 'flex', gap: 8
      }}>
        <input value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder={'黑光之下，无界智能...'}
          style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            color: T.text.primary, fontSize: 15,
            fontFamily: "'Inter','Noto Sans SC',sans-serif"
          }} />
        <button onClick={send} style={{
          background: `linear-gradient(135deg, ${T.spectrum_deep}, ${T.spectrum_base})`,
          border: 'none', color: '#fff', padding: '8px 20px', borderRadius: 10,
          cursor: 'pointer', fontSize: 14, fontWeight: 500,
          fontFamily: "'Inter','Noto Sans SC',sans-serif",
          boxShadow: `0 0 12px ${T.spectrum.glow}55`
        }}>发送</button>
      </div>
    </>
  )
}