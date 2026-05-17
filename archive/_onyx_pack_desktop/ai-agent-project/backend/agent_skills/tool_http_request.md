# 工具：http_request

Triggers: http_request,REST,API 调用,webhook 测试,fetch,tool_http_request,tool http request,tool-http-request,http request,工具,调接口,请求api,curl,post请求,工具http request,测试接口

---

**何时使用**：用户需要 **HTTP/REST 调用**（工具 `http_request`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 默认 GET；写操作需用户确认目标与 body
2. 超时用 `timeout_sec`；响应过大时摘要 status + 关键字段，勿全文塞满上下文
3. 内网/本机 API 优先（如 `/meta/*`、`/agent/*`）而非臆造外网端点

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具 `http_request`；本机优先 `http://127.0.0.1:8000/meta/*`

## 关联技能
- `api_contract_design`
- `fastapi_route_debug`
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用 http_request 测一下 GET /meta/info
- 调本地 8000 的健康检查
