# 工具：local_search 与抓取

Triggers: local_search,local_scrape,本地搜索,知识库,全文检索,tool_local_search,tool local search,tool-local-search,local search,工具,与抓取,搜本地,搜项目,全文搜,vault,工具local search

---

**何时使用**：用户需要 **本机/知识库全文检索**（工具 `local_search`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. `local_search`：优先查本机索引与 `knowledge-vault`；长材料配合 `recursive_long_document` 分块
2. `local_scrape_url`：单 URL 正文抽取，设 `max_chars` 防撑爆上下文
3. 多源结论需标注路径/文件名，禁止编造未读文件内容

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。
- 将内网/隐私/凭证发到外网检索。

## ONYX 对接
- 工具/配置 `local_search`
- 工具/配置 `recursive_long_document`
- 工具/配置 `local_scrape_url`
- 工具/配置 `max_chars`

## 关联技能
- `knowledge_vault_ingest`
- `recursive_long_document`
- `tool_web_search`
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用local search帮我做一件可验证的小事
- [skill:tool_local_search] 调用工具并给出证据
