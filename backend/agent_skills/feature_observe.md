# 能力：Observe 态势简报

Triggers: observe,dashboard,简报,态势,/observe,feature_observe,feature observe,feature-observe,能力,态势简报

---

**何时使用**：用户涉及 ONYX **本机态势简报**（`feature_observe`）或相关 API/面板/斜杠命令时**应**挂载；系统体检 `/meta/doctor` 失败也可附带本技能。

## 执行步骤
1. `/observe/dashboard`、`/observe/report/today`：基于本机采样，**不虚构**全球实时情报
2. 与 `situational_intel_observe` 技能重复时以此 API 路径为准

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `/observe/dashboard` · `/observe/report/today`

## 关联技能
- `skills_master_index`

## 自测用语（习惯体检 / 人工抽检）
- 查一下observe功能状态
- [skill:feature_observe] 走对应 API 试一步
