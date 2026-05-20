# Skill: 持久记忆（Persistent Memory）

**核心理念：** Agent 不是无状态工具，而是随每次会话持续成长的伙伴  
**实现文件：** `backend/memory_store.py` · `backend/skill_pack.py` · `backend/self_evolve.py`

---

## 记忆层次

```
会话记忆（ephemeral）
    本次对话的完整上下文，会话结束后压缩摘要写入下一层

长期记忆（persistent）
    SQLite + FTS5 + 可选向量索引（nomic-embed-text）
    存储：事实、偏好、历史摘要、习惯模式
    召回：用户输入 → search_memories → top-k 注入 system prompt

技能包（skill pack）
    Markdown 文件，Agent 和人类均可读写
    存储：操作 SOP、用户专属指令、习惯体检结果
    位置：backend/agent_skills/（内置）+ 本机生成 learned_habit_auto.md

进化记录（evolution log）
    每次 Agent 执行后，记录哪些技能提升了、哪些需要修正
    由 self_evolve.py 异步写入，不阻塞主流程
```

---

## 写入记忆

```python
from memory_store import store_memory, remember_from_message

# 存储一条事实
store_memory(
    "用户偏好在早上 9 点执行体检报告",
    source_session_id="agent",
    source_role="user",
)

# 从用户消息自动提取可记忆片段
remember_from_message("session-1", "user", "记住：我习惯用 qwen3.5:9b 做主模型")
```

## 召回记忆

```python
from memory_store import search_memories, build_memory_context

# 语义 / 关键词召回
hits = search_memories("用户的工作习惯", limit=5)

# 直接注入 Agent system prompt 的文本块
context = build_memory_context("帮我总结最近项目在忙什么")
```

---

## 技能包自动更新

习惯体检模块（`habit_pipeline.py`）检测到行为变化时，自动调用 `self_evolve.py` 更新技能包：

```python
# self_evolve.py 会：
# 1. 读取当前 learned_habit_auto.md
# 2. 用 REASONING_MODEL 分析差异
# 3. 生成 diff 写回文件
# 4. 记录变更日志到 evolution log
```

---

## 与 Hermes Agent 的区别

| 特性 | BT（黑光）| Hermes Agent |
|------|-----------|--------------|
| 记忆存储 | 本机 SQLite + 文件 | 云端 |
| 隐私 | 数据不离本机 | 需信任服务商 |
| 技能扩展 | Markdown 文件，任何编辑器 | 官方平台 |
| 模型 | 自选本地模型 | 绑定官方模型 |
| 成本 | 一次性硬件 | 按量计费 |

---

## 相关文件

- `backend/memory_store.py` — 读写 API
- `backend/context_pack.py` — 上下文压缩与注入
- `backend/self_evolve.py` — 自动进化逻辑
- `backend/agent_skills/learned_habit_auto.md` — 自动习惯记录（本机生成，gitignore）
