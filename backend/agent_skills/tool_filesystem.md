# 工具：读写与列目录

Triggers: read_file,write_file,list_files,改代码,读文件,列目录,tool_filesystem,tool filesystem,tool-filesystem,filesystem,工具,读写与列目录,写文件,创建文件,保存到,改这个文件,工具filesystem,读代码

---

**何时使用**：用户需要 **读写信箱与列目录**（工具 `filesystem`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 改前先 `list_files` 定位，再 `read_file` 相关入口；禁止未读大段重写
2. `write_file` 保持与仓库风格一致；一次改动聚焦一个意图
3. 默认目录参数为空时用桌面路径；项目任务应显式传项目根路径

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `list_files`
- 工具/配置 `read_file`
- 工具/配置 `write_file`

## 关联技能
- `codebase_context_first`
- `spec_minimal_steps`
- `llm_coding_pitfalls`
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 读 backend/main.py 总结入口
- 只改 README 里技能数量那一行
