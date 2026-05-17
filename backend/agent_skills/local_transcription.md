# 本地音视频转写（Transcribe 类工具）

Triggers: transcribe,转写,字幕,whisper,语音转文字,zackees,transcribe-anything,音频,视频转文字

对标 **transcribe-anything** 等本地 Whisper 流程 — 本仓库不内置 GPU 转写服务，指导 + 可用工具组合。

**推荐路径**：

1. 用户本机安装 Whisper / faster-whisper，或 Ollama 语音模型（见 `.env` `ORCH_SPEECH_MODEL`）。
2. 短视频：可先 `browser_navigate` 取页面说明；本地文件用 `read_file` 仅适用于文本 sidecar。
3. 产出：SRT/VTT 分段 + 摘要；长音频先分段转写再 `recursive_long_document` 合并。
4. 已有 `text_to_speech` 为 **TTS 反向**；勿与转写混淆。
5. 隐私：默认本地处理；若用户坚持用云 API，提醒数据出境与 ToS。

**禁止**：声称已转写但未产生任何输出文件或日志；禁止协助转写侵权盗版内容。
