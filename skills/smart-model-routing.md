# Skill: 智能模型路由（Smart Model Routing）

**核心理念：** 用最小的模型完成任务，只在必要时加载大模型  
**实现文件：** `backend/model_router.py`  
**显存占用（5090 示例）：** 四常驻约 14G + coder 按需 +8.9G

---

## 路由逻辑

```
用户输入
    │
    ├─ 代码关键词？ ────────────────────► deepseek-coder-v2:16b（复杂）
    │                                     qwen3.5:9b（简单脚本）
    ├─ 工具路由关键词？ ────────────────► functiongemma（0.3G）
    ├─ 推理/规划关键词？ ───────────────► deepseek-r1:7b
    └─ 其他（含快答）────────────────────► qwen3.5:9b（主脑）

向量嵌入（后台常驻）────────────────────► nomic-embed-text（0.3G）
```

---

## 使用方法

### 基础路由

```python
from model_router import select_model

model, reason = select_model("帮我写一个排序算法", mode="chat")
# → ("qwen3.5:9b", "code")   # 简单脚本走主脑

model, reason = select_model("重构这个 12 个文件的微服务架构", mode="chat")
# → ("deepseek-coder-v2:16b", "code")  # 复杂代码走 coder
```

### 获取特定角色的模型

```python
from model_router import get_model, get_embed_model, get_tool_router_model

embed   = get_embed_model()           # → "nomic-embed-text:latest"
router  = get_tool_router_model()     # → "functiongemma:latest"
default = get_model("AGENT_DEFAULT_MODEL")  # → "qwen3.5:9b"
```

### 路由诊断

```python
from model_router import routing_info

info = routing_info("分析这段代码的时间复杂度")
print(info["model"])   # deepseek-r1:7b
print(info["reason"])  # reasoning
print(info["model_map"])  # 所有模型的当前分配
```

---

## 环境变量覆盖

无需改代码，通过 `.env` 即可调整任意角色的模型：

```env
AGENT_DEFAULT_MODEL=qwen3.5:9b
FAST_MODEL=qwen3.5:9b
REASONING_MODEL=deepseek-r1:7b
CODE_MODEL=deepseek-coder-v2:16b
CODE_SIMPLE_MODEL=qwen3.5:9b
TASK_MODEL=qwen3.5:9b
EMBED_MODEL=nomic-embed-text:latest
AGENT_ROUTER_MODEL=functiongemma:latest
SMART_ROUTER_ENABLED=1              # 0 = 关闭路由，全走 AGENT_DEFAULT_MODEL
```

---

## 适配其他项目

`model_router.py` 是纯 Python，无外部依赖，可直接复制到任意 FastAPI / Ollama 项目中使用。

```bash
cp backend/model_router.py your_project/model_router.py
```
