# 黑光 · 轻奢 3D 数字人（B 路线）

## 你要的效果

- **不是** NONO / 极客 monospace 大字
- **是** Loro Piana / Aesop 式克制：棕金、衬线、极少文字、电影暗角与颗粒
- **脸** 用真实照片 + 深度置换（Three.js），鼠标驱动轻微 3D 旋转
- **全屏** 用 Electron 窗口最大化或 F11；舞台在 Agent 工作台空态占主视觉

## 一键生成深度图

```powershell
conda activate depth
cd C:\Users\ROG\Desktop\ai-agent-project
# 把你的照片命名为 face.png 放在项目根，或：
python scripts/depth_infer.py -i "D:\path\to\your-portrait.jpg" --device cpu
```

输出：`frontend/public/digital-human/photo.png` + `depth.png`

## RTX 5090（sm_120）

当前稳定版 PyTorch 可能报 `sm_120` 不兼容：

```powershell
pip uninstall torch torchvision -y
pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128
python scripts/depth_infer.py --device cuda
```

或一直用 `--device cpu`（约 10–30 秒/张）。

## 前端开关

`frontend/src/ui_prefs.js`：

- `useDigitalHumanStage: true` — Agent 模式空态显示 3D 舞台
- `useDigitalHumanStage: false` — 回退简约 noir 待命页

改完 `npm run build` 并重启 Electron。

## 下一步（真 3D 说话）

SadTalker / 实时视频流替换 `DigitalHumanStage` 中间 canvas，外层 `DigitalHumanStage.css` 不动。
