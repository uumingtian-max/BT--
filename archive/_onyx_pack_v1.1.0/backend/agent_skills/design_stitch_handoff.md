# 设计稿 → 代码交接（Stitch / MCP 思路）

Triggers: stitch,stitch-mcp,设计稿,figma,ui handoff,界面还原,davideast,设计转代码,mcp design

对标 **Stitch MCP**：把设计意图**结构化**再进代码库，避免「凭感觉写 UI」。

**交接清单（必须齐全再写代码）**：

1. 布局：栅格、断点、主色/字阶（可引用项目 CSS 变量如 `--bg`/`--accent`）。
2. 组件清单：每个组件状态（默认/hover/disabled/loading）。
3. 资源：图标尺寸档、是否已有 `BrandLogo`/`hero.png` 品牌素材。
4. 验收：3 条可目视检查项（对齐、对比度、空状态）。
5. 实现约束：优先改 `frontend/src` 现有 class；不引入新 UI 库除非用户要求。

**工具**：需要抓参考页时用 `browser_screenshot`；静态资源放 `frontend/public/`。

**禁止**：未给设计约束就大批量改 CSS；禁止删除现有品牌图标管线 `build-branding.py`。
