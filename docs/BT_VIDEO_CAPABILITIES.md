# BT 视频能力 — 真实状态（以代码为准）

> 更新时间：与仓库实现同步；勿对外承诺下表未标 ✅ 的项。

## 能力矩阵

| 能力 | 用户感知 | 代码现状 | 依赖 |
| --- | --- | --- | --- |
| **图/视频/音频「看懂」**（Omni 多模态） | 上传附件让主模型分析 | ✅ 结构化 `attachments` → `mm_openai_payload` | vLLM `:8001/health` + `openai_compatible` |
| **多图合成视频** | 给多张图生成 mp4 | ✅ `generate_video(image_paths=...)` → imageio 幻灯片 | `pip install imageio` 等 |
| **文生视频（AI）** | 一句话生成真实 AI 视频 | ❌ 默认 **占位动画**；未接 Wan/CogVideoX/LongLive | `VIDEO_GEN_BACKEND` 在代码里**没有**对应实现 |
| **LongLive 权重** | 下载脚本有 | ❌ **未**接入 `generate_video` | 仅 `scripts/download-nvidia-agent-stack.ps1` |

**已删除**：把 `local_path` 写进 prompt 让模型「猜视频」的旧路径；历史里的 `[上传附件]` 块会在发送前剥掉。

## 「看懂」— 实现说明

- 前端：`POST /upload_file` 后，请求体带 `attachments: [{ path, filename, content_type, url }]`，**不再**拼 `[上传附件]` 文本。
- 后端：`/chat/`、`/agent/run` 有附件时 `assert_attachments_can_run()`，vLLM 未就绪直接 **503**，禁止降级成猜路径。
- `llm_client` → `apply_multimodal_to_messages`：`file:///mnt/c/...` 发给 Nemotron。
- vLLM：`scripts/start-omni-vllm-wsl.sh`（`--skip-mm-profiling` 只跳过启动探测）。

验证：

1. `curl.exe http://127.0.0.1:8001/health` → 200
2. 上传短 mp4，问「视频里有什么」
3. 回答基于画面；vLLM 未起时应看到明确错误而非瞎编

## 「生成」— 实现说明

```text
generate_video / generate_ai_video
  ├─ image_paths 非空 → 真实 mp4（slideshow）
  └─ 仅 prompt     → 默认 placeholder（PIL 动画），不是 LongLive/Wan
```

## 对外一句话（诚实版）

**BT 黑光**：vLLM（Nemotron Omni）就绪时可上传图/视频/音频做真多模态理解；可合成幻灯片 mp4；**文生 AI 视频尚未接真实模型**。
