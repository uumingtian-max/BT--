# 前端自动化维护面板

本文件说明 `AutomationDashboard` 的用途、后端依赖接口和接入方式。

## 已新增文件

```text
frontend/src/AutomationDashboard.js
frontend/src/AutomationDashboard.css
frontend/src/automationApi.js
```

## 面板用途

`AutomationDashboard` 是“自动化 + 可视化第一版”的前端组件，用来展示和触发本地维护任务：

- 查看自动化能力清单
- 运行项目检查
- 查看最近自动化 run
- 查看自动化事件流
- 展示每个检查步骤的输出摘要

## 后端接口依赖

组件依赖以下接口：

```text
GET  /automation/capabilities
POST /automation/run
GET  /automation/runs?limit=20
GET  /automation/events?limit=50
```

这些接口由以下后端文件提供：

```text
backend/automation_routes.py
backend/automation_runner.py
backend/automation_store.py
backend/visual_event_bus.py
```

## 最小接入方式

在 `frontend/src/App.js` 顶部加入：

```js
import AutomationDashboard from './AutomationDashboard';
```

在侧边栏按钮区加入：

```jsx
<button
  type="button"
  className={'sidebar-sub-btn' + (panel === 'automation' ? ' active' : '')}
  onClick={() => setPanel('automation')}
>
  <Icon name="activity" size={12} /> 自动化
</button>
```

在主内容区域的 panel 判断里加入：

```jsx
{panel === 'automation' ? (
  <AutomationDashboard />
) : panel === 'system' ? (
  <SystemPanel ... />
) : ...}
```

## 验证步骤

启动后端：

```bash
python start.py backend
```

检查接口：

```bash
curl http://localhost:8000/automation/capabilities
curl http://localhost:8000/automation/runs?limit=20
```

运行一次项目检查：

```bash
curl -X POST http://localhost:8000/automation/run \
  -H "Content-Type: application/json" \
  -d '{"task_kind":"project_check","target":"backend"}'
```

前端构建验证：

```bash
npm run build --prefix frontend
```

## 当前安全边界

自动化 runner 使用白名单任务，不暴露任意命令执行。当前允许：

```text
project_check
backend_compile
frontend_build
repo_health
```

目标允许：

```text
all
backend
frontend
```

后续如果要增加新维护任务，先在 `automation_runner.py` 的白名单中定义，再补测试。

## 下一步建议

1. 把 `AutomationDashboard` 挂进侧边栏。
2. 给 `/automation/run` 增加后台执行模式，避免前端等待长构建。
3. 把 events 从内存缓冲升级为 SQLite 持久化。
4. 将 run 输出和 Agent 时间线统一成 `run_id` 维度。
5. 增加 GitHub 同步任务，例如检查工作区、生成维护报告、准备提交摘要。
