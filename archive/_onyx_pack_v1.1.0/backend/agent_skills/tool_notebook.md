# 工具：notebook 摄取与综合

Triggers: notebook_ingest,notebook_synthesize,笔记本,资料汇总,tool_notebook,tool notebook,tool-notebook,notebook,工具,摄取与综合,工具notebook,整理笔记

---

**何时使用**：用户需要 **笔记本灌入与综合**（工具 `notebook`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. `notebook_ingest`：批量灌入片段；`notebook_synthesize`：生成结构化摘要
2. 输出保留来源标签；科研场景叠加 `academic_research_pipeline`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `notebook_ingest`
- 工具/配置 `notebook_synthesize`
- 工具/配置 `academic_research_pipeline`

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用notebook帮我做一件可验证的小事
- [skill:tool_notebook] 调用工具并给出证据
