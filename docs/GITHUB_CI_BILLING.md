# GitHub CI 与 PR 收尾说明

## CI 红叉（已确认）

GitHub Actions 失败原因 **不是代码**：

> The job was not started because your account is locked due to a billing issue.

处理步骤：

1. 打开 [GitHub Billing](https://github.com/settings/billing)
2. 解除账户锁定 / 更新付款方式
3. 在 [Actions](https://github.com/uumingtian-max/BT--/actions) 对最新 commit 点 **Re-run all jobs**

本地等价验证（不依赖 GitHub）：

```powershell
powershell -File scripts\run-ci-local.ps1
```

## PR 建议（合并后）

主功能已合入 `main` 后，可关闭重复 PR：

| PR | 说明 | 建议 |
|----|------|------|
| [#3](https://github.com/uumingtian-max/BT--/pull/3) | feature/bklt-stable-automation | 合并或关闭（内容已在 main） |
| [#8](https://github.com/uumingtian-max/BT--/pull/8) | 仪表盘时间线 | 关闭（已含于 main） |
| [#9](https://github.com/uumingtian-max/BT--/pull/9) | BACKEND_HOST | 关闭（已含于 main） |
| [#10](https://github.com/uumingtian-max/BT--/pull/10) | BACKEND_HOST + env | 关闭（已含于 main） |

```powershell
gh auth login
gh pr close 8 --comment "Merged via main"
gh pr close 9 --comment "Merged via main"
gh pr close 10 --comment "Merged via main"
gh pr merge 3 --merge   # 若 PR 仍 open 且与 main 无 diff
```

## Nemotron 推理（可选）

```powershell
launcher\START_NEMOTRON_DOCKER.bat
# 健康检查
curl http://127.0.0.1:8001/health
```
