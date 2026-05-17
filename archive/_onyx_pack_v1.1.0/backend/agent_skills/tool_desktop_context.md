# 工具：桌面上下文画像

Triggers: get_device_profile,get_recent_desktop,work_summary,evolution_profile,桌面文件,最近工作,tool_desktop_context,tool desktop context,tool-desktop-context,desktop context,工具,桌面上下文画像,工具desktop context,我电脑配置,显卡,最近桌面文件,desktop_context

---

**何时使用**：用户需要 **桌面画像与近期工作区**（工具 `desktop_context`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. `get_device_profile`：OS/GPU/路径能力，回答环境相关问题时先拉取
2. `get_recent_desktop_files` / `get_recent_work_summary`：辅助理解用户当前工作区，不代替用户授权读隐私目录
3. `get_evolution_profile`：长期偏好与进化摘要；与 `/chat/memories` 互补

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `get_device_profile`
- 工具/配置 `get_recent_desktop_files`
- 工具/配置 `get_recent_work_summary`
- API /chat/memories
- 工具/配置 `get_evolution_profile`

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用desktop context帮我做一件可验证的小事
- [skill:tool_desktop_context] 调用工具并给出证据
