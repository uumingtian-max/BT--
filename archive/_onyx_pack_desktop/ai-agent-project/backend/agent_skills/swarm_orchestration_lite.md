# 多 Agent / Swarm 轻量编排

Triggers: swarm,多代理群,并行,编排,总线,冲突,合并,ruflo,swarm_orchestration_lite,swarm orchestration lite,swarm-orchestration-lite,Agent,轻量编排,多代理,并行写盘

---

**何时使用**：用户意图与「多 Agent / Swarm 轻量编排」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. **单写者原则**：同一文件/同一配置段同一时刻只让一个「执行代理」修改，其他人只出 diff 建议
2. **交接包**：每个子任务输出必须含「输入假设 / 产出路径 / 未决问题」，便于下一节点接手
3. **合并策略**：先拉最新再应用 patch；冲突时列出冲突块与推荐人工决策点，不静默覆盖
4. **规模控制**：并行子任务数量与上下文上限挂钩；宁可串行减少返工
5. 无工具/无读取就声称「已完成」或编造文件内容
6. 把 `.env`、token、密钥写入聊天或记忆
7. （示例）用户会用自然语言提到「多 Agent / Swarm 轻量编排」相关任务
8. （示例）[skill:swarm_orchestration_lite] 请按本技能执行一步可验证操作

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「多 Agent / Swarm 轻量编排」相关的事
- [skill:swarm_orchestration_lite] 执行一步可验证操作
