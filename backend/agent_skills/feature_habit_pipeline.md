# 习惯体检流水线（每天两次）

Triggers: 习惯体检,habit,每天两次,行为分析,自我扩展,learned_habit,定时体检,feature_habit_pipeline,feature habit pipeline,feature-habit-pipeline,habit pipeline,习惯体检流水线,/habit,习惯检查,早晚体检

---

**何时使用**：习惯体检、每天两次检测、行为分析、自我扩展、`/habit` 时**必须**挂载。

## 执行步骤
1. 默认 **本地 9:00 / 21:00** 自动执行（`HABIT_CHECK_HOURS`）；后端 `background_habit_loop` 负责到点触发
2. 每次流程：`/meta/doctor` → `infer_behavior_patterns` → 日报 → playbook 记忆 → 可选 `learned_habit_auto.md`
3. 手动：`POST /meta/habit/run` 或 UI「立即习惯体检」、斜杠 `/habit`
4. 状态：`GET /meta/habit`；报告目录 `outputs/habit_checks/`
5. LLM 蒸馏需 `HABIT_EVOLVE_ON_CHECK=1` 且 `AGENT_EVOLVE_LLM=1`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。
- 未经用户确认把错误推断写入 playbook 或 learned 技能。

## ONYX 对接
- `GET /meta/habit` · `POST /meta/habit/run` · 报告 `outputs/habit_checks/`
- 环境：`HABIT_CHECK_HOURS=9,21` · `HABIT_AUTO_SKILL=1`

## 关联技能
- `feature_evolution`
- `persistent_context`
- `onyx_ollama_ops`
- `tool_skill_authoring`
- `skills_master_index`

## 自测用语（习惯体检 / 人工抽检）
- 现在做一次习惯体检
- 习惯流水线状态
