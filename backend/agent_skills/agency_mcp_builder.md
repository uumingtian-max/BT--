# MCP 工具开发（agency MCP Builder）

Triggers: MCP,建MCP,工具描述,mcp_invoke,agency_mcp_builder,agency mcp builder,Model Context Protocol,Cursor MCP,扩展工具,agency-mcp-builder,工具开发,agency,Builder

---

**何时使用**：为 Agent 新增/改进 MCP 或 `mcp_invoke` 集成。来源 agency-agents `specialized-mcp-builder`。

## 执行步骤

1. 明确 agent 缺什么能力；能用一个清晰工具解决就不要堆参数
2. 命名 `动词_名词`；描述写**何时调用**
3. 参数 schema + 默认值；返回 JSON 或短 markdown
4. 错误：可行动文案；不把栈抛给模型；密钥仅环境变量
5. 用真实对话试：是否常选错工具/传错参

## 避免

- 一个 `mode` 参数包办增删改查
- 硬编码 API Key 到代码或技能

## ONYX 对接

- 工具 `mcp_invoke` · `docs/TOOLS.md`
- Cursor 侧 MCP 描述符：`mcps/<server>/tools/*.json`

## 自测用语

- [skill:agency_mcp_builder] 设计一个查 /meta/skills 的 MCP 工具
- 优化现有工具 description 让模型少误调
