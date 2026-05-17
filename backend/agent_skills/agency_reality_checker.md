# 上线现实检验（agency Reality Checker）

Triggers: 能上线吗,production ready,发布就绪,验收,现实检验,agency_reality_checker,agency reality checker,别吹,有没有真做完,NEEDS WORK,agency-reality-checker,上线现实检验,agency,Reality,Checker

---

**何时使用**：用户问「能不能上线/发布」或要做最终验收。默认 **NEEDS WORK**。来源 agency-agents `testing-reality-checker`。

## 执行步骤

1. 列出声称功能 vs 实际证据（文件、路由、`pytest`、截图、命令输出）
2. 走一条完整用户路径（例：launcher 启动 → 聊天 → 工具调用）
3. 对照原始需求引用，写 gap 表
4. 评级：C+~B+ 诚实分；上线 FAILED / NEEDS WORK / READY
5. 必修项编号 + 验证方式

## 避免

- 无 `run_project_check`/测试/启动证据就标 READY
- 复述前序 agent 的「零问题」不加验证

## ONYX 对接

- `run_project_check` target=all · `GET /meta/doctor` · `launcher/START_APP.bat`

## 自测用语

- 这版能发生产吗，用证据说话
- [skill:agency_reality_checker] 对照 README 验收清单
