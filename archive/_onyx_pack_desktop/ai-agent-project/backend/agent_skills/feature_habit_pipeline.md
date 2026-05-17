# 习惯体检流水线（每天两次）

Triggers: 习惯体检,habit,每天两次,行为分析,自我扩展,learned_habit,定时体检

- 默认 **本地 9:00 / 21:00** 自动执行（`HABIT_CHECK_HOURS`）；后端 `background_habit_loop` 负责到点触发。
- 每次流程：`/meta/doctor` → `infer_behavior_patterns` → 日报 → playbook 记忆 → 可选 `learned_habit_auto.md`。
- 手动：`POST /meta/habit/run` 或 UI「立即习惯体检」、斜杠 `/habit`。
- 状态：`GET /meta/habit`；报告目录 `outputs/habit_checks/`。
- LLM 蒸馏需 `HABIT_EVOLVE_ON_CHECK=1` 且 `AGENT_EVOLVE_LLM=1`。
