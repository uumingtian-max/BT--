# Git Worktree 并行开发（git-wt 思路）

Triggers: git-wt,worktree,并行分支,多分支同时,zkochan,git work tree,同时开发

对标 **git-wt**：同一仓库多工作区并行，减少 stash 切换成本。

**Agent 协助边界**：

1. 可 `read_file`/`list_files` 读**当前**工作区；不假设其他 worktree 路径存在。
2. 用户要并行实验时，建议命令（由用户在终端执行）：
   - `git worktree add ../feature-x -b feature-x`
   - 每个 worktree 独立 `npm install` / `.env`
3. 改文件前 `read_file` 确认路径属于目标 worktree；合并冲突列出文件级清单。
4. `run_project_check` 在**当前目录**跑；多 worktree 需用户指定 cwd。
5. 禁止：Agent 自行 `git push --force` 或删除 worktree（无用户明确指令）。

与 `swarm_orchestration_lite` 共用：**单写者**、合并前拉最新。
