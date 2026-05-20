# Skill: 习惯体检（Habit Health Check）

**适用场景：** 定期检查用户行为模式，生成结构化体检报告，并根据偏差自动更新技能包  
**推荐模型：** `TASK_MODEL`（默认 `qwen3.5:9b` 或 `granite4:3b`）  
**触发方式：** 定时（`HABIT_CHECK_HOURS`）或用户主动发起

---

## 技能描述

观察用户在对话、任务执行和工具使用中的行为模式，与历史基准对比，
输出结构化健康报告，并决定是否更新 `learned_habit_auto.md`。

---

## 系统提示词模板

```
你是 BT（黑光）的习惯体检模块。
当前时间：{datetime}
用户行为摘要（最近 {window} 天）：
{behavior_summary}

历史基准：
{baseline_snapshot}

请输出以下 JSON 结构，不要添加任何额外文字：
{
  "overall_score": 0-100,
  "dimensions": {
    "task_completion": {"score": 0-100, "trend": "up|stable|down", "note": ""},
    "tool_usage": {"score": 0-100, "trend": "up|stable|down", "note": ""},
    "response_time": {"score": 0-100, "trend": "up|stable|down", "note": ""},
    "memory_utilization": {"score": 0-100, "trend": "up|stable|down", "note": ""}
  },
  "top_insights": ["insight1", "insight2", "insight3"],
  "update_skill_pack": true|false,
  "skill_pack_delta": "如果 update_skill_pack=true，描述需要更新的内容"
}
```

---

## 调用示例

```python
from model_router import get_model
from llm_client import chat_complete_async

model = get_model("TASK_MODEL")   # → qwen3.5:9b

report = await chat_complete_async(
    [
        {"role": "system", "content": HABIT_CHECK_PROMPT},
        {"role": "user", "content": "执行体检"},
    ],
    model,
    temperature=0.1,
)
```

---

## 输出格式说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `overall_score` | int | 综合健康分（0-100）|
| `dimensions` | object | 四个维度分项评分 |
| `top_insights` | list[str] | 最重要的 3 条洞察 |
| `update_skill_pack` | bool | 是否需要更新技能包 |
| `skill_pack_delta` | str | 技能包变更说明 |

---

## 相关文件

- `backend/habit_pipeline.py` — 体检流水线实现
- `backend/scheduler_runner.py` — 定时触发逻辑
- `backend/agent_skills/learned_habit_auto.md` — 自动更新的习惯记录（gitignore）
