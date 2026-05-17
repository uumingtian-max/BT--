# 工具：mcp_invoke

Triggers: mcp_invoke,MCP 桥接,/mcp/call,外部工具,tool_mcp_invoke,tool mcp invoke,tool-mcp-invoke,mcp invoke,工具,工具mcp invoke,mcp工具,调用mcp,外部mcp

---

**何时使用**：用户需要 **MCP 桥接调用**（工具 `mcp_invoke`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 先 `GET /mcp/status` 与 `/mcp/tools` 看已注册工具
2. `server` + `tool` + `arguments` 与 Cursor MCP 概念对齐；失败贴服务器返回错误
3. 不协助用 MCP 执行未授权远程控制或凭证窃取

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `GET /mcp/status` · `GET /mcp/tools` · `POST /mcp/call`

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用mcp invoke帮我做一件可验证的小事
- [skill:tool_mcp_invoke] 调用工具并给出证据
