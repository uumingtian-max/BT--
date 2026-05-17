# 能力：网关入站

Triggers: gateway,telegram,inbound,webhook 入站,feature_gateway,feature gateway,feature-gateway,能力,网关入站,telegram bot,接webhook,消息入站

---

**何时使用**：用户涉及 ONYX **消息网关入站**（`feature_gateway`）或相关 API/面板/斜杠命令时**应**挂载；系统体检 `/meta/doctor` 失败也可附带本技能。

## 执行步骤
1. `GET /gateway/status`；`POST /gateway/inbound` / `telegram` 需配置与密钥
2. 不把用户 `.env` 密钥写入记忆或公开回复

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `GET /gateway/status` · `POST /gateway/inbound`

## 关联技能
- `skills_master_index`

## 自测用语（习惯体检 / 人工抽检）
- 查一下gateway功能状态
- [skill:feature_gateway] 走对应 API 试一步
