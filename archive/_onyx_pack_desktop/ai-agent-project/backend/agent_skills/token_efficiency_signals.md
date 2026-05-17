# Token 节制与信号密度

Triggers: 长日志,输出,摘要,压缩,token,上下文,性能,deepseek,tui,终端,token_efficiency_signals,token efficiency signals,token-efficiency-signals,节制与信号密度,token太多,压缩上下文,太长

---

**何时使用**：用户意图与「Token 节制与信号密度」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 先给**结论与决策**，再给支撑材料；支撑材料用条目而非长段落
2. 处理长文本：保留首尾与关键报错行，中间用「…省略 N 行…」并说明省略原因
3. 同一提示里不要重复粘贴用户整段话；引用时用最短必要片段
4. 多轮对话中新增信息增量叙述，不复述已确认的事实
5. 无工具/无读取就声称「已完成」或编造文件内容
6. 把 `.env`、token、密钥写入聊天或记忆
7. （示例）用户会用自然语言提到「Token 节制与信号密度」相关任务
8. （示例）[skill:token_efficiency_signals] 请按本技能执行一步可验证操作

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「Token 节制与信号密度」相关的事
- [skill:token_efficiency_signals] 执行一步可验证操作
