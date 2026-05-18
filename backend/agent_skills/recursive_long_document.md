# 超长文档：递归摘要（RLM 思路）

Triggers: rlm,recursive language,超长文档,百万字,上下文不够,整本书,100x context,zircote,分块读,大 pdf,recursive_long_document,recursive long document,recursive-long-document,递归摘要,思路,pdf太长,文档太大,读不完

---

**何时使用**：用户意图与「超长文档：递归摘要（RLM 思路）」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. `read_file` 分段（按章节/行范围）或 `local_scrape_url` 抓取可访问 HTML/PDF 文本
2. 每块输出：**事实摘录** + **未决问题**；禁止跨块臆造页码/条款
3. 用 `notebook_ingest` 把稳定结论写入知识库，便于后续 `local_search`
4. 最终回答只基于已读块合并；仍不确定处显式写「未读到原文 X 段」
5. 块数过多时：先 `run_parallel_subagents` 并行摘要（每块独立 prompt），再单轮合并（注意 `swarm_orchestration_lite` 单写者原则）

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `read_file`
- 工具/配置 `local_scrape_url`
- 工具/配置 `notebook_ingest`
- 工具/配置 `local_search`
- 工具/配置 `run_parallel_subagents`
- 工具/配置 `swarm_orchestration_lite`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「超长文档：递归摘要（RLM 思路）」相关的事
- [skill:recursive_long_document] 执行一步可验证操作
