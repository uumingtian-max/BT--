# 真人音色 TTS 接入

手机端已经接入 `/edge_tts`。后端会按下面优先级发声：

1. 如果 `backend/.env` 配了 `REAL_TTS_URL`，优先调用你的真人音色模型服务。
2. 如果真人音色服务不可用，自动退回 Lingguang-style Edge TTS（`alipay_lingguang -> zh-CN-XiaoyiNeural`）。

## 推荐模型

推荐优先级：

1. **IndexTTS2**：中文自然度、音色相似度、情绪/停顿控制最好，适合“像真人聊天”。
2. **CosyVoice2**：实时/低延迟和多语言更友好，适合持续语音对话。
3. **GPT-SoVITS**：生态成熟，资料多，适合自己折腾音色，但自然口气需要调参。

## 配置方式

把真人音色服务跑起来后，在 `backend/.env` 填：

```env
REAL_TTS_URL=http://127.0.0.1:9880/tts
REAL_TTS_API_KEY=
REAL_TTS_VOICE=your-authorized-voice-id
REAL_TTS_STYLE=自然、温柔、真人口语，不要播音腔
REAL_TTS_TIMEOUT_SEC=45
```

`REAL_TTS_URL` 可以返回：

- 直接返回 `audio/mpeg` / `audio/wav` 等音频二进制
- 或返回 JSON：`{"audio_base64":"..."}` / `{"audio_url":"https://..."}`

## 音色授权

只接你有授权的真人音色，例如你自己的声音、购买/授权的音色、或模型自带可商用音色。不要克隆未授权真人或平台专有声音。
