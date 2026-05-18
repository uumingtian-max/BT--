# 本地音视频转写（Transcribe 类工具）

Triggers: transcribe,转写,字幕,whisper,语音转文字,zackees,transcribe-anything,音频,视频转文字,local_transcription,local transcription,local-transcription,本地音视频转写,类工具

---

**何时使用**：用户意图与「本地音视频转写（Transcribe 类工具）」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 用户本机安装 Whisper / faster-whisper，或 Ollama 语音模型（见 `.env` `ORCH_SPEECH_MODEL`）
2. 短视频：可先 `browser_navigate` 取页面说明；本地文件用 `read_file` 仅适用于文本 sidecar
3. 产出：SRT/VTT 分段 + 摘要；长音频先分段转写再 `recursive_long_document` 合并
4. 已有 `text_to_speech` 为 **TTS 反向**；勿与转写混淆
5. 隐私：默认本地处理；若用户坚持用云 API，提醒数据出境与 ToS

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `browser_navigate`
- 工具/配置 `read_file`
- 工具/配置 `recursive_long_document`
- 工具/配置 `text_to_speech`

## 关联技能
- `transcribe_whisper_local`
- `tool_media_gen`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「本地音视频转写（Transcribe 类工具）」相关的事
- [skill:local_transcription] 执行一步可验证操作
