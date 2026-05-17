# BT 外仓对照（精简）

本目录**不**参与 BT 运行时加载；Agent 实际用的是 `backend/agent_skills/*.md`。

## 默认拉取的 2 个仓

| 仓 | 用途 |
|----|------|
| [agency-agents](https://github.com/msitarzewski/agency-agents) | 工程向人设：审查、安全、验收、编排（已压缩为 `agency_*` 技能 + Cursor `agency-*.mdc`） |
| [gstack](https://github.com/garrytan/gstack) | 多角色流水线，对齐 `gstack_agent_roles` / `run_task_orchestration` |

## 可选（需加 `-All`）

| 仓 | 用途 |
|----|------|
| [obra/superpowers](https://github.com/obra/superpowers) | 写新技能时的格式参考 |

## 拉取

```powershell
# 项目根执行：仅 agency-agents + gstack
.\scripts\sync-bt-vendor-repos.ps1

# 含 superpowers
.\scripts\sync-bt-vendor-repos.ps1 -All
```

清单：`vendor/repos.manifest.json`。`vendor/*/` 已在 `.gitignore`，不会进 Git。

## 刻意不纳入 vendor

- **HermesHub / hermes-agent**：CLI 与 BT 技能包不兼容，勿 `hermes skills install` 到本仓库。
- **llama.cpp**：用 `scripts/ensure-llama-cpp.ps1` + `docs/setup/LLAMA_CPP.md`，不必克隆源码。
- 其余热榜仓：主题已写在 `github_trending_developers.md`，无需再占磁盘。
