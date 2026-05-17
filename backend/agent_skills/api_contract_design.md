# API 契约设计

Triggers: openapi,契约,错误码,版本,REST 设计,api_contract_design,api contract design,api-contract-design,API,契约设计

---

**何时使用**：用户意图与「API 契约设计」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 先冻结请求/响应 schema 与错误码表，再实现 FastAPI 路由
2. 破坏性变更升版本或加兼容字段；文档与 `meta_routes` 对齐

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `meta_routes`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「API 契约设计」相关的事
- [skill:api_contract_design] 执行一步可验证操作
