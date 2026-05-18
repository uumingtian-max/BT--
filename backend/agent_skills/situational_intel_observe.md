# 态势感知与设备情报（World Monitor 思路）

Triggers: worldmonitor,态势,情报面板,仪表盘,全球新闻,geopolitical,koala73,observe,简报,监控,situational_intel_observe,situational intel observe,situational-intel-observe,态势感知与设备情报,World,Monitor,思路

---

**何时使用**：用户意图与「态势感知与设备情报（World Monitor 思路）」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. `GET /observe/dashboard` — 前台/进程/桌面文件等画像
2. `POST /observe/report/today` — 生成今日简报
3. `GET /observe/report/latest` — 读取最新简报
4. `GET /telegraf/prometheus` — 指标文本（若启用）
5. 先 **事实**（样本数、Top 进程/标题）再 **推断**（你在忙什么），推断标「可能」
6. 用户要「全球新闻」时：用 `web_search`/`local_search`，标注时间与来源，不做确定性预测
7. 建议动作可执行：「立即采集」→ `POST /observe/sample`；不要假装已刷新外网数据
8. 与记忆系统：引用 `memory_store` 时带日期；冲突时以最新观测为准

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `web_search`
- 工具/配置 `local_search`
- 工具/配置 `memory_store`

## 关联技能
- `worldmonitor_observe`
- `feature_observe`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「态势感知与设备情报（World Monitor 思路）」相关的事
- [skill:situational_intel_observe] 执行一步可验证操作
