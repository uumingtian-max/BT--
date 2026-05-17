# 能力：Telegraf 指标导出

Triggers: telegraf,prometheus,metrics,快照,/telegraf,feature_telegraf,feature telegraf,feature-telegraf,能力,指标导出

---

**何时使用**：用户涉及 ONYX **Prometheus 指标**（`feature_telegraf`）或相关 API/面板/斜杠命令时**应**挂载；系统体检 `/meta/doctor` 失败也可附带本技能。

## 执行步骤
1. `/telegraf/prometheus` 文本、`/telegraf/snapshot` JSON
2. 讨论 SRE 时用真实端点片段；不编造未部署的 metric 名

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `/telegraf/prometheus` · `/telegraf/snapshot`

## 关联技能
- `skills_master_index`

## 自测用语（习惯体检 / 人工抽检）
- 查一下telegraf功能状态
- [skill:feature_telegraf] 走对应 API 试一步
