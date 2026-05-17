#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${1:-}"
BASE_MODEL="${GEMMA_BASE_MODEL:-/mnt/d/models/Gemma-4-26B-A4B-NVFP4}"
OUT_DIR="${GEMMA_LORA_OUT:-${PROJECT_DIR}/outputs/gemma-lora/onyx-gemma-lora}"

if [[ -z "${DATA_DIR}" ]]; then
  DATA_DIR="$(find "${PROJECT_DIR}/outputs/gemma-evolution" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | tail -n 1 || true)"
fi

if [[ ! -f "${DATA_DIR}/train.jsonl" ]]; then
  echo "Missing dataset: ${DATA_DIR}/train.jsonl"
  echo "Run on Windows first: python scripts/prepare-gemma-evolution-dataset.py"
  exit 2
fi

python - <<'PY'
import importlib.util
missing = [m for m in ("torch", "transformers", "datasets", "peft", "trl", "accelerate") if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit("Missing Python packages: " + ", ".join(missing) + "\nInstall them in your WSL training env, then rerun this script.")
PY

python - "$BASE_MODEL" "$DATA_DIR" "$OUT_DIR" <<'PY'
from __future__ import annotations

import sys

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer

base_model, data_dir, out_dir = sys.argv[1:4]

tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True, use_fast=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def render(example):
    text = tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)
    return {"text": text}

dataset = load_dataset("json", data_files={"train": f"{data_dir}/train.jsonl", "eval": f"{data_dir}/eval.jsonl"})
dataset = dataset.map(render, remove_columns=dataset["train"].column_names)

model = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto",
    trust_remote_code=True,
)

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)

args = TrainingArguments(
    output_dir=out_dir,
    num_train_epochs=1,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    warmup_ratio=0.03,
    logging_steps=5,
    save_steps=50,
    eval_strategy="steps" if len(dataset.get("eval", [])) else "no",
    eval_steps=50,
    bf16=torch.cuda.is_available(),
    report_to=[],
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["eval"] if len(dataset.get("eval", [])) else None,
    peft_config=peft_config,
    args=args,
    dataset_text_field="text",
    max_seq_length=4096,
)
trainer.train()
trainer.save_model(out_dir)
tokenizer.save_pretrained(out_dir)
print(f"Saved LoRA adapter to {out_dir}")
PY
