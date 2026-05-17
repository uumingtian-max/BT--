# BKLT 黑光维护基线

> 维护基线（品牌对外为 **BT（黑光）**；BKLT / ONYX 为历史兼容名）。启动脚本在 **`launcher/`**。

## 项目定位

BT（黑光）是一个本地优先的 AI Agent 自动化可视化工作台，不是普通聊天机器人。目标是让 AI 在用户电脑上自动规划、调用工具、执行任务、运行测试、整理记忆、同步 GitHub，并把执行过程可视化。

## 当前固定信息

- 本地路径：`C:\Users\ROG\Desktop\ai-agent-project`
- GitHub 仓库：`https://github.com/uumingtian-max/ai-agent-project`
- 桌面快捷方式：指向 `launcher\Launch-BT-Heiguang.vbs`
- 后端地址：`http://127.0.0.1:8000`
- 本地 OpenAI 兼容网关（llama.cpp）：`http://127.0.0.1:8001/v1`
- 当前主要模型 ID：`Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced-Q5_K_P`（须与 `backend\.env` 及 `/v1/models` 一致）
- 配置模板：`backend\.env.local-llamacpp.example`

## 启动链路

```text
桌面快捷方式
  -> launcher\Launch-BT-Heiguang.vbs
  -> launcher\START_APP.bat
  -> scripts\ensure-llama-cpp.ps1（LLM_BACKEND=openai_compatible 时）
  -> Electron
```

兼容：`launcher\Launch-BKLT-Blacklight.vbs`、`launcher\Launch-ONYX-OVERRIDE.vbs` 仍可作为旧快捷方式入口。

迁移策略：

1. 新脚本放在 `launcher\`，根目录 `START_APP.bat` 仅转发到 launcher。
2. 确认新链路能启动后，再把桌面快捷方式改到 `Launch-BT-Heiguang.vbs`。
3. 旧名文件保留为兼容转发，不直接删除。

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

1. 品牌统一：对外统一 **BT（黑光）**（README、启动器、窗口标题、manifest、图标）。
2. 模型 ID 统一：`.env`、`frontend/src/modelCatalog.js`、`http://127.0.0.1:8001/v1/models` 三者一致。
3. 手机端入口：展示局域网地址、Tailscale 地址、二维码、token 登录状态。
4. 自动化可视化：项目健康检查流水线、工具调用时间线、日志、GitHub 同步状态。
5. 记忆与上下文：完成上下文压缩报告和记忆树增强，避免覆盖本地未提交半成品。

## 排障顺序

如果 BT（黑光）启动后不能正常回答，优先检查：

1. `http://127.0.0.1:8001/v1/models` 是否可用（llama-server）。
2. `backend\.env` 中 `LLAMA_CPP_*`、`OPENAI_BASE_URL` 是否正确；日志 `logs\llama-server.log`。
3. `http://127.0.0.1:8000/health` 是否返回 `ok`。
4. 后端 `/meta/doctor` 或 `/meta/info` 中模型 ID 是否与 8001 网关一致。
5. 前端是否连接到正确后端；改 `frontend` 后须 `npm run build --prefix frontend`（在项目根目录执行）。

实验性 vLLM 路线见 `launcher\START_VLLM_GEMMA4.bat`，非当前默认。

不要误判为 ChatGPT 没连上：ChatGPT 项目只做记录、交接和维护协作，不负责本地推理。
