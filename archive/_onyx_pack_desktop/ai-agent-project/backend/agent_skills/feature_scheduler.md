# 能力：定时任务

Triggers: scheduler,定时,周期任务,cron,自动跑,feature_scheduler,feature scheduler,feature-scheduler,能力,定时任务,定时跑,每天执行,cron job

---

**何时使用**：用户涉及 ONYX **定时任务**（`feature_scheduler`）或相关 API/面板/斜杠命令时**应**挂载；系统体检 `/meta/doctor` 失败也可附带本技能。

## 执行步骤
1. API：`/scheduler/jobs` 列表/创建；`/jobs/{id}/run` 立即执行
2. 任务提示词应自包含；间隔 `interval_sec` 不宜过短以免刷爆 LLM
3. UI 面板「定时」与斜杠 `/scheduler` 可跳转

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `/scheduler/jobs` · `POST /jobs/{id}/run`

## 关联技能
- `skills_master_index`

## 自测用语（习惯体检 / 人工抽检）
- 查一下scheduler功能状态
- [skill:feature_scheduler] 走对应 API 试一步
