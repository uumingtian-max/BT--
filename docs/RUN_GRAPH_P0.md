# Run Graph P0 — 持久执行时间线

> 状态：P0 已落地到后端底座。目标是把自动化运行从“简单运行记录”升级为可恢复、可审计、可视化的 run graph。

## 新增文件

- `backend/run_graph_store.py`：SQLite 持久化运行图。
- `backend/tests/test_run_graph_store.py`：run graph 生命周期测试。

## 数据库

运行时生成：`backend/run_graph.db`。

`.gitignore` 已忽略 `*.db`、`*.db-wal`、`*.db-shm`，不会提交用户本地运行数据。

## 表结构

### `runs`

一条 Agent/Automation 运行：

- `id`
- `source`：如 `automation`、未来可扩展 `agent`
- `kind`：如 `project_check`、`backend_compile`
- `title`
- `target`
- `status`
- `summary`
- `metadata_json`
- `started_at` / `ended_at`
- `duration_ms`

### `run_steps`

运行中的每一步：

- `id`
- `run_id`
- `parent_step_id`
- `step_index`
- `step_type`：如 `command`、`tool_call`、`error`
- `name`
- `status`
- `input_json`
- `output_json`
- `started_at` / `ended_at`
- `duration_ms`

### `run_artifacts`

运行产物：

- `id`
- `run_id`
- `step_id`
- `artifact_type`
- `title`
- `path`
- `url`
- `metadata_json`
- `created_at`

### `visual_events`

可视化事件流持久化：

- `id`
- `run_id`
- `event_type`
- `source`
- `title`
- `status`
- `payload_json`
- `created_at`

## 已接入的运行路径

### Automation

`backend/automation_runner.py` 已经接入：

- `run_automation_task()` 开始时创建 run graph。
- 每个命令步骤 `_run_command()` 写入 `run_steps`。
- 任务结束时更新 run graph 状态、摘要、耗时。
- 仍保持原 `automation_store.py` 兼容，不破坏旧 `/automation/runs`。

### Visual Event Bus

`backend/visual_event_bus.py` 已经接入：

- 事件仍写入内存队列，保证前端刷新快。
- 同时写入 `run_graph_store.visual_events`，重启后仍能查。
- 如果 SQLite 写入失败，不阻断主任务。

## 新增 API

### `GET /automation/graphs`

查询 automation 类型的 run graph 列表。

参数：

- `limit`：默认 50，最大 200
- `status`：可选，按状态过滤

### `GET /automation/runs/{run_id}/graph`

查询单次自动化运行的完整 run graph，包含：

- run 基本信息
- steps
- artifacts

## 下一步

1. 把 `/agent/run` 的 tool_call/tool_result/final_answer 也写入 run graph。
2. 前端 `AutomationDashboard` 增加“查看步骤图 / 时间线”入口。
3. 新增 `ToolTimeline` 组件，支持按 run_id 展示 step/event。
4. dangerous 工具加入 pending approval step。
5. 后续支持 failed step 单独重跑。

## 验证建议

```bash
python -m py_compile backend/run_graph_store.py backend/automation_runner.py backend/automation_routes.py backend/visual_event_bus.py
pytest backend/tests/test_run_graph_store.py
```

若改了前端，再跑：

```bash
npm run build --prefix frontend
```
