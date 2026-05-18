# 社交内容转技能

Triggers: x.com,twitter,推文,X链接,社交内容,技能接入,接进去技能,看到这个,学一下这个,知识转技能,social source,tweet to skill,social_source_to_skill,social source to skill,social-source-to-skill,社交内容转技能

---

**何时使用**：用户意图与「社交内容转技能」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 先获取内容
2. 优先使用 local_scrape_url、browser_navigate 或 web_search 获取公开正文
3. 如果页面因为登录、权限或访问限制不可读，明确告诉用户“当前没拿到原文”，让用户发截图或复制正文
4. 不要根据 URL 猜内容；没拿到正文就只能先建待接入记录和通用模板
5. 判断接入类型
6. 如果内容是操作方法、提示词、工作流、技巧：接成 backend/agent_skills/*.md 技能
7. 如果内容是可自动执行的动作：先写工具需求文档，再评估是否新增后端工具
8. 如果内容是资料、名单、案例、观点：优先用 notebook_ingest 写入知识库

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「社交内容转技能」相关的事
- [skill:social_source_to_skill] 执行一步可验证操作
