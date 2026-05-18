# 任意内容转笔记工作流

Triggers: NotebookLM,anything to notebook,任意内容,转笔记,生成播客,生成PPT,思维导图,生成Quiz,深度分析,多源内容,微信文章,YouTube,PDF转笔记,EPUB,文档转报告,anything_to_notebook_workflow,anything to notebook workflow,anything-to-notebook-workflow,任意内容转笔记工作流

---

**何时使用**：用户意图与「任意内容转笔记工作流」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. YouTube：优先作为 URL 源交给 NotebookLM 或本地网页/字幕能力处理，不主动下载受限内容
2. 普通公开网页：使用 `local_scrape_url`、`browser_navigate` 或 `web_search` 获取正文
3. X/Twitter：先尝试公开页面或搜索；若登录墙不可读，让用户发截图或正文
4. PDF / Markdown / TXT / Office / EPUB：优先读取本地文件；必要时转成 Markdown/TXT 再进入知识库
5. 图片 / 扫描件：如果项目已有 OCR 能力则提取文字；否则作为待接入能力记录
6. 音频 / 播客：如果已有转写能力则转文本；否则登记为“转写工具需求”
7. 搜索关键词：先搜索并汇总公开来源，再生成报告或笔记
8. 确认用户输入类型：URL、本地路径、文本、搜索词、混合多源

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `local_scrape_url`
- 工具/配置 `browser_navigate`
- 工具/配置 `web_search`
- 工具/配置 `notebook_ingest`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「任意内容转笔记工作流」相关的事
- [skill:anything_to_notebook_workflow] 执行一步可验证操作
