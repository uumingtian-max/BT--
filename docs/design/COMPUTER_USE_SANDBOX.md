# BT Computer-Use Sandbox

## 当前状态（未上线）

- 本机已经检测到 Docker 和 WSL，可作为隔离执行基础。
- 项目已有 `browser_playwright` 工具、路径沙盒、`PolicyGuard` 风险拦截和 Docker compose 示例。
- 还没有完整启用真正的 Computer-Use 隔离沙箱：缺少专用容器/虚拟桌面、截图-动作 agent loop、前端确认流和真实隔离浏览器适配器。
- 当前只保留设计边界，不挂主应用路由，不对外宣称“可用沙箱”。

## 已修正的安全边界

- 浏览器工具不再自动执行 `pip install playwright` 或 `playwright install chromium`。
- 缺依赖时只返回明确错误，等待用户确认安装。
- `/meta/doctor` 增加 `computer_use_sandbox` 状态，避免把“计划中”误报成“已启用”。
- 暂不提供 `/meta/computer-use/*` 能力，等隔离浏览器、确认 UI、动作审计全部齐了再落地。
- 未显式启用 `COMPUTER_USE_SANDBOX_ENABLED=1` 时，动作只进入审计日志并被阻断，不会控制用户主桌面。
- `click/type/key` 或涉及登录、付款、发布、删除、安装、下载、权限的动作会返回 `waiting_confirmation`。

## 目标形态

Computer-Use Sandbox 必须满足：

- 隔离运行：在 Docker / WSL / 专用浏览器 profile 内执行，不直接控制用户主桌面。
- 最小权限：只能访问允许目录、临时下载目录和指定 localhost。
- 可观察：每一步保留截图、动作、DOM/窗口标题、时间戳和结果。
- 可确认：登录、付款、发布、删除、权限变更、外部下载必须停下来让用户确认。
- 可恢复：任务失败后能从最近截图和动作日志继续，而不是重新猜。

## 推荐环境变量

```env
COMPUTER_USE_SANDBOX_ENABLED=0
COMPUTER_USE_SANDBOX_URL=http://127.0.0.1:9222
COMPUTER_USE_SANDBOX_ROOT=backend/workspace/computer-use
COMPUTER_USE_SANDBOX_ALLOW_NET=localhost,127.0.0.1
COMPUTER_USE_REQUIRE_CONFIRM=login,payment,publish,delete,permission,download
```

## 下一步补丁

1. 前端增加 Sandbox 状态卡：未启用、可用、执行中、等待确认、已阻断。
2. Playwright 只连接到用户确认过的 sandbox browser，不直接打开本机默认浏览器。
3. 所有截图和动作日志写入 `outputs/computer-use/`，默认不进 Git。
4. 增加 sandbox browser adapter：连接隔离 Chromium/CDP 或容器内浏览器。
5. 增加动作确认 UI：展示风险标签、目标页面、将要输入的内容摘要和批准按钮。

## 非目标

- 不自动安装 Docker、Playwright、Chromium 或系统服务。
- 不关闭安全策略，不绕过浏览器权限，不保存用户登录凭证。
- 不把外部 Manus / Claude / OpenAI 的实现搬进项目，只吸收隔离执行、证据链和确认机制这些原则。
