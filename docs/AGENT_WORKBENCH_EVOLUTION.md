# Agent 工作台进化路线

本项目的目标不是做普通聊天机器人，而是做一个本地优先的 AI Agent 自动化工作台。核心体验是：用户提出目标，Agent 自动规划、调用工具、读取资料、运行项目检查、整理结果，并把每一步执行过程可视化出来。

## 产品定位

ONYX-OVERRIDE 应该成为一个本机环境里的 Agent Control Plane：

```text
用户目标
  ↓
任务理解 / 计划
  ↓
工具选择 / 权限提示
  ↓
真实执行 / 日志采集
  ↓
结果压缩 / 记忆写入
  ↓
可视化时间线 / 下一步建议
```

## 设计原则

1. **真实执行优先**：能调用工具就不要只给教程。
2. **过程透明**：每个 thinking、tool_call、tool_result、final_answer 都应该可见。
3. **本地优先**：文件、记忆、画像、技能和运行日志优先存储在本机。
4. **工具插件化**：工具必须有描述、分组、参数 schema、风险等级和启用状态。
5. **用户可控**：涉及写入、外部请求或桌面交互的动作要有清晰提示。
6. **可回放**：一次 Agent 任务应该能被保存、复盘、调试和转成 playbook。

## 已完成的底座升级

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 结构化工具注册表 | 已完成 | `backend/tool_registry.py` |
| 工具风险等级 | 已完成 | `safe / confirm / dangerous` |
| UI 工具元数据接口 | 已完成 | `GET /meta/tools/registry` |
| 工具风险摘要接口 | 已完成 | `GET /meta/tools/risks` |
| 工具注册表测试 | 已完成 | `backend/tests/test_tool_registry.py` |
| 架构文档 | 已完成 | `docs/ARCHITECTURE.md` |
| 工具文档 | 已完成 | `docs/TOOLS.md` |
| 开发文档 | 已完成 | `docs/DEVELOPMENT.md` |

## 下一阶段：执行时间线

前端应该把 `/agent/run` 的 SSE 事件渲染成 Agent Run Timeline：

```text
[用户目标]
  ↓
[思考 / 计划]
  ↓
[工具调用]
  ↓
[工具结果：成功 / 失败]
  ↓
[上下文压缩]
  ↓
[最终回答]
  ↓
[写入记忆 / playbook]
```

建议事件结构：

```json
{
  "run_id": "uuid",
  "step_id": "uuid",
  "type": "tool_call",
  "status": "running",
  "tool": "read_file",
  "risk_level": "safe",
  "params": {},
  "started_at": "2026-05-17T12:00:00Z",
  "ended_at": null,
  "duration_ms": null,
  "error": null
}
```

## 下一阶段：工具提示机制

基于 `risk_level` 做执行前提示：

| 风险等级 | 前端行为 |
| --- | --- |
| `safe` | 低风险，只展示工具调用过程 |
| `confirm` | 展示确认提示和参数预览 |
| `dangerous` | 展示高风险提示、参数预览和取消入口 |

## 下一阶段：记忆树与上下文压缩

记忆不要只做线性聊天记录，建议分层：

```text
memory_tree/
  user_profile/       长期偏好、设备习惯、项目偏好
  project_memory/     当前项目结构、重要文件、历史修复
  playbooks/          成功任务复盘和失败教训
  tool_observations/  工具成功率、常见错误、耗时统计
  knowledge_notes/    用户导入的长期资料
```

上下文组装建议：

1. 根据用户任务检索相关记忆。
2. 按 `project / user / tool / skill / recent` 分桶。
3. 对每个桶独立压缩。
4. 给 Agent 注入来源标签，避免混淆旧信息和当前结果。
5. 每次工具执行后只把摘要写回记忆，不写入大段原始日志。

## 下一阶段：插件化工具

建议未来工具目录结构：

```text
backend/plugins/
  file_ops/
    plugin.json
    handler.py
  browser/
    plugin.json
    handler.py
  github/
    plugin.json
    handler.py
```

`plugin.json` 示例：

```json
{
  "name": "read_file",
  "group": "files_code",
  "description": "读取本地文件内容",
  "risk_level": "safe",
  "timeout_seconds": 30,
  "input_schema": {
    "type": "object",
    "properties": {
      "path": {"type": "string"}
    },
    "required": ["path"]
  }
}
```

## 前端工作台建议布局

```text
┌────────────────────────────────────────────────────────────┐
│ 顶部：模型 / 模式 / 后端状态 / 工具风险摘要                   │
├───────────────┬─────────────────────────────┬──────────────┤
│ 左侧工具面板   │ 中间 Agent 时间线             │ 右侧记忆/上下文 │
│ - 工具搜索     │ - 用户目标                    │ - 相关记忆      │
│ - 分组         │ - 计划                        │ - 技能包        │
│ - 风险标记     │ - 工具调用                    │ - 压缩摘要      │
│ - 参数 schema  │ - 结果 / 错误                  │ - playbook      │
├───────────────┴─────────────────────────────┴──────────────┤
│ 底部输入框：自然语言目标 / 文件拖拽 / 运行按钮 / 停止按钮       │
└────────────────────────────────────────────────────────────┘
```

## 质量指标

建议后续记录这些指标：

| 指标 | 用途 |
| --- | --- |
| tool_success_rate | 工具成功率 |
| average_run_duration_ms | 任务平均耗时 |
| failed_step_count | 失败步骤数 |
| user_confirmation_count | 用户确认次数 |
| memory_hit_count | 记忆命中次数 |
| context_compression_ratio | 上下文压缩比例 |
| final_answer_quality_flag | 最终回答质量兜底是否触发 |

## 推荐实施顺序

1. 前端读取 `/meta/tools/registry`，做工具面板和风险徽章。
2. 给 `/agent/run` 每次执行生成 `run_id` 和 `step_id`。
3. 把 SSE 步骤统一成事件 schema。
4. 做 Agent Run Timeline 组件。
5. 给需要确认的工具增加执行前提示。
6. 把运行日志持久化到本地 SQLite。
7. 做记忆树检索和上下文压缩面板。
8. 把工具从 `TOOL_MAP` 逐步迁移到 plugins 目录。
