# Nemotron Omni 多模态（图 / 视频 / 音频理解）

Triggers: 看视频,分析视频,视频里,截图分析,识图,看图,听这段音频,多模态,Omni,上传视频,理解画面,视频内容,图片里有什么,nemotron omni,omni 多模态

---

**何时使用**：用户要让 Agent **理解**本地图片/视频/音频内容（不是单纯文生视频）。

## BT 视频能力（真实，两层）

| 能力 | 工具/链路 | 真实程度 |
| ------ | --------- | -------- |
| **理解**图/视频/音 | vLLM :8001 + 用户上传附件 → `mm_openai_payload` 多模态 | ✅ 需 health=200；❌ vLLM 未起时禁止说已分析 |
| **生成**幻灯片 | `generate_video(image_paths=...)` | ✅ imageio 出真 mp4 |
| **文生 AI 视频** | `generate_video(prompt=...)` | ❌ 默认占位动画；LongLive **未接入**代码 |

禁止：vLLM 未启动却描述视频内容；把占位视频说成 LongLive/Wan 生成。

## 执行步骤（理解类）

1. 用户应通过界面上传附件（API `attachments` 字段）；不要依赖 prompt 里的 `local_path` 文字。
2. 需要系统/显存状态时先 `pc_health_snapshot` 或 `get_gpu_status`。
3. 向用户说明：vLLM 网关需已启动（`:8001/health`）；大视频建议先让用户提供较短片段或降低分辨率。
4. 若仅生成视频：走 `generate_video`，输出 `outputs/` 下路径。

## vLLM 启动说明（给维护者）

- `--skip-mm-profiling`：**只跳过启动时**「最大分辨率 video profiling」（避免 WSL 24GB 显存 illegal access）。
- **不关闭**运行时多模态：启动脚本仍带 `--limit-mm-per-prompt`、`--video-pruning-rate` 等，聊天可附图/视频。
- 若启动仍失败，用 `VLLM_ENFORCE_EAGER=1` 再试；勿用 Docker + cpu-offload 跑 Omni 主网关。

## 避免

- 未启动 vLLM 就声称「已分析视频内容」。
- 把 `generate_video` 生成结果说成 Omni 原生输出。
- 隐私模式下把视频内容外发到 `web_search`。

## 自测用语

- 帮我分析下载文件夹里这个 mp4 讲了什么（需附路径）
- 根据这几张截图总结界面问题
- 生成一段 5 秒科技感片头（应走 generate_video）
