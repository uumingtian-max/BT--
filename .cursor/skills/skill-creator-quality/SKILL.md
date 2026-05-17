---
name: skill-creator-quality
description: >-
  ONYX 项目内写/改技能。用户说 帮我把这个流程写成 Cursor 技能、优化 SKILL 触发词、
  技能老是不自动用上 时使用。全局完整版见 ~/.cursor/skills/skill-creator-quality/SKILL.md
---

# Skill Creator（ONYX 项目）

完整流程：**`C:\Users\ROG\.cursor\skills\skill-creator-quality\SKILL.md`**

## 本仓库两种技能格式

| 类型 | 路径 | 触发 |
|------|------|------|
| Cursor | `.cursor/skills/<name>/SKILL.md` | YAML `description` |
| ONYX Agent | `backend/agent_skills/<stem>.md` | `Triggers:` 行 |

## 快捷命令

```bash
python scripts/optimize-agent-skills-deep.py --force
```

清单：`GET http://127.0.0.1:8000/meta/skills` · 规则：`.cursor/rules/agent-skill-quality.mdc`

## 三句话对应动作

1. **写成技能** → 从对话抽流程 → 选 Cursor 或 ONYX 路径 → 写 description/Triggers + 自测句  
2. **优化触发词** → 先改 description/Triggers，再对齐「何时使用」  
3. **不自动用上** → 读全局 `references/fix-undertrigger.md` → 改 description → 新对话自测  
