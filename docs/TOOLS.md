# Agent 工具系统

本文档用于维护 `/agent/tools` 暴露的 Agent 工具清单、分组和后续扩展规范。

## 当前工具分组

后端工具入口位于 `backend/agent.py` 的 `TOOL_MAP`，前端和自检接口通过 `GET /agent/tools` 读取工具清单。

| 分组 | 工具 |
| --- | --- |
| 搜索与抓取 | `web_search`, `local_search`, `local_scrape_url` |
| 文件与代码 | `read_file`, `write_file`, `list_files`, `execute_python` |
| 画像与编排 | `get_device_profile`, `get_recent_desktop_files`, `get_recent_work_summary`, `get_evolution_profile`, `run_task_orchestration` |
| 知识与媒体 | `notebook_ingest`, `notebook_synthesize`, `generate_image`, `generate_video`, `generate_ai_video`, `text_to_speech`, `run_project_check` |
| 桌面控制 | `open_url`, `open_path`, `get_foreground_window`, `list_windows`, `focus_window`, `send_hotkey`, `type_text`, `click_screen` |
| 浏览器自动化 | `browser_navigate`, `browser_screenshot`, `browser_click_and_extract`, `browser_fill_form` |
| 并行子 Agent | `run_parallel_subagents` |
| 集成 | `http_request`, `query_database`, `mcp_invoke` |

## 新增工具规范

新增工具时，至少完成以下事项：

1. 在 `backend/agent.py` 中增加执行函数。
2. 在 `TOOL_MAP` 注册工具名。
3. 在 `TOOLS_DESC` 写清用途和参数。
4. 在 `list_tools()` 的分组里加入工具。
5. 增加测试，确保工具存在、参数异常时不会让 Agent 崩溃。
6. 如果工具有写入、执行命令、打开外部程序、网络请求等副作用，必须标注风险，并尽量增加确认机制。

## 推荐的工具元数据结构

后续建议把 `TOOL_MAP` 升级为结构化 registry：

```python
{
    "name": "read_file",
    "description": "读取本地文件内容",
    "group": "files_code",
    "risk_level": "safe",
    "timeout_seconds": 30,
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"}
        },
        "required": ["path"]
    },
    "handler": read_file,
}
```

建议风险等级：

| 等级 | 说明 | 示例 |
| --- | --- | --- |
| `safe` | 只读或低风险 | `read_file`, `list_files`, `get_device_profile` |
| `confirm` | 有副作用但通常可恢复 | `write_file`, `open_url`, `type_text` |
| `dangerous` | 执行代码、控制桌面、访问数据库或外部系统 | `execute_python`, `query_database`, `click_screen`, `mcp_invoke` |

## 工具执行质量要求

工具函数应该遵守：

- 输入为空时返回明确错误，例如 `read_file error: missing path`。
- 捕获可预期异常，不把堆栈直接暴露给用户。
- 长结果交给 `compress_tool_result_for_llm()` 压缩。
- 所有路径类工具必须走安全路径解析，避免越权读写。
- 网络/浏览器/执行代码类工具必须设置超时。

## `/agent/tools` 后续升级目标

当前接口返回 `tools`, `count`, `groups`。建议升级为：

```json
{
  "tools": [
    {
      "name": "read_file",
      "group": "files_code",
      "description": "读取本地文件内容",
      "risk_level": "safe",
      "input_schema": {},
      "enabled": true
    }
  ],
  "count": 36,
  "groups": {}
}
```

这样前端可以直接展示工具说明、风险提示和参数表单。
