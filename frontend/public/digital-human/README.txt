黑光 · 3D 数字人资源目录
========================

本目录 photo.png / depth.png 不入 Git（隐私 + 体积）。换脸只改本机文件。

1. 肖像 → photo.png
   复制你的照片到：
   frontend/public/digital-human/photo.png

2. 深度图（conda depth）：
   conda activate depth
   cd C:\Users\ROG\Desktop\ai-agent-project
   python scripts/depth_infer.py --device cpu

3. SadTalker 权重（conda sadtalker，从项目根跑）：
   conda activate sadtalker
   python scripts/sadtalker_download_models.py
   .\scripts\run_sadtalker_portrait.ps1

4. 前端/Electron 读取 photo.png + depth.png；口型视频接通后替换为 SadTalker MP4 流。
