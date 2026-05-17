# 修复包应用记录

来源: `C:\Users\ROG\Desktop\ai-agent-project-fixed (1).zip`  
应用时间: 2026-05-17

## 已合并的变更

| 文件 | 说明 |
|------|------|
| `backend/meta_routes.py` | vLLM `/v1/models` 列表增加 45s TTL 缓存，减轻 scheduler 双次轮询 |
| `frontend/src/modelCatalog.js` | 锁定模型改为 vLLM 路径 id，与 `backend/.env` 一致 |
| `knowledge-vault/system_integrated-overview.md` | 系统概览文档同步 |
| `backend/.env` | `EXTRA_MODEL_IDS` 恢复 Ollama 备用模型条目 |

## 未覆盖（保留本机数据）

- `backend/*.db`、`agent_tasks.db` — 运行时数据库未覆盖
- `logs/` — 本机日志保留
- `node_modules/`、`.venv-f5/` — 需在本机 `npm install` / 按文档重装

## 验证建议

1. WSL 启动 vLLM: `scripts/START_VLLM_GEMMA4.bat` 或 `打开本机Gemma模型.cmd`
2. 本机启动: `START_APP_LOCAL.bat`
3. 浏览器检查模型显示为 **Gemma 4 26B · vLLM (本地)**
