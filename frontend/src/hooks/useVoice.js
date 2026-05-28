import { useRef, useCallback } from 'react'

export function useVoice(apiUrl) {
  const audioRef = useRef(null)

  const speak = useCallback(async (text) => {
    if (!text) return
    try {
      const res = await fetch((apiUrl || 'http://localhost:8000').replace('/chat', '/tts'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'zh-CN-XiaoxiaoNeural', tone: 'soft' })
      })
      if (!res.ok) {
        // Fallback: use browser Web Speech API
        const u = new SpeechSynthesisUtterance(text)
        u.lang = 'zh-CN'
        u.rate = 1.0
        u.pitch = 1.1
        speechSynthesis.cancel()
        speechSynthesis.speak(u)
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      if (audioRef.current) {
        audioRef.current.src = url
        audioRef.current.play()
      }
    } catch {
      // Silent fallback
    }
  }, [apiUrl])

  return { speak, audioRef }
}
