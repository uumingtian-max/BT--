# 黑光 · Nemotron + SGLang 七项任务单

> **专家席**：核心 #1–#11 + 变现 #12–#38 已在 `backend/expert_roles.py` 就绪；执行内核仍 ≤4 次 LLM，变现席按关键词激活。
> **本文只改任务 1**（SGLang 不走 Ollama）；任务 2–7 保持原意。

---

## 任务 1 · 启动本地 GPU 大模型（SGLang，不是 Ollama）

### 模型目录结论（已核对）

路径：`D:\models\Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4`

| 检查项 | 结果 |
|--------|------|
| 格式 | **HuggingFace safetensors**（`model-00001~03-of-00003.safetensors` + `config.json`） |
| GGUF | **无** → 可直接用 SGLang，不必走 llama.cpp |
| 量化 | `hf_quant_config.json` / ModelOpt 混合精度 → 需 `--reasoning-parser nemotron_3` |

### 为什么用 SGLang

- 自带 **OpenAI 兼容** HTTP：`/v1/chat/completions`
- 黑光后端几乎不用改：把 GPU 路由从 Ollama `11434` 改为 **`http://127.0.0.1:30000/v1`**
- **Nemotron-Reasoning** 会输出 `` 思考块 → `llm_judge()` / TICK / 超级记忆可保留思考轨迹，判断质量更好

### 启动前（一次性）

```powershell
cd C:\Users\ROG\Desktop\ai-agent-project
.\scripts\patch-nemotron-config.ps1
```

生成：`D:\models\...\Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4-sglang-win\config.json`

### 方式 A · 本机 SGLang（任务单默认端口 **30000**）

```powershell
conda activate sglang   # 你的 SGLang 环境名

python -m sglang.launch_server ^
  --model-path D:\models\Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4 ^
  --served-model-name nemotron-omni ^
  --trust-remote-code ^
  --reasoning-parser nemotron_3 ^
  --host 0.0.0.0 ^
  --port 30000
```

验收：

```powershell
curl http://127.0.0.1:30000/v1/models
```

### 方式 B · Docker（仓库现成，宿主机端口 **8001**）

```powershell
cd C:\Users\ROG\Desktop\ai-agent-project
docker compose -f docker-compose.nemotron.yml up -d
curl http://127.0.0.1:8001/v1/models
```

若用 Docker，`.env` 里 `GPU_OPENAI_BASE_URL` 写 `http://127.0.0.1:8001/v1`，**不要**写 30000。

### 任务 1 完成后 · `backend/.env` 必改项

```env
BKLT_DUAL_ENGINE=1
LLM_BACKEND=openai_compatible

# 云端文字（你一直用的）
API_OPENAI_BASE_URL=https://inferaichat.com/v1
API_MODEL=claude-opus-4-7
AGENT_DEFAULT_MODEL=claude-opus-4-7
LOCKED_MODEL_ID=claude-opus-4-7

# 本地 Omni（SGLang，不是 Ollama）
GPU_OPENAI_BASE_URL=http://127.0.0.1:30000/v1
GPU_OPENAI_API_KEY=local
GPU_MODEL=nemotron-omni
BKLT_OMNI_MODEL=nemotron-omni
ORCH_VISION_MODEL=nemotron-omni
ORCH_SPEECH_MODEL=nemotron-omni
AGENT_OMNI_MM_ENABLED=1
```

> **注意**：当前 `.env` 若把 `GPU_OPENAI_BASE_URL` 指到 inferaichat，附件/多模态会走错路，必须改成本地 SGLang。

---

## 任务 2 · 云端 API（inferaichat / Opus）

- 纯文字、编排、专家内核：`claude-opus-4-7`（或你的 `claude-ccmax`）
- `ORCH_PLANNER_MODEL` / `ORCH_CODER_MODEL` / `ORCH_REVIEWER_MODEL` 保持 Opus

## 任务 3 · NPU 嵌入（记忆 / 技能检索）

- `EMBED_MODEL=llama-nemotron-embed-1b-v2`
- `EMBED_BACKEND=openvino` + `EMBED_DEVICE=NPU`（你现网配置）
- 与 SGLang **独立**，不走 Ollama

## 任务 4 · 黑光后端 + 双引擎路由

- `python start.py backend` 或 `launcher\START_APP.bat`
- 确认 `GET http://127.0.0.1:8000/meta/llm-routes` 显示 `gpu` + `api` 均 ok

## 任务 5 · TICK / 超级记忆 / `llm_judge`

- `CONSCIOUS_TICK_ENABLED=1`
- Nemotron Reasoning 的思考块喂给 `llm_judge()`（待接入 `consciousness_loop` / `super_memory`）
- 专家 #12–#38 按「赚钱/自动化」关键词自动激活，不全员连聊

## 任务 6 · 语音（灵光 / Edge TTS）

- `/voice/startup` · `alipay_lingguang` → `zh-CN-XiaoyiNeural`

## 任务 7 · 数字人（深度图 + SadTalker）

- `scripts/digital-human/depth_infer.py` → `photo.png` + `depth.png`
- `scripts/sadtalker/download_models.py` + `run_portrait.ps1`

---

## 你一直要用的模型一览

| 用途 | 模型 ID | 入口 |
|------|---------|------|
| 主聊天 / 文字 | `claude-opus-4-7` | inferaichat API |
| 附件 / 图音视频 | `nemotron-omni` | SGLang `:30000/v1`（或 Docker `:8001`） |
| 向量记忆 | `llama-nemotron-embed-1b-v2` | OpenVINO NPU |
| Ollama（备用栈，非 Omni 主路） | `qwen3.5:9b` 等 | `:11434` |
| 语音 | Edge `zh-CN-XiaoyiNeural` | `/voice/*` |
