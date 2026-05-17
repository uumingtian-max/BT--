# 工具：open_url 与 open_path

Triggers: open_url,open_path,打开链接,打开文件夹,tool_open_navigate,tool open navigate,tool-open-navigate,open navigate,工具,工具open navigate,打开这个链接,open_navigate

---

**何时使用**：用户需要 **打开 URL 或本地路径**（工具 `open_navigate`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 仅打开用户明确同意的 URL/路径；`file://` 注意 Windows 路径转义
2. 不用于批量打开未知来源链接或钓鱼排查外的自动点击链

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用open navigate帮我做一件可验证的小事
- [skill:tool_open_navigate] 调用工具并给出证据
