# BKLT SkillHub 设计说明

BKLT SkillHub 是 BKLT 黑光的技能市场与自进化技能底座。它借鉴 Hermes Agent optional-skills 的设计，但面向 Windows 本地 AI Agent 桌面工作台做本地化改造。

## 目标

1. 技能不再只是 `backend/agent_skills/*.md` 的静态文档，而是可索引、可审计、可启用、可禁用的能力包。
2. 默认上下文保持精简，只给模型技能索引；需要时再加载完整技能和 reference 文件。
3. 外部技能必须先进入隔离区和静态风险扫描，不能直接执行。
4. 成功任务可以沉淀为候选技能，形成程序性记忆。

## 目录分层

```text
backend/agent_skills/       # 核心内置技能，默认启用
backend/optional_skills/    # 官方可选技能，默认不启用
backend/user_skills/        # 用户或 Agent 创建的技能
backend/skill_quarantine/   # 外部导入隔离区，必须审计
```

## API v1

SkillHub v1 是只读底座，不做外部安装，不运行脚本。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/meta/skillhub/summary` | 技能数量、来源、风险摘要 |
| GET | `/meta/skillhub/registry` | 结构化技能索引，可按 source / risk_level 过滤 |
| GET | `/meta/skillhub/audit` | 静态风险扫描结果 |
| GET | `/meta/skillhub/skills/{skill_id}` | 单个技能详情和完整内容 |

旧接口 `/meta/skills` 暂时保留，用于兼容现有前端和 Agent 技能挂载逻辑。

## 渐进加载

```text
Level 0: /meta/skillhub/registry
只返回 name / description / category / source / risk_level / tags

Level 1: /meta/skillhub/skills/{skill_id}
加载完整 SKILL.md

Level 2: references / scripts / templates
后续版本按文件路径受控加载
```

## 风险分层

| 等级 | 含义 | v1 行为 |
|------|------|---------|
| safe | 文档型技能，无明显危险指令 | 可显示、可作为候选上下文 |
| confirm | 涉及脚本、联网、环境变量、进程启动 | 显示风险，需要确认后才能启用执行能力 |
| dangerous | 删除、格式化、密钥外传、私钥访问等 | 默认禁止启用，留在隔离区 |

v1 静态扫描关键词包括：

- `rm -rf`、`del /s`、`rmdir /s`
- `format`、`clear-disk`、`remove-partition`
- `Invoke-WebRequest`、`curl`、`wget`、`irm`、`iwr`
- `OPENAI_API_KEY`、`API_KEY`、`SECRET`、`PASSWORD`、`TOKEN`
- `id_rsa`、`BEGIN PRIVATE KEY`
- `subprocess`、`Start-Process`、`os.system`、`exec`、`eval`

## 与 Hermes optional-skills 的对应关系

| Hermes 机制 | BKLT 实现 |
|-------------|-----------|
| `optional-skills/` 默认不激活 | `backend/optional_skills/` 默认不启用 |
| Skills Hub browse/search/install | v1 先做 registry/audit，v2 再做 install/enable |
| Progressive disclosure | registry → detail → supporting files |
| frontmatter 元数据 | 支持 `name`、`description`、`version`、`platforms`、`metadata.hermes.tags`、`metadata.bklt.tags` |
| trust levels | core / optional / user / quarantine |
| security scan | v1 静态扫描，v2 增加策略确认和隔离区 UI |

## 第一批建议移植/重写技能

| 优先级 | 技能 | BKLT 处理 |
|--------|------|-----------|
| P0 | one-three-one-rule | 可重写为 `backend/optional_skills/communication/one-three-one-rule/SKILL.md` |
| P0 | bklt-project-maintenance | 黑光自身维护流程，放 core 或 user |
| P1 | watchers | 改 Windows 版，接 scheduler 和 automation events |
| P1 | fastmcp | 改为 BKLT MCP 生成器，用于把本地能力开放为 MCP |
| P2 | qmd 思路 | 不直接依赖 qmd，做 BKLT local knowledge search |
| P2 | honcho 思路 | 不直接接入，参考其 user/AI peer/session summary/profile 结构 |

## 后续路线

### v1：索引与审计

- [x] `backend/skillhub.py`
- [x] `backend/skillhub_routes.py`
- [x] `/meta/skillhub/summary`
- [x] `/meta/skillhub/registry`
- [x] `/meta/skillhub/audit`
- [x] `/meta/skillhub/skills/{skill_id}`
- [ ] 前端 SkillStorePanel

### v2：可选技能管理

- [ ] enable / disable 状态存储
- [ ] install from local directory
- [ ] quarantine UI
- [ ] 技能详情抽屉
- [ ] 风险确认弹窗

### v3：外部技能市场

- [ ] GitHub 技能导入
- [ ] URL SKILL.md 导入
- [ ] well-known skills endpoint
- [ ] 技能更新检查
- [ ] 供应链安全日志

### v4：自动学习技能

- [ ] 成功任务复盘生成候选技能
- [ ] 用户确认后写入 `backend/user_skills/`
- [ ] 失败任务生成 troubleshooting 技能
- [ ] 技能使用次数、成功率、最近使用时间

## 安全原则

1. 外部技能默认不执行。
2. 有脚本的技能默认 confirm。
3. dangerous 技能默认禁止启用。
4. 涉及密钥、登录、删除、系统权限、外部发布的技能必须显式确认。
5. 技能可以帮 Agent 思考，但不能绕过工具风险分层。
