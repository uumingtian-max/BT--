# 黑光统一维护补丁说明

针对 [uumingtian-max/ai-agent-project](https://github.com/uumingtian-max/ai-agent-project) 与本地 `C:\Users\ROG\Desktop\ai-agent-project` 已落地的修正。

## 一、你需要维护什么（优先级）

| 优先级 | 项 | 做法 |
|--------|-----|------|
| P0 | `backend/.env` | 复制自 `.env.example`，只开 **一条** LLM 路线（Ollama 或 vLLM） |
| P0 | Ollama 五模型 | `ollama list` 与 `.env` 岗位键一致；重叠模型已删 |
| P1 | 发版冒烟 | `.\scripts\run-agent-smoke.ps1` |
| P1 | 模型管理 | `.\scripts\MANAGE_MODELS.ps1` 或 `launcher\MANAGE_MODELS.bat` |
| P2 | F5-TTS | 可选：`launcher\INSTALL_F5_TTS.bat` + `backend/requirements-tts.txt` |
| P2 | 画图 SD | 可选：`pip install -r backend/requirements-media.txt` + `ENABLE_LOCAL_SD=1` |
| P2 | Electron | 根目录 `npm install`（`electron` 已改为 `^36.4.0`） |
| P3 | CI | push 后看 GitHub Actions；测试模型已改为 `qwen3.5:4b` |

## 二、4 常驻 + 1 按需（5090 24G）

**常驻约 9.7G**（`OLLAMA_RESIDENT_MODELS`，启动预热）：

| 模型 | 职责 |
|------|------|
| nomic-embed-text | EMBED_MODEL |
| functiongemma | AGENT_ROUTER_MODEL |
| qwen3.5:4b | 答案 / 视觉 / 体检 JSON / 简单代码 |
| deepseek-r1:7b | 推理 / 规划 |

**按需约 8.9G**（`OLLAMA_ON_DEMAND_MODELS`，复杂写码时加载，用完 `OLLAMA_RELEASE_ON_DEMAND=1` 卸载）：

| 模型 | 职责 |
|------|------|
| deepseek-coder-v2:16b | CODE_MODEL / ORCH_CODER_MODEL |

已删除重叠：`qwen3.5:0.8b`、`nemotron-3-nano:4b`、`granite4:3b`（granite 结构化改 4b + schema）。

## 三、已改动的文件

- `backend/.env.example` — 无重复 `AGENT_DEFAULT_MODEL`；Ollama/vLLM 分节；F5-TTS 全变量
- `backend/.env` — 你的本机配置（勿提交 git）
- `backend/model_router.py` — 智能路由与五模型栈一致；简单/复杂代码分流
- `backend/agent_runtime.py` — 默认 TASK/EVOLVE 与精简栈一致
- `backend/ollama_pins.py` — keep_alive + 预热
- `backend/llm_client.py` — 请求带 `keep_alive`
- `package.json` — `electron: ^36.4.0`
- `.github/workflows/ci.yml` — CI 模型与 backend requirements 审计
- `scripts/MANAGE_MODELS.ps1`、`scripts/pin-ollama-models.ps1`、`scripts/run-agent-smoke.ps1`
- `backend/requirements-tts.txt` — F5-TTS 可选依赖说明

## 四、落地顺序（5 步）

1. 确认 `backend/.env` 存在且 `LLM_BACKEND=ollama`（你当前配置）。
2. `.\scripts\MANAGE_MODELS.ps1` → [1] 拉模型 → [2] 预热（或重启黑光自动预热）。
3. `.\scripts\run-agent-smoke.ps1` 应全绿。
4. 根目录 `npm install`（更新 Electron 补丁）。
5. 满意后 `git add` + `commit` + `push` 触发 CI。

## 五、多后端路线说明

不必为 Qwen / Gemma vLLM / Codex 各做一个 BAT 切换模型：

- **Ollama**：`LLM_BACKEND=ollama` + 第 5 节岗位键（日常推荐）。
- **vLLM / llama.cpp**：注释掉 Ollama 段，启用 `openai_compatible` + `OPENAI_BASE_URL`，模型名用 `VLLM_DEFAULT_MODEL`（见 `.env.example`）。
- **Codex 网关**：同上，改 `OPENAI_BASE_URL` 与对应 model id。

切换路线 = 改 `.env` + 重启 backend，不必换整个 Electron 安装包。
