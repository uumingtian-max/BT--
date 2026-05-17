# Gemma 进化训练流程

这套流程分两层：

1. **安全进化数据集**：从 `memory.db` 的 playbook、`workflow.db` 的任务复盘、`backend/agent_skills/*.md` 导出 chat JSONL。
2. **可选 LoRA 微调**：在 WSL/Linux GPU 环境里用导出的 JSONL 训练 Gemma LoRA adapter。

默认不会改原始 Gemma 权重，也不会动正在运行的 vLLM/Ollama 服务。

## 1. 导出训练数据

Windows 里运行：

```powershell
python scripts\prepare-gemma-evolution-dataset.py
```

或双击：

```text
TRAIN_GEMMA_EVOLVE_DATASET.bat
```

输出位置类似：

```text
outputs/gemma-evolution/20260517-030000/
  train.jsonl
  eval.jsonl
  manifest.json
```

每行是：

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}],"source":"workflow.review","meta":{}}
```

脚本会过滤常见 token/API key、明显坏样本和超长噪声，但训练前仍建议抽查 `train.jsonl`。

## 2. 训练 LoRA（可选）

### Windows / 本机 quant 环境

如果 `C:\Users\ROG\miniconda3\envs\quant` 已有 CUDA 版 PyTorch，可直接运行：

```powershell
C:\Users\ROG\miniconda3\envs\quant\python.exe scripts\train-gemma-lora-windows.py
```

或双击：

```text
TRAIN_GEMMA_LORA_WINDOWS.bat
```

### WSL/Linux

在 WSL/Linux GPU 环境中准备依赖：

```bash
pip install torch transformers datasets accelerate peft trl
```

然后运行：

```bash
export GEMMA_BASE_MODEL=/mnt/d/models/Gemma-4-26B-A4B-NVFP4
bash scripts/train-gemma-lora-wsl.sh /mnt/c/Users/ROG/Desktop/ai-agent-project/outputs/gemma-evolution/你的数据目录
```

产物默认写到：

```text
outputs/gemma-lora/onyx-gemma-lora/
```

## 3. 接回 Gemma 服务

训练完成后，优先先单独验证 adapter 输出质量。确认稳定后，再考虑用 vLLM/Transformers 加载 base model + LoRA adapter。

如果只是想让 ONYX 更懂你的习惯，通常先用“导出数据 + playbook 蒸馏 + 技能扩展”就够了；真正 LoRA 适合样本量明显增加后再做。
