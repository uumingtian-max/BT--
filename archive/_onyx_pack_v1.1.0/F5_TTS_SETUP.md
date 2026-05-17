# 手机端语音与 F5-TTS 可选升级

当前手机端默认使用内置 **Lingguang-style TTS**：自然分句、轻微韵律变化、偏真人口气，不需要额外下载 F5 权重。

**F5-TTS** 保留为后续可选升级：当你想做“指定授权音色克隆”时再启用。

## 为什么选 F5-TTS

- 适合 3-10 秒参考音频做零样本音色克隆。
- 本地部署相对轻，手机聊天场景延迟更容易压住。
- 中文/英文都能用，日常对话比系统 TTS 自然很多。
- 当前项目已经有 `REAL_TTS_URL` 网关，不需要改手机端。

## 推荐架构

```text
iPhone /mobile/
  -> ONYX 后端 /edge_tts
  -> REAL_TTS_URL
  -> F5-TTS 服务
  -> 返回 mp3/wav
  -> 手机自动播放
```

## 手机端默认链路

当前默认：

```text
iPhone /mobile/
  -> ONYX 后端 /edge_tts
  -> Lingguang-style Edge TTS
  -> 手机自动播放
```

## F5-TTS 可选链路

启用 F5 后，手机端 `/mobile/` 不需要改地址。聊天回复完成后：

1. 前端调用电脑后端 `POST /edge_tts`
2. 后端优先调用 `REAL_TTS_URL`
3. `REAL_TTS_URL` 指向本项目新增的 F5-TTS 适配器 `http://127.0.0.1:9880/tts`
4. 适配器加载 F5-TTS + 授权参考音频，返回 `audio/wav`
5. 手机自动播放

## 配置

启动 F5-TTS 服务后，在 `backend/.env` 写：

```env
REAL_TTS_URL=http://127.0.0.1:9880/tts
REAL_TTS_VOICE=f5-authorized-voice
REAL_TTS_STYLE=自然、温柔、真人口语，不要播音腔
REAL_TTS_TIMEOUT_SEC=45
```

本项目已经带了一层 F5-TTS 适配器：

```bat
INSTALL_F5_TTS.bat
START_F5_TTS.bat
```

先运行 `INSTALL_F5_TTS.bat` 安装到隔离目录 `.venv-f5`，不会污染主后端环境。适配器启动前需要配置：

```env
F5_TTS_REF_AUDIO=outputs\voice_ref.wav
F5_TTS_REF_TEXT=这里填写参考音频里真实说出来的文字
F5_TTS_MODEL=F5TTS_v1_Base
F5_TTS_DEVICE=cuda
F5_TTS_NFE_STEP=24
```

如果你改用别人的 F5-TTS 服务，不用改手机端，只要那个服务能接收：

```json
{
  "text": "要朗读的话",
  "voice": "f5-authorized-voice",
  "style": "自然、温柔、真人口语，不要播音腔",
  "format": "mp3"
}
```

响应可以是：

- 直接返回 `audio/mpeg` / `audio/wav`
- 或 JSON：`{"audio_base64":"..."}` / `{"audio_url":"..."}`

当前 ONYX 已经支持这三种返回。

## 音频样本建议

- 用你有授权的女声音频。
- 3-10 秒即可先试，最好干净、无背景音乐、无混响。
- 真人自然聊天口气比播音腔更好。
- 采样建议 wav / 16k 或 24k / 单声道。

## 备选

- **GPT-SoVITS**：相似度上限高，1 分钟音频微调后更像，但部署和训练更麻烦。
- **ChatTTS**：语气词、笑声、停顿强，但不是稳定克隆某一个真人音色的首选。
- **CosyVoice**：也很适合，阿里系，3 秒复刻不错；如果 F5-TTS 效果不满意可换它。
- **Fish Speech**：质量强但整体更重，适合后续升级。

## 合规提醒

只接你有授权的真人音色。不要克隆未授权真人或平台专有声音。
