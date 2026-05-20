# GitHub 仓库说明 — ai-agent-project

## 仓库链接

**https://github.com/uumingtian-max/ai-agent-project**

---

## 这是什么

你的 **BT（黑光）** 项目的公开 Git 仓库，和桌面上的本地目录是同一套代码：

| | 路径 |
|---|------|
| **本地** | `C:\Users\ROG\Desktop\ai-agent-project` |
| **线上** | https://github.com/uumingtian-max/ai-agent-project |

---

## 分支

| 分支 | 用途 |
|------|------|
| `main` | 默认主分支 |
| `feature/bklt-stable-automation` | 当前本地开发分支（自动化相关稳定版） |

---

## 常用 Git 命令

```powershell
# 进入项目
cd C:\Users\ROG\Desktop\ai-agent-project

# 看状态
git status

# 拉取远程更新
git pull origin feature/bklt-stable-automation

# 推送本地提交
git push origin feature/bklt-stable-automation
```

---

## 不进 Git 的内容（只在本地）

- `backend/.env`（密钥、模型配置）
- `backend/behavior.db`、`backend/memory.db`
- `data/knowledge-vault/`（知识库，当前约 473 个 memory 文件）
- `node_modules/`、`frontend/build/`、`logs/`、`outputs/`

---

## 相关文档

- 完整文件清单：桌面 `BT黑光-ai-agent-project-文件清单与说明.md`
- 项目 README：仓库根目录 `README.md`
- 目录结构：仓库 `docs/PROJECT_LAYOUT.md`
