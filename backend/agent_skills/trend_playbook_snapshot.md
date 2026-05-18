# 热榜主题快照（行为对齐，不拉取外网）

Triggers: 热榜,trending,github,今日榜单,社区风向,升级路线,对标,trending developers,开发者热榜,trend_playbook_snapshot,trend playbook snapshot,trend-playbook-snapshot,热榜主题快照,行为对齐,不拉取外网,风向,升级建议,对标清单

---

**何时使用**：用户意图与「热榜主题快照（行为对齐，不拉取外网）」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. **本地化个人智能体**：默认本机工具链与显式配置的上游；不假设用户已登录某云
2. **持久记忆与可复现**：写入记忆前合并近似条目；结论区分「观测 / 推断」并带时间或路径锚点
3. **方法论 + Skills**：短触发词 + 可执行清单 + 验收标准；复杂任务先拆步再调工具
4. **科研 / 工程技能链**：先列假设、数据与失败模式；数值结论写前提与不确定度
5. **规范驱动交付**：意图 → 最小可验证契约（接口/数据/错误码）→ 实现 → 自测；保持小 PR 粒度
6. **可观测与长任务**：长步骤在回复中分段小结；指标端点若已部署则可用 `/telegraf/prometheus` 做健康检查思路（不代替业务监控设计）
7. **多 Agent / 编排**：单一写入者或明确合并规则；避免并行改同一资源无锁
8. **Trending Developers 当日主题**：优先挂载 `github_trending_developers`，再按子技能（A2A / 计划审阅 / RLM / gstack / stitch / 路由 / 态势）细化

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- API /telegraf/prometheus
- 工具/配置 `github_trending_developers`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「热榜主题快照（行为对齐，不拉取外网）」相关的事
- [skill:trend_playbook_snapshot] 执行一步可验证操作
