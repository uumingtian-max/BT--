# ─── ONYX-OVERRIDE 后端 Dockerfile ──────────────────────────
# 基于 Python 3.11 slim，适合 Linux 服务器 / Docker Desktop 部署

FROM python:3.11-slim AS base

# 系统依赖（curl 供 healthcheck，git 供 Skill Creator）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ─── 依赖层（利用 Docker 缓存）─────────────────────────────
COPY requirements-agent-api.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-agent-api.txt

# ─── 应用代码 ────────────────────────────────────────────────
COPY backend/ .

# 创建必要目录
RUN mkdir -p outputs/habit_checks logs

# 不以 root 运行
RUN useradd -m -u 1000 onyx && chown -R onyx:onyx /app
USER onyx

EXPOSE 8000

# 生产模式：2 个 worker，关闭 reload
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]
