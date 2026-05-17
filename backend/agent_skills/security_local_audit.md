# 本地安全审计清单

Triggers: 安全审计,secrets,.env,凭证,渗透,security_local_audit,security local audit,security-local-audit,本地安全审计清单,扫描密钥,泄露,.env提交

---

**何时使用**：用户意图与「本地安全审计清单」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 扫描勿将 `.env`、token 提交或写入记忆；`run_project_check` + 人工 review
2. 拒绝未授权渗透、木马、凭证窃取；合法自查限于用户自有项目

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `run_project_check`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「本地安全审计清单」相关的事
- [skill:security_local_audit] 执行一步可验证操作
