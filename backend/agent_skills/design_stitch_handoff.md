# 设计稿 → 代码交接（Stitch / MCP 思路）

Triggers: stitch,stitch-mcp,设计稿,figma,ui handoff,界面还原,davideast,设计转代码,mcp design,design_stitch_handoff,design stitch handoff,design-stitch-handoff,代码交接,MCP,思路,设计稿还原,ui实现

---

**何时使用**：用户意图与「设计稿 → 代码交接（Stitch / MCP 思路）」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 布局：栅格、断点、主色/字阶（可引用项目 CSS 变量如 `--bg`/`--accent`）
2. 组件清单：每个组件状态（默认/hover/disabled/loading）
3. 资源：图标尺寸档、是否已有 `BrandLogo`/`hero.png` 品牌素材
4. 验收：3 条可目视检查项（对齐、对比度、空状态）
5. 实现约束：优先改 `frontend/src` 现有 class；不引入新 UI 库除非用户要求

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## 关联技能
- `stitch_mcp_ui`
- `onyx_frontend_react`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「设计稿 → 代码交接（Stitch / MCP 思路）」相关的事
- [skill:design_stitch_handoff] 执行一步可验证操作
