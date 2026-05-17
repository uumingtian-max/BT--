# 本地 Whisper 转写

Triggers: whisper,transcribe,speech_to_text,语音转文字,transcribe_whisper_local,transcribe whisper local,transcribe-whisper-local,本地,转写

---

**何时使用**：用户意图与「本地 Whisper 转写」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. API：`POST` 本地 agent `speech_to_text`（见 `local_agent_api.py`）
2. 与 `local_transcription` 技能一致；大文件分片转写

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `speech_to_text`
- 工具/配置 `local_transcription`

## 关联技能
- `local_transcription`
- `tool_media_gen`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「本地 Whisper 转写」相关的事
- [skill:transcribe_whisper_local] 执行一步可验证操作
