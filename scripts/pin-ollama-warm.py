"""Warm all resident Ollama models (called from pin-ollama-models.ps1)."""
# pyright: reportMissingImports=false
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from env_bootstrap import load_backend_dotenv

load_backend_dotenv()

from ollama_pins import keep_alive_duration, role_map_for_ui, warm_all_pinned_models

result = warm_all_pinned_models()
print("keep_alive:", keep_alive_duration())
print("strict_roles:", result.get("strict_roles"))
print(json.dumps(result, ensure_ascii=False, indent=2))
print("--- 岗位表 ---")
for row in role_map_for_ui():
    tag = row.get("pin", "resident")
    print(f"  {row['model']}: {row['role']} · {tag}")

expected = int(result.get("ps_expected") or 0)
got = int(result.get("ps_count") or 0)
primary = (result.get("primary_model") or "").strip()
loaded = result.get("ps_loaded") or []
on_demand = result.get("on_demand") or []

if primary and primary in loaded:
    print(f"\n[OK] 主脑 {primary} 已在显存（Ollama 单卡通常只显示 1 行，属正常）", file=sys.stderr)
elif got == 0:
    print("\n[警告] 显存里没有常驻模型，请确认 Ollama 已启动。", file=sys.stderr)
elif expected and got < expected:
    print(
        f"\n[提示] ollama ps 仅 {got}/{expected} 行；当前: {loaded}。"
        f" 若主脑不是 {primary or 'qwen3.5:9b'}，请再执行一次 pin（已按主脑最后预热）。",
        file=sys.stderr,
    )
    if on_demand:
        print(f"  按需模型（写码时自动加载）: {', '.join(on_demand)}", file=sys.stderr)
