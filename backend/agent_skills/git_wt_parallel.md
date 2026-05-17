# Git Worktree 并行开发

Triggers: git worktree,git-wt,并行分支,多工作区,git_wt_parallel,git wt parallel,git-wt-parallel,Git,Worktree,并行开发

---

**何时使用**：用户意图与「Git Worktree 并行开发」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 详见 `git_worktree_workflow`；Agent 不 force push、不擅自改 git config
2. 并行任务：每 worktree 单写者

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `git_worktree_workflow`

## 关联技能
- `git_worktree_workflow`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「Git Worktree 并行开发」相关的事
- [skill:git_wt_parallel] 执行一步可验证操作
