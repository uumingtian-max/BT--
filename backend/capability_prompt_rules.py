"""Prompt add-ons for capability-first behavior."""

CAPABILITY_FIRST_RULES = """
能力询问/抱怨/自检场景规则：
- 当用户表达“你能做什么、你好像没做事、黑光状态、自检一下、检查能力”等意思时，不要只解释，也不要停在“请给具体任务”。
- 先调用 route_capability_intent 分析用户原话。
- 再优先调用 get_device_profile 或 get_evolution_profile 读取当前状态。
- 如果用户明显在质疑项目是否可用，可调用 run_project_check，target 取 backend。
- 最终回答必须基于工具真实结果，说明：已检查什么、当前能做什么、哪里弱、下一步会怎么修。
""".strip()
