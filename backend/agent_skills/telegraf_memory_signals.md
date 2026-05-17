# Telegraf / 时序指标与持久信号

Triggers: telegraf,influx,时序,prometheus,指标,监控,采集,grafana,telegraf_memory_signals,telegraf memory signals,telegraf-memory-signals,时序指标与持久信号

---

**何时使用**：用户意图与「Telegraf / 时序指标与持久信号」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 本后端暴露 **`GET /telegraf/prometheus`**（Prometheus 文本）与 **`GET /telegraf/json`**；可用 [Telegraf](https://github.com/influxdata/telegraf) `inputs.prometheus` 拉取后写入 InfluxDB / Mimir 等
2. **本地优先**（对齐私有 Agent 栈）：指标不含用户消息正文，仅聚合 `task_outcomes` 与采样计数；公网部署时配合 `TELEGRAF_METRICS=0` 或反向代理鉴权
3. **持久化信号**（对齐 agent 记忆思路）：把「成功率 / 近 1h 事件量」当作运维信号，与 `playbook` 的人类可读记忆分工明确
4. **多源管线**：设备行为采样 + Agent 工具结果是两条源；Telegraf 侧可再拼系统 `inputs.cpu`、`inputs.mem` 等，形成统一看板（类比多传感器融合思路，非 RuView 硬件能力）
5. 无工具/无读取就声称「已完成」或编造文件内容
6. 把 `.env`、token、密钥写入聊天或记忆
7. 工具 `task_outcomes`
8. （示例）用户会用自然语言提到「Telegraf / 时序指标与持久信号」相关任务

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `task_outcomes`
- 工具/配置 `playbook`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「Telegraf / 时序指标与持久信号」相关的事
- [skill:telegraf_memory_signals] 执行一步可验证操作
