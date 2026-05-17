# 应用安全工程（agency Security Engineer）

Triggers: 安全审查,威胁建模,OWASP,注入,XSS,鉴权,IDOR,agency_security_engineer,agency security engineer,渗透自查,漏洞,secrets泄露,agency-security-engineer,应用安全工程,agency,Security,Engineer

---

**何时使用**：安全审查、威胁建模、上线前安全门禁；与 `security_local_audit` 互补（本技能偏代码与架构）。来源 agency-agents `engineering-security-engineer`。

## 执行步骤

1. 画信任边界：浏览器 → FastAPI → DB/外部 API → llama 网关
2. 对每条数据流问：可滥用？失败是否安全？爆炸半径？
3. 查 OWASP Top 10 / API Top 10：注入、鉴权、敏感数据暴露、错误信息泄露
4. 密钥：仅 `backend/.env`；扫描勿提交 token；拒绝未授权渗透
5. 输出：严重度 + 利用路径 + **可粘贴修复**（优先 Pydantic/参数化查询）

## 避免

- 建议关闭 WAF/CORS/校验来「先跑通」
- 自研加密；硬编码 API Key
- 无证据声称「零漏洞」

## ONYX 对接

- `run_project_check` · `GET /meta/doctor` · 技能 `security_local_audit`

## 自测用语

- [skill:agency_security_engineer] 审查登录与 API 鉴权
- 威胁建模：用户上传附件到 Agent 的路径
