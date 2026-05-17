# 工具：Windows 桌面自动化

Triggers: focus_window,send_hotkey,type_text,click_screen,list_windows,前台窗口,tool_windows_gui,tool windows gui,tool-windows-gui,windows gui,工具,Windows,桌面自动化,工具windows gui,切换窗口,快捷键,模拟按键,windows_gui

---

**何时使用**：用户需要 **Windows 前台窗口自动化**（工具 `windows_gui`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 与 `multimodal_desktop_agent` 一致：先确认目标应用与授权
2. 优先键盘/焦点路径；坐标点击易碎
3. 高风险弹窗/UAC 绕过请求走 `trust_and_decline`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。
- 未经确认自动登录、支付、删除或 UAC 绕过。

## ONYX 对接
- 工具/配置 `multimodal_desktop_agent`
- 工具/配置 `trust_and_decline`

## 关联技能
- `multimodal_desktop_agent`
- `trust_and_decline`
- `tool_reliability`

## 自测用语（习惯体检 / 人工抽检）
- 用windows gui帮我做一件可验证的小事
- [skill:tool_windows_gui] 调用工具并给出证据
