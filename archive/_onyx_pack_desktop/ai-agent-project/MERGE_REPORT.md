# AI Agent 合并清单

生成时间：2026-05-15 14:16:54

## 主项目
- 保留唯一主项目：C:\Users\ROG\Desktop\ai-agent-project

## 已合并进 imported-assets
- ai-agent-system 文档/命令脚本：imported-assets\ai-agent-system-docs
- ai-agent-system PowerShell 脚本：imported-assets\ai-agent-system-scripts
- model_v6 小模型资产：imported-assets\model_v6
- daily-self-learning 记录：imported-assets\daily-self-learning

## 未合并的大体积/运行时资产
- C:\Users\ROG\.ollama：Ollama 正式模型仓，保留，不并入项目
- ai-agent-system\ollama-standalone-v0.23.3-test：独立 Ollama 测试版，待确认是否删除
- ai-agent-system\ollama-windows-*.zip：安装包缓存，可删除
- ai-agent-system\*.log / *.err.log：拉模型和测试日志，可删除
- .codex/.cursor/.claude：工具自身状态，不并入，不直接删除

## 下一步建议
1. 清理 ai-agent-project 内部缓存：__pycache__、.pytest_cache、tmp-agent*.log、前端构建缓存。
2. 确认后删除 ai-agent-system 中重复/缓存目录。
3. 保留 .ollama 和 quant 环境。
