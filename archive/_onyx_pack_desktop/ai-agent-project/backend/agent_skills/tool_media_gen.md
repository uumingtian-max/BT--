# 工具：图像/视频/TTS

Triggers: generate_image,generate_video,text_to_speech,出图,配音,tool_media_gen,tool media gen,tool-media-gen,media gen,工具,图像,视频,TTS,工具media gen,生成图片,文生图,media_gen

---

**何时使用**：用户需要 **图像/视频/TTS 生成**（工具 `media_gen`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 生成前确认用途合法、无未授权肖像/商标滥用
2. 产物路径写入回复；失败时检查 Ollama/本地模型与 `outputs/` 权限
3. 语音**输入**见 `local_transcription`；`text_to_speech` 为输出

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `local_transcription`
- 工具/配置 `text_to_speech`

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用media gen帮我做一件可验证的小事
- [skill:tool_media_gen] 调用工具并给出证据
