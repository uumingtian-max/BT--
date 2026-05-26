# SadTalker 脚本

| 文件 | 说明 |
|------|------|
| `download_models.py` | 下载 checkpoints + gfpgan/facexlib 权重到 `../SadTalker/` |
| `fix_env.py` | basicsr 补丁 + setuptools（librosa/pkg_resources） |
| `patch_basicsr.py` | 单独打 torchvision 兼容补丁 |
| `run_portrait.ps1` | 用 `frontend/public/digital-human/photo.png` 跑测试 MP4 |

需本机已 clone [SadTalker](https://github.com/OpenTalker/SadTalker) 到项目根 `SadTalker/`（目录在 `.gitignore`）。
