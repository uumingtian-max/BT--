# ONYX 前端 React

Triggers: frontend,react,App.js,OperatorPanels,侧栏,onyx_frontend_react,onyx frontend react,onyx-frontend-react,frontend react,ONYX,前端

---

**何时使用**：修改、构建、打包或排障 **ONYX 应用本身**（ONYX 前端 React）时**必须**挂载，禁止泛化建议。

## 执行步骤
1. 路径 `frontend/src/`；构建 `npm run build`
2. Electron 资源用 `assetUrl()`（见 `BrandLogo.js`）；改 UI 保持现有 CSS 变量与侧栏结构
3. 技能面板读 `/meta/skills`，勿写死技能数量

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- API /meta/skills

## 自测用语（习惯体检 / 人工抽检）
- ONYX ONYX 前端 React 怎么排障
- [skill:onyx_frontend_react] 按仓库真实路径改一处
