# ONYX Ollama 运维

Triggers: ollama,模型拉取,11434,LLM_BACKEND,起不来,onyx_ollama_ops,onyx ollama ops,onyx-ollama-ops,ollama ops,ONYX,运维,模型起不来,连不上模型,vllm,gemma,本机推理,5090

---

**何时使用**：模型连不上、换后端、Ollama/vLLM/Gemma 排障时**必须**挂载。

## 执行步骤
1. `scripts/ensure-ollama.ps1`、`START_APP.bat` 自动拉起
2. `/meta/doctor` → `ollama_reachable`；`/meta/models` 列表
3. 连接失败中文提示见 `llm_client.py`；勿在未启动 Ollama 时声称模型可用

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `/meta/doctor` · `/meta/models`
- Ollama：`scripts/ensure-ollama.ps1` · `START_APP.bat`
- 本机 vLLM：`copy backend\.env.local-gemma4.example backend\.env`
- `scripts\START_VLLM_GEMMA4.bat` · `START_APP_LOCAL.bat`（跳过 Ollama）

## 关联技能
- `multi_provider_llm_routing`
- `personal_local_super_agent`
- `codex_lb_routing`

## 自测用语（习惯体检 / 人工抽检）
- 模型连不上怎么办
- 怎么用本机 vLLM 跑 Gemma
