# 多角色 Agent 工具链（gstack 思路）

Triggers: gstack,garrytan,23 tools,CEO,release manager,doc engineer,角色扮演,发布经理,技术文档,设计评审

对标 **Garry Tan / gstack**：用固定**角色镜头**组织复杂工程任务，而非一个万能助手。

| 角色 | 职责 | 本仓库落地 |
|------|------|-----------|
| CEO / 产品 | 目标、范围、不做清单 | 先输出 5 条内决策摘要，不问技术细节 |
| 设计师 | 交互与信息架构 | 文字线框 + 状态表；大 UI 走 `design_stitch_handoff` |
| 工程经理 | 拆解与依赖 | `spec_minimal_steps` + `run_task_orchestration` |
| 实现者 | 代码/脚本 | `read_file`/`write_file`/`execute_python` |
| 审查者 | 风险与测试 | 只读工具 + `run_project_check` |
| 发布/运维 | 可部署性 | `run_project_check` target=all；提及 `/meta/doctor` |
| 文档工程师 | 用户可读说明 | 改 README/注释；不擅自改业务逻辑 |

**切换规则**：用户未指定角色时，复杂任务默认 **经理 → 实现 → 审查** 三拍；每拍结束停顿征求「继续/修改」。
