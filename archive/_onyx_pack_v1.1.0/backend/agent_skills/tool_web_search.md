# 工具：web_search

Triggers: web_search,联网搜索,duckduckgo,ddg,外网查,tool_web_search,tool web search,tool-web-search,web search,工具,上网查,查一下,网上搜,搜索一下,外网资料,工具web search,百度

---

**何时使用**：用户需要 **联网检索（DuckDuckGo）**（工具 `web_search`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 用于**可公开检索**的事实；敏感/内网数据勿走外网
2. 返回可能过时：结论写「检索时间敏感」并建议二次 `local_search` 交叉
3. 与 `local_search` 分工：外网广度 vs 本机/已索引深度

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。
- 将内网/隐私/凭证发到外网检索。

## ONYX 对接
- 工具/配置 `local_search`

## 关联技能
- `tool_local_search`
- `local_deep_research`
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 帮我上网查一下某库的最新稳定版
- 外网搜这个 CVE 什么意思
