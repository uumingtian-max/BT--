# Git Worktree 并行开发（git-wt 思路）

Triggers: git-wt,worktree,并行分支,多分支同时,zkochan,git work tree,同时开发,git_worktree_workflow,git worktree workflow,git-worktree-workflow,Git,并行开发,思路,多分支并行

---

**何时使用**：用户意图与「Git Worktree 并行开发（git-wt 思路）」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 可 `read_file`/`list_files` 读**当前**工作区；不假设其他 worktree 路径存在
2. 用户要并行实验时，建议命令（由用户在终端执行）：
3. `git worktree add ../feature-x -b feature-x`
4. 每个 worktree 独立 `npm install` / `.env`
5. 改文件前 `read_file` 确认路径属于目标 worktree；合并冲突列出文件级清单
6. `run_project_check` 在**当前目录**跑；多 worktree 需用户指定 cwd
7. 禁止：Agent 自行 `git push --force` 或删除 worktree（无用户明确指令）

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `read_file`
- 工具/配置 `list_files`
- 工具/配置 `run_project_check`

## 关联技能
- `git_wt_parallel`
- `llm_coding_pitfalls`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「Git Worktree 并行开发（git-wt 思路）」相关的事
- [skill:git_worktree_workflow] 执行一步可验证操作
