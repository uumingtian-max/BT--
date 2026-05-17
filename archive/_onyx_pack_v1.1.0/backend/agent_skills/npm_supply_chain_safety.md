# npm 供应链安全

Triggers: npm audit,供应链,依赖漏洞,typosquat,postinstall,npm_supply_chain_safety,npm supply chain safety,npm-supply-chain-safety,npm,供应链安全

---

**何时使用**：用户意图与「npm 供应链安全」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 用 `run_project_check` target=frontend；建议用户本地 `npm audit`
2. 拒绝：恶意 postinstall、凭证回传、依赖投毒协助
3. 升级依赖时说明 breaking change 风险，不盲目 `@latest`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `run_project_check`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「npm 供应链安全」相关的事
- [skill:npm_supply_chain_safety] 执行一步可验证操作
