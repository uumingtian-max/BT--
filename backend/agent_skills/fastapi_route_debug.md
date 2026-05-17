# FastAPI 路由调试

Triggers: fastapi,uvicorn,422,路由,backend 调试,fastapi_route_debug,fastapi route debug,fastapi-route-debug,路由调试,500错误,接口报错,后端挂了

---

**何时使用**：用户意图与「FastAPI 路由调试」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 路由分散在 `*_routes.py`；统一前缀见 `main.py`
2. 500 时贴 traceback 片段；用 `/meta/doctor` 查 DB 与 Ollama

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- API /meta/doctor

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「FastAPI 路由调试」相关的事
- [skill:fastapi_route_debug] 执行一步可验证操作
