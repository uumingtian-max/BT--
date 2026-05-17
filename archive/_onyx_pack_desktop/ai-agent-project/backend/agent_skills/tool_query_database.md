# 工具：query_database

Triggers: query_database,sqlite,SQL,查库,memory.db,tool_query_database,tool query database,tool-query-database,query database,工具,工具query database,查数据库,sql查询

---

**何时使用**：用户需要 **SQLite 只读查询**（工具 `query_database`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 仅 **SELECT** 类只读查询；禁止 DROP/DELETE 除非用户明确要求且路径确认
2. 常用库：`memory.db`、`workflow.db`、`scheduler.db` 等（见 `/meta/doctor`）
3. 结果行数用 `limit` 控制；敏感列（token）勿回显到聊天

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具 `query_database`；库在 `backend/*.db`

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用query database帮我做一件可验证的小事
- [skill:tool_query_database] 调用工具并给出证据
