# 技能创作与质量（Skill Creator 精简版）

Triggers: 写技能,改技能,优化技能,提质,skill creator,触发词,技能质量,技能评测,undertrigger,技能包,authoring,meta/skills,tool_skill_authoring,tool skill authoring,tool-skill-authoring,skill authoring,技能创作与质量,Skill,Creator,精简版,skill_authoring,工具skill authoring

---

**何时使用**：用户要新建/改写/优化技能、触发不准、或说「提升技能质量/直接提质」时**必须**挂载。

## 执行步骤

1. **Capture Intent**：弄清技能让 Agent 做什么、何时触发、输出格式；从对话抽取步骤与用户纠正。
2. **Triggers**：中英 + 工具名 + 口语同义；略「主动」防 undertrigger（用户没点名技能但意图明显也要命中）。
3. **六段正文**：何时使用 / 执行步骤 / 避免 / ONYX 对接 / 关联技能 / 自测用语；单条 <500 行。
4. **渐进披露**：正文仅在命中时注入（`skill_pack` 约 2–4 条、2.4k–2.8k 字/条）；长文放 `knowledge-vault/`。
5. **可验证技能**：写 2–3 条自测用语；用 `[skill:stem]` 实测后再改。
6. **全库提质**：`python scripts/optimize-agent-skills-deep.py --force`
7. **同步索引**：重大变更更新 `skills_master_index` 与 README 计数（以 `/meta/skills` 为准）。

## 避免

- 一条技能包打天下（应拆 stem）；Triggers 过少或仅生僻英文。
- 把外仓 5000 行 SKILL 整文件塞进 `agent_skills/`（撑爆上下文）。
- 手改 `learned_habit_auto.md`（由 habit_pipeline 覆盖）。

## ONYX 对接

- 目录：`backend/agent_skills/*.md` · `GET /meta/skills`
- 强制：`[skill:stem]` · `/skill <id>` · `AGENT_SKILL_PACK=1`

## 关联技能

- `skills_master_index`
- `agent_forced_skill`
- `feature_habit_pipeline`
- `feature_evolution`

## 自测用语（习惯体检 / 人工抽检）

- 帮我把习惯体检写得更易触发
- 现在有多少技能
- 全库提质命令是什么
