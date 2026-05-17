# BT 外仓对照（精简三仓）

Triggers: 外仓,参考仓库,vendor,agency-agents,gstack,superpowers,同步外仓,bt_external_repos,bt external repos,克隆对照,热榜仓库,bt-external-repos,外仓对照,精简三仓

---

**何时使用**：用户问「还要拉哪些 GitHub」「对照外仓更新技能」或 Triggers 命中时。BT **只**默认维护 2 个对照仓 + 1 个可选格式仓。

## 执行步骤

1. 说明原则：运行时读 `backend/agent_skills/*.md`，**不**直接加载 `vendor/` 内 markdown
2. 默认对照仓：
   - **agency-agents** → 已落地 `agency_*` 技能、Cursor `agency-*.mdc`
   - **gstack** → 已落地 `gstack_agent_roles`、`agency_dev_orchestrator`
3. 可选：**obra/superpowers**（仅写新技能时对照格式）
4. 拉取命令（项目根）：`.\scripts\sync-bt-vendor-repos.ps1`；含 superpowers 加 `-All`
5. 从外仓**挑选**单文件改写进 `agent_skills/`，勿整仓复制或安装 Hermes CLI

## 避免

- 声称 HermesHub / hermes skills install 已接入 BT
- 把 vendor 全文塞进上下文或技能包
- 无 `git clone` 结果就声称已同步

## ONYX 对接

- 清单 `vendor/repos.manifest.json` · 说明 `vendor/README.md`
- 技能总览 `GET /meta/skills` · 社区对照 `GET /meta/alignment`

## 自测用语

- BT 需要 clone 哪几个外仓？
- [skill:bt_external_repos] 如何从 agency-agents 更新 code reviewer 技能
