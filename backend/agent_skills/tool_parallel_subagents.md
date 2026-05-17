# 工具：run_parallel_subagents

Triggers: run_parallel_subagents,并行子代理,parallel agents,tool_parallel_subagents,tool parallel subagents,tool-parallel-subagents,parallel subagents,工具,同时查,并行分析,多个文件一起,工具parallel subagents,parallel_subagents

---

**何时使用**：用户需要 **并行只读子代理**（工具 `parallel_subagents`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 用于**只读**或**分区明确**的子问题（多文件摘要、多 URL 对比）
2. 合并结果时去重矛盾陈述；写入操作由主 Agent 串行执行
3. 超长文档分块策略见 `recursive_long_document`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `recursive_long_document`

## 关联技能
- `recursive_long_document`
- `swarm_orchestration_lite`
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用parallel subagents帮我做一件可验证的小事
- [skill:tool_parallel_subagents] 调用工具并给出证据
