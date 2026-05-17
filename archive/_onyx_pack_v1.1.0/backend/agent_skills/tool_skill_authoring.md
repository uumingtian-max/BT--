# 技能创作与质量（Skill Creator 精简版）

Triggers: 写技能,改技能,优化技能,提质,skill creator,触发词,技能质量,技能评测,undertrigger,技能包,authoring,meta/skills,tool_skill_authoring,tool skill authoring,tool-skill-authoring,skill authoring,技能创作与质量,Skill,Creator,精简版,skill_authoring,工具skill authoring

---

**何时使用**：用户要新建/改写/优化技能、触发词不准、或问「提升技能质量」时**必须**挂载。

## 执行步骤
1. **Capture Intent**：弄清技能让 Agent 做什么、何时触发、输出格式；从对话抽取步骤与用户纠正
2. **Triggers**：中英 + 工具名 + 口语同义；略「主动」防 undertrigger（用户没点名技能但意图明显也要命中）
3. **六段正文**：何时使用 / 执行步骤 / 避免 / ONYX 对接 / 关联技能 / 自测用语；单条 <500 行
4. **渐进披露**：正文仅在命中时注入（`skill_pack` 约 2–4 条、2.4k–2.8k 字/条）；长文放 `knowledge-vault/`
5. **可验证技能**：写 2–3 条自测用语；用 `[skill:stem]` 实测后再改
6. **全库提质**：`python scripts/optimize-agent-skills-deep.py --force`
7. **同步索引**：重大变更更新 `skills_master_index` 与 README 计数（以 `/meta/skills` 为准）
8. 一条技能包打天下（应拆 stem）；Triggers 过少或仅生僻英文

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `skill_pack`
- API /meta/skills
- 工具/配置 `skills_master_index`
- 工具/配置 `agent_forced_skill`
- 工具/配置 `feature_habit_pipeline`
- 工具/配置 `feature_evolution`

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用skill authoring帮我做一件可验证的小事
- [skill:tool_skill_authoring] 调用工具并给出证据
