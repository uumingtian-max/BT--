# 后端架构（agency Backend Architect）

Triggers: 后端架构,API设计,数据库设计,微服务,扩展性,agency_backend_architect,agency backend architect,FastAPI架构,schema,索引,agency-backend-architect,agency,Backend,Architect

---

**何时使用**：新模块设计、API/DB 方案、性能与可靠性权衡。来源 agency-agents `engineering-backend-architect`。

## 执行步骤

1. 澄清模式：本仓库多为 FastAPI 单体 + SQLite/可选 DB；勿过度微服务
2. 路由：放 `*_routes.py`，前缀见 `main.py`；Pydantic 模型边界校验
3. DB：索引、迁移思路、软删；查询避免 N+1
4. 可靠性：超时、重试、断路；错误不泄露内部细节
5. 安全与观测：鉴权中间件、结构化日志、/meta/doctor 可诊断

## 避免

- 无测量就承诺「百万 QPS」
- 破坏现有 API 契约却不版本化

## ONYX 对接

- `fastapi_route_debug` · `read_file`/`write_file` · `run_project_check`

## 自测用语

- [skill:agency_backend_architect] 设计技能包检索 API 扩展
- 订单流 SQLite 表与索引建议
