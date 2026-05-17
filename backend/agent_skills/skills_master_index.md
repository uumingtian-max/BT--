# 技能总目录（本仓库）

Triggers: 技能库,全部技能,有多少技能,skill catalog,skills list,meta/skills,技能太少,技能包,skill pack,多少个技能

---

**何时使用**：用户问技能数量、分类、是否被隐藏、或觉得「技能太少/不生效」时，**先**用本技能核对事实再回答。

## 执行步骤

1. 调用 `GET /meta/skills` → `count` 与 `skills[]`（与 `backend/agent_skills/*.md` 一一对应，**无 UI 隐藏过滤**）。
2. 说明自动挂载规则：用户消息命中 `Triggers:`；强挂载 `[skill:stem]` 或 `/skill <id>`。
3. 按分类指路（见下表）；需要写/改技能时用 `tool_skill_authoring`。
4. 批量提质：`python scripts/optimize-agent-skills-deep.py`（Skill Creator 结构：何时使用/步骤/避免/自测）。

## 分类

| 类型 | 前缀/示例 | 说明 |
|------|-----------|------|
| 元技能 | `tool_skill_authoring`, `skills_master_index` | 写技能、查目录 |
| 趋势/社区 | `github_trending_developers`, `weekly_trend_map`, `monthly_trend_map`, `trend_playbook_snapshot` | 热榜对标 |
| 工具专精 | `tool_*` | 每个 Agent 工具一条 playbook |
| 能力/API | `feature_*` | 记忆、定时、网关、观测、习惯体检等 |
| 工程/本应用 | `onyx_*`, `fastapi_route_debug` | ONYX 前后端与运维 |
| 自动学习 | `learned_habit_auto` | **由 habit_pipeline 覆盖**，勿手改 |

## 避免

- 声称技能数量却不查 `/meta/skills`。
- 把 Cursor 外仓技能说成「已内置在 ONYX」；外仓仅主题对照（见 `claude_skills_domain_map`）。

## ONYX 对接

- `GET /meta/skills` · `AGENT_SKILL_PACK=1` · 技能目录 `backend/agent_skills/`

## 关联技能

- `tool_skill_authoring`
- `agent_forced_skill`
- `claude_skills_domain_map`
- `github_trending_developers`

## 自测用语（习惯体检 / 人工抽检）

- 你现在有多少技能，有没有被藏起来
- 列出和浏览器相关的技能 id
- 帮我优化 habit 相关技能的触发词
