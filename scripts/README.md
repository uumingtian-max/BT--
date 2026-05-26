# scripts/

按子目录分类；根目录同名文件为**兼容入口**（旧文档/快捷方式仍可用）。

| 目录 | 用途 |
|------|------|
| [`sadtalker/`](sadtalker/) | SadTalker 环境修复、权重下载、口型推理 |
| [`digital-human/`](digital-human/) | Depth Anything → `photo.png` / `depth.png` |
| 根目录其余 `.ps1` / `.py` | 安装、WSL vLLM、Ollama、CI、品牌打包（历史保留） |

## 常用（黑光 3D + 口型）

```powershell
python scripts/digital-human/depth_infer.py --device cpu
python scripts/sadtalker/download_models.py
.\scripts\sadtalker\run_portrait.ps1
```

兼容旧路径：`scripts/depth_infer.py`、`scripts/run_sadtalker_portrait.ps1` 等仍可用。
