# 本机模型岗位 Pin（精简栈 · 4 常驻 + 1 按需）

Triggers: 模型岗位,pin,keep_alive,视觉,画图,推理,答案,精简,常驻,按需

---

## 常驻 VRAM（约 9.7G，`ollama ps` 应长期看到）

| 模型 | 职责 |
|------|------|
| nomic-embed-text:latest | 嵌入（后台） |
| functiongemma:latest | 工具路由 |
| **qwen3.5:4b** | 答案 / 视觉 / 快答 / 审查 / 习惯体检 JSON |
| **deepseek-r1:7b** | 推理 / 规划 / 进化 |

`.env`：`OLLAMA_RESIDENT_MODELS=...`（四个逗号分隔）

## 按需（约 8.9G，复杂写码才加载）

| 模型 | 职责 |
|------|------|
| deepseek-coder-v2:16b | 复杂重构、多文件、编排实现 |

- 路由：`model_router` 命中 `CODE_MODEL` 时，backend 自动 `ensure_on_demand_loaded` → 对话 → `release`（`keep_alive=0`）。
- 简单脚本走 `CODE_SIMPLE_MODEL=qwen3.5:4b`，**不会**拉起 16b。
- 手动：`ollama run deepseek-coder-v2:16b`，用完 `ollama stop deepseek-coder-v2:16b`。

`.env`：`OLLAMA_ON_DEMAND_MODELS=deepseek-coder-v2:16b`，`OLLAMA_RELEASE_ON_DEMAND=1`

## 已删除（重叠）

- `qwen3.5:0.8b`、`nemotron-3-nano:4b`、`granite4:3b` — 结构化/体检改 qwen3.5:4b + JSON schema

## 画图

`generate_image`（Stable Diffusion），不是 Ollama。

## 管理脚本

- `scripts\MANAGE_MODELS.ps1` — [1] 拉 5 个磁盘模型，[2] 只预热 4 个常驻
- `scripts\pin-ollama-models.ps1` — 同上
