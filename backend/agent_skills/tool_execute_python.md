# 工具：execute_python

Triggers: execute_python,跑脚本,验证,python REPL,tool_execute_python,tool execute python,tool-execute-python,execute python,工具,运行python,执行代码,跑一下,工具execute python,验证脚本

---

**何时使用**：用户需要 **短 Python 验证脚本**（工具 `execute_python`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 仅短脚本验证（断言、解析、小实验）；长任务拆步
2. 副作用（写盘、删文件）需用户意图明确；失败贴**完整 traceback** 再缩小范围重试

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## 关联技能
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用execute python帮我做一件可验证的小事
- [skill:tool_execute_python] 调用工具并给出证据
