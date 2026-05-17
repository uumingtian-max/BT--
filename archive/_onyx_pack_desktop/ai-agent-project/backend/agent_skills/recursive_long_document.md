# 超长文档：递归摘要（RLM 思路）

Triggers: rlm,recursive language,超长文档,百万字,上下文不够,整本书,100x context,zircote,分块读,大 pdf

对标 **Recursive Language Model**：大材料不一次性塞进模型，而是**分块 → 局部结论 → 递归合并**。

**推荐工具链**：

1. `read_file` 分段（按章节/行范围）或 `local_scrape_url` 抓取可访问 HTML/PDF 文本。
2. 每块输出：**事实摘录** + **未决问题**；禁止跨块臆造页码/条款。
3. 用 `notebook_ingest` 把稳定结论写入知识库，便于后续 `local_search`。
4. 最终回答只基于已读块合并；仍不确定处显式写「未读到原文 X 段」。
5. 块数过多时：先 `run_parallel_subagents` 并行摘要（每块独立 prompt），再单轮合并（注意 `swarm_orchestration_lite` 单写者原则）。

**禁止**：声称已读完整文件却未调用 `read_file`；禁止把合并摘要当成逐字引用。
