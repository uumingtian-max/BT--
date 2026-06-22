# BT黑光 Bug修复任务说明

> 本文件供其他 AI 代理执行部署任务。所有代码改动已在分支 `claude/black-construction-site-8qj5sz` 完成并推送，只需登录服务器执行以下步骤。

---

## 背景

BT黑光后端使用 `inferaichat.com` 作为 Claude API 代理（`openai_compatible` 模式）。该代理有时将 Claude API 原生 `tool_use` 内容块透传到响应，导致两个 bug：

1. **连接超时无重试**：外部 API 抖动直接报错，pool timeout 仅 5s 导致并发时频繁崩
2. **`tool_use_id` 校验错误**：代理透传的 tool_use 块被存入 `chat.db`，下次带历史请求时触发 `invalid_request_error: unexpected tool_use_id found in tool_result blocks`

---

## 已完成的代码改动（4 次 commit）

### commit 1 — `backend/llm_client.py`：连接超时 + 重试
- `pool` timeout 从 5s 改为 30s
- `openai_compatible` 三条路径（sync/async/stream）加重试：ConnectError/ConnectTimeout/PoolTimeout/RemoteProtocolError 最多重试 3 次（退避 1→3→8s）
- ReadTimeout 转为友好中文提示
- `chat_complete_async` 的 timeout 改为 `httpx.Timeout` 对象（read=ollama_timeout_sec）

### commit 2 — `backend/llm_client.py`：tool_use_id 校验错误
- 新增 `_extract_text_from_content()`：从数组 content 中提取纯文本，丢弃 tool_use/tool_result 块
- 新增 `_sanitize_content_for_api()`：发送前净化 message.content，过滤 tool 块，保留媒体块
- `_openai_messages()` 对每条消息净化；空 assistant 消息跳过
- `_openai_non_stream_content()` 和流式 delta 解析均使用 `_extract_text_from_content`

### commit 3 — `backend/chat.py`：历史加载净化 + 存量清理接口
- 新增 `_strip_tool_blocks_from_content()`：加载历史时对 JSON 数组格式 content 探测并提取文本
- `get_history()` 对每条记录应用净化
- 新增 `POST /maintenance/strip-tool-blocks` 端点：一次性清理 DB 里已有脏消息

### commit 4 — `.gitignore`
- 新增 `onyx-pytest/`（pytest 生成的临时目录）

---

## 部署步骤

在服务器上按顺序执行：

```bash
# 1. 进入项目目录（路径按实际情况调整）
cd /root/BT--

# 2. 拉取修复代码
git pull origin claude/black-construction-site-8qj5sz

# 3. 重启后端（按实际启动方式调整）
pkill -f "uvicorn\|python.*main" 2>/dev/null
sleep 2
cd /root/BT--/backend
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/bt-backend.log 2>&1 &
sleep 3

# 4. 清理 DB 里已有的脏消息（只需执行一次）
curl -X POST http://localhost:8000/maintenance/strip-tool-blocks
# 预期返回：{"ok":true,"fixed":N}
```

---

## 验证

执行完后，在 BT 应用里正常发一条消息，不再出现以下错误即为成功：

```
Provider error: [invalid_request_error] messages.0.content.1: unexpected `tool_use_id` found in `tool_result` blocks
```

---

## 涉及文件

| 文件 | 改动类型 |
|------|---------|
| `backend/llm_client.py` | Bug修复（超时/重试/tool块净化） |
| `backend/chat.py` | Bug修复（历史净化/清理接口） |
| `.gitignore` | 新增忽略规则 |

分支：`claude/black-construction-site-8qj5sz`  
仓库：`uumingtian-max/BT--`
