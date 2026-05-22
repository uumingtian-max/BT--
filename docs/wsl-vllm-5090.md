# WSL + RTX 5090 跑 vLLM（Nano-Omni）

> 一键入口：`启动-vLLM.bat` 或 `powershell -File scripts\use-vllm.ps1`  
> NPU 小模型：`docs/intel-npu-small-models.md`  
> 分享/协作：`BT项目分享说明.md`（桌面）

## 已修好

| 组件 | 状态 |
| ------ | ------ |
| **NPU embed** | `D:\models\llama-nemotron-embed-1b-v2-ov-npu` 静态 IR，已实测 `device=NPU dim=2048` |
| **ninja** | `/usr/bin/ninja` → miniconda |
| **仅 WSL** | `ensure-vllm.ps1` 不再走 Windows 原生 vLLM |
| **世界级模式** | `AGENT_TIER=world` 见 `backend/agent_world_class.py`，探针 `GET /meta/agent-tier` |

## 5090 卡点（真因）

- 系统 `nvcc` 是 **12.4**，flashinfer 为 **sm_120** JIT 需要 **CUDA ≥ 12.8**
- 日志：`SM 12.x requires CUDA >= 12.9` / `ninja … exit 127`
- 历史笔误：`CUDA_HOME=/us` 会让 JIT 找 `/us/bin/nvcc` — **必须清缓存**

## 一次性修复（WSL root）

```bash
wsl -d Ubuntu -u root bash /mnt/c/Users/ROG/Desktop/ai-agent-project/scripts/install-wsl-cuda129.sh
```

WSL 内清 flashinfer 并预热（gcc-13 + cuda-12.9）：

```bash
wsl -d Ubuntu
rm -rf ~/.cache/flashinfer
export CUDA_HOME=/usr/local/cuda-12.9
export CC=gcc-13 CXX=g++-13 CUDAHOSTCXX=g++-13
python3 /mnt/c/Users/ROG/Desktop/ai-agent-project/scripts/warmup-flashinfer-wsl.py
```

Windows 侧启动整条链路：

```powershell
powershell -File scripts\use-vllm.ps1
# 仅写 .env 不启 vLLM：powershell -File scripts\use-vllm.ps1 -SkipStart
# 换模型：powershell -File scripts\use-vllm.ps1 -ModelDir "D:\models\你的模型"
```

验证：

```powershell
curl.exe http://127.0.0.1:8001/health
curl.exe http://127.0.0.1:8001/v1/models
curl.exe http://127.0.0.1:8000/meta/doctor
```

失败时看 `logs\vllm-wsl.log`。

## GPU 显存（防顶满）

默认：`max-model-len=4096`，`gpu-memory-utilization=0.78`，`max-num-seqs=4`（`scripts/vllm-serve-wsl.sh`）。

## NPU 配置（backend\.env）

由 `use-vllm.ps1` 从 `backend\.env.local-vllm-nano.example` 合并，典型项：

```ini
EMBED_BACKEND=openvino
EMBED_OV_DEVICE=NPU
EMBED_OV_NPU_DIR=D:\models\llama-nemotron-embed-1b-v2-ov-npu
RERANK_ENABLED=1
AGENT_TIER=world
```

导出 embed IR（已完成可跳过）：`scripts/install-embed-npu.ps1` 或 `python scripts\export_llama_bidirec_openvino.py`

## Nemotron Omni 启动失败（你遇到的日志）

| 现象 | 原因 |
| ------ | ------ |
| 卡在 `profiled with 1 video items` 后 `CUDA illegal memory access` | **启动时** MM profiling 在 ~24GB 显存下易爆；用 `--skip-mm-profiling` 跳过探测，**不关闭**聊天识图/视频 |
| Docker + `--cpu-offload-gb 20` + FlashInfer MoE | UVA offload 与 NVFP4 MoE 组合不稳定 |
| `--moe-backend triton` | NVFP4 **不支持** triton，需 flashinfer_cutlass 或 emulation |
| `Model loading took 1.31 GiB` 后手动 `Terminated` | 权重未全进 GPU，进程被中断 |

**推荐（WSL 原生 v0.21，勿 Docker）：**

```bash
bash /mnt/c/Users/ROG/Desktop/ai-agent-project/scripts/start-omni-vllm-wsl.sh
# 或 ChatGPT 同款 eager：
VLLM_ENFORCE_EAGER=1 bash .../scripts/start-omni-vllm-wsl.sh
```

脚本含义：

- `--skip-mm-profiling`：不跑启动阶段「1 条最大分辨率视频」探测（你日志里的崩溃点）
- 仍保留 `--limit-mm-per-prompt` / `--video-pruning-rate`：BT **运行时**可让 Omni 理解图/视频/音频
- **文生视频**仍走 BT 工具 `generate_video`（LongLive 等），不是 Omni 直接吐 MP4

Agent 技能：`backend/agent_skills/nemotron_omni_multimodal.md`

成功标志：`Application startup complete` + `curl.exe http://127.0.0.1:8001/health` → 200

**Docker 若坚持用 v0.20**：加 `--skip-mm-profiling`（若无此参数则勿用 Docker 跑 Omni）；**不要** `--moe-backend triton`；权重挂载用 `/mnt/d/models/...` 不要错路径。

## 禁止

- Windows 原生 vLLM 作为主网关
- Docker 跑 Nemotron Omni 作为主网关（WSL2 GPU 透传 + MM profiling 易炸）
