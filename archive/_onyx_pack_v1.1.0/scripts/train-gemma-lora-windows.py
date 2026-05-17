from __future__ import annotations

import os
import sys
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoTokenizer, DataCollatorForLanguageModeling
from trl import SFTConfig, SFTTrainer


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOT = ROOT / "outputs" / "gemma-evolution"


def latest_dataset() -> Path:
    candidates = [p for p in DEFAULT_DATA_ROOT.glob("*") if (p / "train.jsonl").exists()]
    if not candidates:
        raise SystemExit("No dataset found. Run scripts\\prepare-gemma-evolution-dataset.py first.")
    return sorted(candidates)[-1]


def main() -> int:
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_dataset()
    base_model = Path(os.environ.get("GEMMA_BASE_MODEL", r"D:\models\Gemma-4-26B-A4B-NVFP4"))
    out_dir = Path(os.environ.get("GEMMA_LORA_OUT", str(ROOT / "outputs" / "gemma-lora" / "onyx-gemma-lora")))
    max_steps = int(os.environ.get("GEMMA_TRAIN_MAX_STEPS", "0"))

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available in this Python environment.")
    if not base_model.exists():
        raise SystemExit(f"Missing base model: {base_model}")
    if not (data_dir / "train.jsonl").exists():
        raise SystemExit(f"Missing train.jsonl in {data_dir}")

    tokenizer = AutoTokenizer.from_pretrained(str(base_model), trust_remote_code=True, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dataset = load_dataset(
        "json",
        data_files={
            "train": str(data_dir / "train.jsonl"),
            "eval": str(data_dir / "eval.jsonl"),
        },
    )

    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj.linear", "k_proj.linear", "v_proj.linear", "o_proj.linear"],
    )

    args = SFTConfig(
        output_dir=str(out_dir),
        num_train_epochs=1,
        max_steps=max_steps if max_steps > 0 else -1,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=1e-4,
        warmup_ratio=0.03,
        logging_steps=2,
        save_strategy="steps",
        save_steps=25,
        save_total_limit=2,
        eval_strategy="steps" if len(dataset["eval"]) else "no",
        eval_steps=25,
        bf16=True,
        tf32=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        report_to=[],
        max_length=2048,
        packing=False,
        dataset_kwargs={"skip_prepare_dataset": False},
        model_init_kwargs={
            "torch_dtype": torch.bfloat16,
            "device_map": "auto",
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        },
    )

    base_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    def collate_with_text_mm_token_types(features):
        batch = base_collator(features)
        if "mm_token_type_ids" not in batch:
            batch["mm_token_type_ids"] = torch.zeros_like(batch["input_ids"])
        return batch

    trainer = SFTTrainer(
        model=str(base_model),
        args=args,
        data_collator=collate_with_text_mm_token_types,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"] if len(dataset["eval"]) else None,
        processing_class=tokenizer,
        peft_config=peft_config,
    )
    trainer.train()
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    print(f"Saved LoRA adapter to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
