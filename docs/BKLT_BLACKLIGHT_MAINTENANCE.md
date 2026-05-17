# BKLT 黑光维护基线

> 本文件是 ai-agent-project / BKLT 黑光 的长期维护规则。旧名 ONYX-OVERRIDE 只作为历史兼容名保留；对外统一使用 **BKLT 黑光 / BLACKLIGHT**。

## 项目定位

BKLT 黑光是一个本地优先的 AI Agent 自动化可视化工作台，不是普通聊天机器人。目标是让 AI 在用户电脑上自动规划、调用工具、执行任务、运行测试、整理记忆、同步 GitHub，并把执行过程可视化。

## 当前固定信息

- 本地路径：`C:\Users\ROG\Desktop\ai-agent-project`
- GitHub 仓库：`https://github.com/uumingtian-max/ai-agent-project`
- 桌面快捷方式：`C:\Users\ROG\Desktop\BKLT 黑光.lnk`
- 后端地址：`http://127.0.0.1:8000`
- 本地 OpenAI-compatible 模型网关：`http://127.0.0.1:8001/v1`
- 当前主要模型 ID：`nvidia/Gemma-4-26B-A4B-NVFP4`
- 本地模型目录：`D:\models\Gemma-4-26B-A4B-NVFP4`

## 启动链路

当前启动链路仍带有旧名，迁移时必须保证可回滚、不断启动：

```text
BKLT 黑光.lnk
  -> wscript.exe
  -> C:\Users\ROG\Desktop\ai-agent-project\Launch-ONYX-OVERRIDE.vbs
  -> START.bat
  -> scripts\launch-agent.ps1
```

迁移策略：

1. 先新增 BKLT 命名脚本或别名，不删除旧 ONYX 文件。
2. 确认新链路能启动后，再把快捷方式目标迁到 BKLT 文件。
3. 最后只保留旧文件作为兼容入口或带提示的转发脚本。

## 少确认维护规则

默认少确认、直接执行：

- 项目维护、代码修改、测试、构建、GitHub 同步、整理说明：能直接做就直接做。
- 不要每一步都询问确认。
- 完成后只汇报：改了什么、真实跑了什么、结果是什么、还有什么风险。
- 用户不需要学习复杂工程细节；维护者应主动执行、主动验证、简短汇报。
- 如果必须用户点一次权限，只说明点哪个按钮，不展开长篇解释。

必须确认的情况：

- 删除大量文件。
- 覆盖用户未保存内容。
- 暴露密钥、隐私、数据库、个人运行记录。
- 登录授权、付款、发布到外部平台。
- 系统级权限或不可逆操作。

## 提交与安全规则

必须遵守：

- 代码改动后必须真实运行测试、编译或构建，不能假装完成。
- 重要优化后提交并同步 GitHub。
- 不提交 `.env`、数据库、`node_modules`、`outputs`、`frontend/build`、个人运行记录、临时文件。
- 接手本地仓库前先看 `git status` 和 `git diff`，尤其注意 `backend/context_pack.py`、`backend/memory_store.py` 可能有未提交半成品。

## 下一阶段优先级

1. 品牌迁移：README、启动器、窗口标题、manifest、图标、快捷方式链路从 ONYX-OVERRIDE 逐步迁到 BKLT 黑光。
2. 模型 ID 统一：确保 `.env`、后端运行时、前端展示、vLLM `/models` 一致使用 `nvidia/Gemma-4-26B-A4B-NVFP4`。
3. 手机端入口：展示局域网地址、Tailscale 地址、二维码、token 登录状态。
4. 自动化可视化：项目健康检查流水线、工具调用时间线、日志、GitHub 同步状态。
5. 记忆与上下文：完成上下文压缩报告和记忆树增强，避免覆盖本地未提交半成品。

## 排障顺序

如果 BKLT 黑光启动后不能正常回答，优先检查：

1. `http://127.0.0.1:8001/v1/models` 是否可用。
2. 本地 vLLM / Gemma OpenAI-compatible 网关是否运行。
3. `http://127.0.0.1:8000/health` 是否返回 `ok`。
4. 后端 `/meta/info` 中模型 ID 是否和本地网关一致。
5. 前端是否连接到正确后端地址。

不要误判为 ChatGPT 没连上：ChatGPT 项目只做记录、交接和维护协作，不负责本地推理。