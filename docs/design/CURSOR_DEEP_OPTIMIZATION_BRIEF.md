# BT（黑光）深度优化蓝图：Atom + Hermes + Cursor 工作流

> 目的：给 Cursor / Codex / Claude Code 作为下一轮深度优化任务单。当前阶段先写方案，不发布，不改运行时代码；能借鉴的是架构模式和验证流程，不直接搬外部项目代码。

## 资料结论

- Atom 可借鉴的是“可黑客化编辑器”路线：Electron + HTML/CSS/JS、包管理、主题、文件树、多 Pane、跨项目搜索、内置 Git/GitHub 工作流、实时协作 Teletype。Atom 本身已归档，不建议引入它的代码或依赖，只借产品结构。
- Hermes Agent 可借鉴的是“常驻自进化 Agent”路线：持久记忆、自动技能创建、多平台消息网关、cron 自动化、并行子智能体、浏览器控制、Docker/SSH/远程执行后端、doctor 诊断、轨迹导出和压缩。
- Cursor/Trae/Claude Code 横评类文章可借鉴的是方向判断：AI 编程正在从补全变成多 Agent 工作区，核心竞争力从“生成代码”转向“验证、维护、可审计交付”。
- 知乎原链接当前抓取返回 403，不能作为已核验依据；后续如果权哥能打开或贴内容，再补进二次分析。

## 对 BT 当前项目的判断

BT 已经具备 Electron + React + FastAPI、本地模型网关、工具调用、记忆、前端工作台、数字人和双引擎雏形。下一步不该做大而散的重构，而是把现有能力收束成一个“高定本地 Agent Control Plane”：

- 一个工作区：聊天、任务、工具、模型、数字人、运行状态在一个可切换界面里。
- 一条执行线：用户指令 -> 计划 -> 工具调用 -> 结果验证 -> 可回放记录。
- 一个学习闭环：任务结束后自动沉淀经验为 skill / memory / runbook，但必须有人类确认入口。
- 一个安全边界：工具风险分级、干跑、确认、回滚说明、敏感信息扫描。
- 一个高定数字人：不是游戏角色，不是赛博 UI，而是 Hermès / Bottega Veneta 级别的克制奢华真人代理人。

## 最高优先级审美标准

当前数字人必须从“科技演示”升级成“时装屋代理人”。Cursor 做 UI 或 Three.js 时，按下面标准执行：

- 脸：真人面孔优先，肤色自然，不能过度锐化、不能塑料感、不能游戏角色化。
- 光：三层光。暖顶光塑造额头和鼻梁，侧光给颧骨和头发边缘，低强度阴影保留真人立体感。
- 材质：皮肤是柔和漫反射，头发有厚度和微弱光泽，眼睛要有湿润高光但不夸张。
- 色彩：Hermès 橙不要大面积使用，转为金棕、皮革棕、丝绸米白和少量铜金。
- 字体：展示名用衬线，系统信息用等宽；不要默认 Inter/Arial/system-ui 做主视觉。
- 布局：脸是第一视觉中心，信息只在边缘像展厅铭牌；不堆卡片，不堆按钮，不做科技 HUD。
- 动效：只要呼吸感、轻微视差和低频光线变化；不要炫光、粒子雨、霓虹扫描线。
- 文案：用“Maison Agent / Atelier / Portrait / Depth”这种克制语言，不要“AI超强/赛博/酷炫”。

## Cursor 执行顺序

### P0：先补观测，不碰大功能

目标：每次启动都知道“哪条链路活着、哪条坏了、是谁占端口”。

- 增强 `/meta/doctor`：输出 backend、frontend、8000/8001、Ollama/SGLang、TTS、SadTalker、数字人资产状态。
- 给前端加一个“系统状态条”：只展示状态，不做自动修复。
- 所有诊断结果返回 `{ok, status, checks, next_action}`，不要只返回字符串。
- 验证：`curl.exe -sS http://127.0.0.1:8000/health`、`curl.exe -sS http://127.0.0.1:8000/meta/doctor`、`pytest backend/tests -q`。

### P1：Atom 式工作区，不做花架子

目标：把当前 UI 收成多 Pane 工作台，而不是继续堆页面。

- 左侧：项目文件 / 任务队列 / 技能库。
- 中间：Agent 对话 + 执行时间线。
- 右侧：工具结果、数字人、模型状态、日志。
- 底部：Git 状态、验证命令、最近失败。
- 必须保留现有暗色科技风格，不重写整套前端。

### P2：Hermes 式学习闭环，但先可控

目标：任务完成后生成“经验候选”，不自动污染长期记忆。

- 新增 `memory_candidate`：任务摘要、失败原因、成功命令、适用路径、风险等级。
- 前端提供“采纳为技能 / 忽略 / 稍后”三个动作。
- 技能格式保持 `SKILL.md` 或 repo 现有 skills markdown，避免新格式。
- 只把高价值稳定结论写入长期记忆，日志和临时错误不要写。

### P3：工具和执行内核分级

目标：让 Agent 知道什么能直接做，什么要确认。

- 低风险：读文件、搜索、测试、构建、HTTP health check。
- 中风险：编辑代码、安装依赖、启动服务、写 docs。
- 高风险：删除、系统权限、发布、真实付款、暴露 token、关闭安全设置。
- 每个工具声明 `risk_level`、`dry_run_supported`、`rollback_hint`。
- UI 显示风险提示，后端强制校验，不只靠前端。

### P4：多 Agent 不是乱开线程

目标：借 Cursor/Hermes 的并行思想，但先做“角色化串并行”。

- Planner：拆任务和验收标准。
- Builder：按最小补丁实现。
- Reviewer：只找 bug、风险、缺测试。
- Verifier：真实运行命令并收集输出。
- Memory：任务结束后写候选经验。
- 初期不要让多个 Agent 同时改同一文件；并行只用于读、查资料、测试、截图。

### P5：数字人链路按真实产物推进

目标：把 Depth Anything、Three.js、SadTalker 做成可验证的高定真人代理人链路。

- `scripts/depth_infer.py` 生成 `photo.png/depth.png`。
- Three.js 数字人只读取 `frontend/public/digital-human/` 下的受控资产。
- Three.js shader 要优先改善真人肤色、脸部三层光、头发边缘和低频呼吸，不要做游戏角色特效。
- SadTalker 先作为本地外部工具，不把整包纳入 Git。
- 视频生成产物进 ignored 目录，只提交脚本和 README。
- 验证：生成深度图、前端 build、SadTalker 脚本语法检查、必要时人工看结果；人工验收以“像真人高定代理人”为准，不以技术特效多少为准。

## 不要做

- 不要直接把 Hermes 整仓塞进 BT。
- 不要把 Atom 旧代码或插件生态当依赖。
- 不要用“自动学习”绕过用户确认写长期记忆。
- 不要在一个提交里混入系统安装、模型下载、UI 重写和后端架构重构。
- 不要提交 `SadTalker/`、模型权重、生成图片/视频、`.env`、数据库、日志。

## Cursor 下一轮提示词

```text
请先阅读 AGENTS.md、CLAUDE.md、docs/CURSOR_DEEP_OPTIMIZATION_BRIEF.md 和 git status。
目标不是重写项目，而是按 P0 -> P1 -> P2 顺序做小步深度优化。
每一步必须先列验收标准，再改代码，再跑真实验证。
优先改 /meta/doctor 和前端状态可视化，不要改模型配置，不要提交真实密钥，不要纳入 SadTalker 整包或生成媒体。
数字人方向必须是 Hermès / Bottega Veneta 级别的克制奢华真人代理人：真实脸、暖金棕、衬线+等宽、三层光、呼吸感，不要赛博游戏角色。
如果需要安装依赖、删除文件、发布或改系统权限，先停下来问权哥。
```

## 参考来源

- Atom 官网：https://atom-editor.cc/
- Atom 归档说明：https://github.blog/news-insights/product-news/sunsetting-atom/
- Hermes Agent 官网：https://hermes-agent.org/zh/
- Hermes Agent GitHub：https://github.com/NousResearch/hermes-agent
- CSDN 横评文章：https://blog.csdn.net/weixin_44822948/article/details/160746765
- 高定数字人参考板：`docs/DIGITAL_HUMAN_REFERENCE_BOARD.md`
