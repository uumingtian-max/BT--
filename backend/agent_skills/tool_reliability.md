# 工具可靠性与诚实性

Triggers: 工具,搜索,文件,执行,代码,python,桌面,目录,tool_reliability,tool reliability,tool-reliability,reliability,工具可靠性与诚实性,工具reliability

---

**何时使用**：任何工具调用前后需要诚实性/核验约束时**可**叠加挂载。

## 执行步骤
1. 声称「已完成」前必须有工具或本地可核验产物；否则明确说未完成
2. 搜索/抓取结果可能过时：结论中标注信息来源与时间敏感度
3. `execute_python` 仅用于短脚本验证；长任务改为多步小脚本并检查副作用
4. 无工具/无读取就声称「已完成」或编造文件内容
5. 把 `.env`、token、密钥写入聊天或记忆
6. 工具 `execute_python`
7. `tool_reliability`
8. `trust_and_decline`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `execute_python`
- 工具/配置 `tool_reliability`
- 工具/配置 `trust_and_decline`

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用reliability帮我做一件可验证的小事
- [skill:tool_reliability] 调用工具并给出证据
