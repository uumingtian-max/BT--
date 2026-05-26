# 仓库整改说明（2026-05）

## 做了什么

1. **脚本分舱**：`scripts/sadtalker/`、`scripts/digital-human/`；根目录保留兼容入口。
2. **文档分舱**：`docs/design/`（白龙马++ 等）、`docs/digital-human/`。
3. **演示页**：`frontend/public/demos/`（`blacklight_3d_final.html` 等），默认 UI 不依赖。
4. **技能进化接线**：`backend/user_skills/*.md` 现由 `skill_pack` 加载（同名覆盖 `agent_skills`）。
5. **`.gitignore` 加强**：本地 venv、模型 partial、SadTalker 权重目录等。

## 仍在本机、不进 Git

- `SadTalker/checkpoints/`、肖像 `photo.png` / `depth.png`
- `backend/.env`、`data/`、数据库
- `archive/`、`vendor/*/` 克隆体

## 下一步（产品精华）

见 [design/BAILONGMA_PLUS_3D_AGENT.md](design/BAILONGMA_PLUS_3D_AGENT.md)：TICK 常驻、super_memory 上屏、SadTalker 视频流接入 Electron。
