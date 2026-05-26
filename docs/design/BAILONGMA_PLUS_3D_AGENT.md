# BaiLongma++ Direction For BT

> 参照 BaiLongma 的方向，但不复制代码、界面、提示词或仓库结构。BT 的目标是更高级的真人 3D 数字代理人：一个有面孔、有意识流、有超级记忆、能联网学习并长出候选技能的本地高定 Agent。

## BaiLongma 值得借鉴的点

- 持续运行：不是一问一答，而是由 TICK 驱动的长期循环。
- 记忆注入：SQLite、全文搜索、向量召回、显著性排序共同决定当轮上下文。
- 焦点栈：对话主题不是平铺历史，而是多帧注意力栈，可 push、return、pop、compress。
- Brain UI：用户能看到思考流、工具调用、记忆注入、焦点变化，而不是只看最终回复。
- 自检和看门狗：启动自检、超时 abort、兜底投递，让系统不会悄悄卡死。
- 工具市场：能力可扩展，但必须配合风险隔离和审计。

## BT 要更高级的地方

- 真人 3D 第一：BaiLongma 更偏意识框架，BT 要把“意识流”落到真人肖像、深度图、呼吸光、眼神高光和高定材质里。
- 超级记忆：不只是检索记忆，而是根据用户语气、纠正、反复强调、满意/不满信号生成反思上下文。
- 自成长技能：联网学习外部方向，提炼证据，生成 pending 候选技能；用户确认后才进入 user skill。
- 本地优先：照片、候选记忆、运行日志、数据库、生成媒体默认不进 Git。
- 高端克制：不是赛博桌宠，不是游戏 NPC；界面像高定展厅里能思考的真人代理人。

## 真人 3D Conscious Agent 验收标准

- 主视觉必须是用户真人肖像或授权肖像，不用通用卡通 avatar。
- 3D 层至少由 `photo.png + depth.png` 驱动，能做轻微 parallax、呼吸和低频光影。
- UI 上可见四个意识信号：`TICK`、`FOCUS`、`MEMORY`、`SKILL`。
- Agent 忙碌时不只显示 spinner，而是显示意识流运行、焦点栈、超级记忆、候选技能生长。
- 用户纠正后，下一轮系统上下文必须能读到超级记忆反思。
- 联网学习只能生成候选技能，不自动激活、不搬外部代码、不自作主张安装。

## 下一步补丁路线

1. 已落地：前端 DigitalHumanStage 做成 Conscious Maison Agent，增加意识环和四类信号。
2. 已落地：后端新增 `consciousness_loop.py`，提供低风险 TICK、状态 API 和手动 tick API。
3. 下一步：把 super_memory / consciousness 的状态接入前端状态卡，显示当前语气判断和最新反思。
4. 下一步：增加 focus stack 可视化，先从当前会话主题开始，不急着全量重构。
5. 下一步：把 `/meta/super-memory/learn-web` 生成的 pending 技能显示到 SkillHub 候选区。
6. 沙箱：等隔离浏览器、确认 UI、动作审计三件套齐了再上线，不提前冒充完成。

## 后端 TICK 边界

- `GET /meta/consciousness/status`：查看 TICK 状态和最近心跳。
- `POST /meta/consciousness/tick`：手动跑一次本地自省。
- 默认 `CONSCIOUS_TICK_ENABLED=1`，`CONSCIOUS_TICK_SEC=180`，最低 30 秒。
- TICK 只读取本地超级记忆、候选技能、任务复盘；不执行工具、不上传、不下载、不安装。
