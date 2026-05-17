# 开发与维护指南

本文档用于统一 ONYX-OVERRIDE 的本地开发、检查、提交和发布流程。

## 环境要求

| 依赖 | 建议版本 |
| --- | --- |
| Python | 3.10+ |
| Node.js | 18+，推荐 20 LTS |
| npm | 随 Node 安装 |
| Ollama / vLLM | 按实际模型路线选择 |

## 首次安装

```bash
git clone https://github.com/uumingtian-max/ai-agent-project.git
cd ai-agent-project

pip install -r requirements-agent-api.txt
cd frontend && npm install && cd ..

cp backend/.env.example backend/.env
```

## 常用启动命令

```bash
python start.py             # 桌面应用
python start.py dev         # 后端 hot reload + 前端 dev server
python start.py backend     # 仅后端
python start.py mobile      # 局域网 / Tailscale 访问
npm run start               # 仅 Electron
npm run dev --prefix frontend
npm run build --prefix frontend
```

## 提交前检查

建议每次提交前执行：

```bash
python -m py_compile start.py backend/main.py backend/agent.py backend/env_bootstrap.py
ruff check backend/
ruff format --check backend/
pytest backend/tests/ -v --tb=short
npm run build --prefix frontend
```

如果本地没有安装 `ruff` 或 `pytest`：

```bash
pip install ruff pytest pytest-asyncio httpx
```

## CI 规则

GitHub Actions 会检查：

1. Python 3.10 / 3.11 / 3.12 后端基础检查。
2. Ruff lint 和 format check。
3. Python 关键入口编译。
4. 后端测试目录存在时运行 `pytest backend/tests/`。
5. 前端 `npm ci` 和 `npm run build`。
6. Python 依赖安全扫描和 gitleaks 密钥扫描。

测试失败不应该被吞掉。只有 `backend/tests` 目录不存在时，CI 才跳过测试。

## 分支建议

| 分支 | 用途 |
| --- | --- |
| `main` | 稳定可运行版本 |
| `dev` | 日常开发集成 |
| `feature/*` | 单个功能或修复 |
| `fix/*` | 小型缺陷修复 |
| `docs/*` | 文档整理 |

## 新增 API 的流程

1. 在后端添加路由或 service。
2. 增加 Pydantic 请求/响应 schema。
3. 增加测试。
4. 更新 README 的 API 表。
5. 如果前端调用，封装到前端 API 层。

## 新增 Agent 工具的流程

1. 阅读 `docs/TOOLS.md`。
2. 给工具定义清楚参数、结果和风险等级。
3. 在 `TOOL_MAP` 注册。
4. 在 `/agent/tools` 分组中暴露。
5. 增加异常测试。
6. 对写文件、执行代码、桌面控制、外部请求类工具增加确认或限制。

## 安全约定

- `.env` 不进仓库。
- 密钥只从环境变量读取。
- 不在日志里打印 API key、cookie、token。
- 文件读写必须限制在可控目录内。
- 命令执行和桌面控制类能力必须尽量可审计。
- 对外访问时必须配置 `MOBILE_ACCESS_TOKEN` 和收紧 CORS。

## 发布检查清单

发布前确认：

- [ ] `python start.py backend` 能启动。
- [ ] `/health` 返回 `{ "status": "ok" }`。
- [ ] `/agent/tools` 返回工具数量和分组。
- [ ] `npm run build --prefix frontend` 通过。
- [ ] GitHub Actions 全绿。
- [ ] README、docs 与实际命令一致。
