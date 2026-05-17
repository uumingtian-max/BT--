# 能力：进化蒸馏

Triggers: evolve,distill,进化,playbook,/agent/evolve,feature_evolution,feature evolution,feature-evolution,evolution,能力,进化蒸馏,蒸馏,自我进化,进化规则

---

**何时使用**：蒸馏规则、playbook 进化、`/agent/evolve` 时**必须**挂载。

## 执行步骤
1. `POST /agent/evolve/distill`：从行为库提炼规则；`GET /agent/playbook` 查看
2. 蒸馏结果写入前让用户确认，避免错误偏好固化

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。
- 未经用户确认把错误推断写入 playbook 或 learned 技能。

## ONYX 对接
- `POST /agent/evolve/distill` · `GET /agent/playbook`
- 需 `AGENT_EVOLVE_LLM=1` 才自动 LLM 蒸馏；习惯体检用 `HABIT_EVOLVE_ON_CHECK=1`

## 关联技能
- `feature_habit_pipeline`
- `memory_eval_consolidation`
- `skills_master_index`

## 自测用语（习惯体检 / 人工抽检）
- 从最近行为蒸馏一条 playbook
- 查看当前进化规则
