# WorldMonitor 风格观测

Triggers: worldmonitor,全球面板,新闻态势,worldmonitor_observe,worldmonitor observe,worldmonitor-observe,风格观测

---

**何时使用**：用户意图与「WorldMonitor 风格观测」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 用 `/observe/*` 与本机采样；不编造实时战报或股价
2. 与 `situational_intel_observe` 一致：标注数据来源与延迟

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- API /observe/*
- 工具/配置 `situational_intel_observe`

## 关联技能
- `situational_intel_observe`
- `feature_observe`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「WorldMonitor 风格观测」相关的事
- [skill:worldmonitor_observe] 执行一步可验证操作
