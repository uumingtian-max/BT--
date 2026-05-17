# SQLite 运维剧本

Triggers: sqlite,wal,迁移,备份,behavior.db,sqlite_ops_playbook,sqlite ops playbook,sqlite-ops-playbook,运维剧本

---

**何时使用**：用户意图与「SQLite 运维剧本」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 库文件在 `backend/*.db`；查询用 `query_database` 只读
2. 备份：复制文件前停写或 WAL checkpoint；不擅自 DELETE 用户数据

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `query_database`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「SQLite 运维剧本」相关的事
- [skill:sqlite_ops_playbook] 执行一步可验证操作
