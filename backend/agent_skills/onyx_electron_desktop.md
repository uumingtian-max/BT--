# ONYX Electron 桌面

Triggers: electron,main.js,桌面应用,shortcut,图标,onyx_electron_desktop,onyx electron desktop,onyx-electron-desktop,electron desktop,ONYX,桌面

---

**何时使用**：修改、构建、打包或排障 **ONYX 应用本身**（ONYX Electron 桌面）时**必须**挂载，禁止泛化建议。

## 执行步骤
1. `electron/main.js`：后端健康等待、`ensureOllama`
2. 快捷方式：`Launch-ONYX-OVERRIDE.vbs` + `scripts/create-desktop-shortcut.ps1`
3. 图标：`electron/icon.ico`、 branding 脚本 `scripts/build-branding.py`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## 自测用语（习惯体检 / 人工抽检）
- ONYX ONYX Electron 桌面 怎么排障
- [skill:onyx_electron_desktop] 按仓库真实路径改一处
