# BT（黑光）本地跑通清单

按顺序做；任一步失败不要跳过后面的「验证」。

## 1. vLLM（主模型 · 看懂视频/图）

```powershell
# Windows 终端
wsl -e bash -lc "sed -i 's/\r$//' /mnt/c/Users/ROG/Desktop/ai-agent-project/scripts/start-omni-vllm-wsl.sh && bash /mnt/c/Users/ROG/Desktop/ai-agent-project/scripts/start-omni-vllm-wsl.sh"
```

等到日志出现 `Application startup complete`，再：

```powershell
curl.exe http://127.0.0.1:8001/health
```

应返回 200。

## 2. 后端

```powershell
cd C:\Users\ROG\Desktop\ai-agent-project\backend
# 使用 backend/.env 或 .env.local-vllm-nano.example 复制后的配置
# LLM_BACKEND=openai_compatible  OPENAI_BASE_URL=http://127.0.0.1:8001/v1
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

自检：

```powershell
curl.exe http://127.0.0.1:8000/meta/doctor
pytest ..\backend\tests\ -q
```

## 3. 前端

```powershell
cd C:\Users\ROG\Desktop\ai-agent-project\frontend
npm run build
# 或开发：npm start
```

上传附件测试：vLLM 未起时应 **503**；`:8001` 正常时应走真多模态（见 `docs/BT_VIDEO_CAPABILITIES.md`）。

## 4. Run Graph（自动化时间线）

- 库：`backend/run_graph.db`（已在 `.gitignore` 忽略 `*.db`）
- 接口：`GET /meta/run-graph/runs/{run_id}`、`GET /automation/runs/{run_id}/graph`
- 事件：`/meta/visual-events` 会合并 SQLite，重启后时间线不丢

## 5. 常见问题

| 现象 | 处理 |
| --- | --- |
| 上传视频后 503 | 先完成步骤 1 |
| Agent 报错模型 | 查 `.env` 的 `LOCKED_MODEL_ID` 与 vLLM `/v1/models` |
| 仍看到 `[上传附件]` 路径文字 | 刷新前端；旧会话历史会自动剥掉路径块 |
