# 工具：run_project_check

Triggers: run_project_check,lint,构建检查,frontend check,npm audit,tool_project_check,tool project check,tool-project-check,project check,工具,工具project check,npm build,构建失败,project_check

---

**何时使用**：用户需要 **前端构建与依赖检查**（工具 `project_check`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. `target=frontend`：适合 React/Electron 构建与依赖健康检查思路
2. 供应链安全主题叠加 `npm_supply_chain_safety`
3. 检查失败：贴关键错误行，给最小修复建议，不声称已绿构建除非工具返回成功

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `npm_supply_chain_safety`

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用project check帮我做一件可验证的小事
- [skill:tool_project_check] 调用工具并给出证据
