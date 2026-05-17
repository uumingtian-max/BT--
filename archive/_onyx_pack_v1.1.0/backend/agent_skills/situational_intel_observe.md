# 态势感知与设备情报（World Monitor 思路）

Triggers: worldmonitor,态势,情报面板,仪表盘,全球新闻,geopolitical,koala73,observe,简报,监控

对标 **worldmonitor** 类「情报面板」— 本仓库用**本机可观测数据**，不抓取未授权情报源或虚构实时战报。

**可用 API**：

- `GET /observe/dashboard` — 前台/进程/桌面文件等画像
- `POST /observe/report/today` — 生成今日简报
- `GET /observe/report/latest` — 读取最新简报
- `GET /telegraf/prometheus` — 指标文本（若启用）

**回答风格**：

1. 先 **事实**（样本数、Top 进程/标题）再 **推断**（你在忙什么），推断标「可能」。
2. 用户要「全球新闻」时：用 `web_search`/`local_search`，标注时间与来源，不做确定性预测。
3. 建议动作可执行：「立即采集」→ `POST /observe/sample`；不要假装已刷新外网数据。
4. 与记忆系统：引用 `memory_store` 时带日期；冲突时以最新观测为准。

UI：侧栏 **设备画像** + **系统** 自检；Agent 可调 `get_device_profile`。
