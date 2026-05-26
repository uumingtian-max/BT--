/** 单一语音通道：开机播报 + 任意文案朗读（档案可进化） */

const SESSION_STARTUP_KEY = 'bt_voice_startup_played';

export async function fetchVoiceProfile(apiBase) {
  try {
    const r = await fetch(`${apiBase}/voice/profile`);
    if (!r.ok) return null;
    return r.json();
  } catch {
    return null;
  }
}

export async function playMp3FromResponse(res) {
  if (!res || !res.ok) return false;
  const blob = await res.blob();
  if (!blob.size) return false;
  const url = URL.createObjectURL(blob);
  try {
    const audio = new Audio(url);
    audio.volume = 1;
    await audio.play();
    return true;
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }
}

/** 每个应用会话只播一次开机语音 */
export async function playStartupVoice(apiBase) {
  if (typeof window === 'undefined') return;
  if (sessionStorage.getItem(SESSION_STARTUP_KEY)) return;
  try {
    const prof = await fetchVoiceProfile(apiBase);
    if (prof && prof.startup_on_boot === false) return;
    const r = await fetch(`${apiBase}/voice/startup`, { method: 'POST' });
    if (r.status === 204) return;
    const ok = await playMp3FromResponse(r);
    if (ok) sessionStorage.setItem(SESSION_STARTUP_KEY, '1');
  } catch {
    /* ignore */
  }
}

export async function speakText(apiBase, text, { voice } = {}) {
  const body = { text: text || '', voice: voice || '' };
  const r = await fetch(`${apiBase}/voice/speak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(body),
  });
  return playMp3FromResponse(r);
}
