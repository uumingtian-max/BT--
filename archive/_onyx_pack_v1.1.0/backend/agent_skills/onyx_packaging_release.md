# ONYX 打包发布

Triggers: zip,打包,desktop zip,package,发布,onyx_packaging_release,onyx packaging release,onyx-packaging-release,packaging release,ONYX,打包发布

---

**何时使用**：修改、构建、打包或排障 **ONYX 应用本身**（ONYX 打包发布）时**必须**挂载，禁止泛化建议。

## 执行步骤
1. `scripts/package-desktop-zip.ps1` → 桌面 `ONYX-OVERRIDE-v*.zip`
2. 排除 `node_modules`；含 `INSTALL_FIRST_RUN.bat` 与 README
3. 发版前：`npm run build` + `/meta/doctor` 通过

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `node_modules`
- API /meta/doctor

## 自测用语（习惯体检 / 人工抽检）
- ONYX ONYX 打包发布 怎么排障
- [skill:onyx_packaging_release] 按仓库真实路径改一处
