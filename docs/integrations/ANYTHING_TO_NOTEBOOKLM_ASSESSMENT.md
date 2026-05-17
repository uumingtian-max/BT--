# Anything → NotebookLM 集成评估

参考项目：`joeseesun/qiaomu-anything-to-notebooklm`

## 参考项目能力概览

该项目定位为 Claude Code Skill，用自然语言把多源内容转换成 NotebookLM 可处理的素材，并进一步生成播客、PPT、思维导图、Quiz、报告等结果。

可借鉴方向：

- 多源内容识别：网页、YouTube、播客、X/Twitter、PDF、EPUB、Markdown、Office 文档、图片、音频、ZIP、搜索关键词。
- 意图映射：生成播客、PPT、思维导图、Quiz、报告、闪卡、深度分析。
- 深度分析：多轮递进提问，把长材料压缩成结构化洞察。
- 文件转换：借鉴 markitdown / OCR / 音频转写等通用处理思路。
- NotebookLM 工作流：创建 notebook、添加 source、生成 artifact、下载结果。

## 不接入的部分

BKLT 黑光不接入以下能力：

- 绕过登录、订阅、付费墙、权限或平台访问限制。
- 使用伪装 UA、伪装来源、存档站规避访问控制等策略。
- 自动抓取用户无权访问的内容。
- 自动执行资金、钱包、账户授权、交易或合约相关动作。

这些内容只允许作为“风险识别 / 尽调 / 合规提醒”处理。

## 建议接入路线

### Phase 1：技能层接入（已完成）

新增 BKLT 技能：

- `backend/agent_skills/anything_to_notebook_workflow.md`

作用：让 Agent 能识别“任意内容 → 笔记 / 报告 / PPT / 脑图 / Quiz / NotebookLM”的用户意图，并按公开内容、用户本地文件、用户提供文本进行处理。

### Phase 2：本地知识库优先

在 NotebookLM 工具未正式接入前，优先使用 BKLT 现有能力：

- `local_scrape_url` / `browser_navigate`：获取公开网页正文。
- `read_file`：读取本地文件。
- `notebook_ingest`：写入 BKLT 本地知识库。
- `notebook_synthesize`：把长材料整理成结构化中文笔记。
- `text_to_speech`：把摘要或脚本转语音。
- `generate_video` / `generate_image`：后续用于视频或图像输出。

### Phase 3：新增 NotebookLM 工具（待评估）

如果用户明确需要 NotebookLM，可新增后端工具：

- `notebooklm_status`：检查 CLI/认证状态。
- `notebooklm_create`：创建 notebook。
- `notebooklm_add_source`：添加 URL 或文本文件 source。
- `notebooklm_generate`：生成 audio / slide-deck / mind-map / quiz / report。
- `notebooklm_download_artifact`：下载生成结果到 `outputs/notebooklm/`。

风险等级建议：

- `notebooklm_status`：safe。
- `notebooklm_create` / `notebooklm_add_source`：confirm，因为会上传内容到外部服务。
- `notebooklm_generate` / `notebooklm_download_artifact`：confirm。

### Phase 4：前端可视化

在自动化面板加入“内容处理流水线”：

```text
输入识别 → 内容获取 → 清洗转换 → 入库/上传 → 生成结果 → 下载/预览
```

前端展示：

- 输入类型。
- 处理步骤。
- 来源列表。
- 风险提示。
- 输出文件。

## 与 BKLT 当前定位的关系

这个方向适合 BKLT 黑光，因为它能把“链接、文件、视频、播客、文章”变成可复用知识资产，并通过自动化面板把过程可视化。

但 BKLT 必须坚持本地优先、安全分层和少确认规则：

- 本地处理优先。
- 上传 NotebookLM 等外部服务前必须提示确认。
- 高风险来源或敏感内容只做安全分析，不自动执行外部动作。

## 下一步

1. 使用新技能处理用户提供的 GitHub / X / 文章链接。
2. 把常见输出先落成本地 Markdown 报告、PPT 大纲、播客脚本和 Quiz。
3. 确认是否需要真实 NotebookLM CLI 集成；如果需要，再新增工具注册表和后端路由。
