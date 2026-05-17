# API 测试（agency API Tester）

Triggers: API测试,接口测试,pytest api,422,401,429,agency_api_tester,agency api tester,OpenAPI,契约测试,负载测试,agency-api-tester,测试,agency,Tester

---

**何时使用**：验证 FastAPI 路由、鉴权、错误码与性能。来源 agency-agents `testing-api-tester`，对齐本仓库 `backend/tests/`。

## 执行步骤

1. 从 `main.py` / `*_routes.py` 列端点与鉴权要求
2. 功能：正常/边界/非法输入 → 期望状态码与 body
3. 安全：无 token 401、注入样例不 500、敏感字段不出响应
4. 跑 `pytest backend/tests/`；失败贴真实 traceback
5. 性能：关键路径记录耗时；>3s 或错误率异常标风险

## 避免

- 未跑测试就写 PASS
- 在生产 URL 上做破坏性压测（除非用户明确授权）

## ONYX 对接

- `http_request` · `fastapi_route_debug` · `/meta/doctor`

## 自测用语

- [skill:agency_api_tester] 测 /agent/run 与 /meta/skills
- 新路由加 pytest 用例清单
