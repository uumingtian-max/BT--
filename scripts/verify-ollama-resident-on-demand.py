#!/usr/bin/env python3
"""Smoke: 4 resident models config + coder on-demand load/unload (needs ollama serve)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from env_bootstrap import load_backend_dotenv

load_backend_dotenv()

from model_router import select_model
from ollama_pins import (
    ensure_on_demand_loaded,
    is_on_demand_model,
    on_demand_models,
    release_on_demand_model,
    resident_models_from_env,
    warm_all_pinned_models,
)


def ollama_ps_models() -> set[str]:
    try:
        out = subprocess.check_output(["ollama", "ps"], text=True, encoding="utf-8", errors="replace")
    except Exception as exc:
        print(f"SKIP ollama ps: {exc}")
        return set()
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if len(lines) < 2:
        return set()
    names: set[str] = set()
    for ln in lines[1:]:
        parts = ln.split()
        if parts:
            names.add(parts[0])
    return names


def main() -> int:
    errors: list[str] = []

    resident = resident_models_from_env()
    on_demand = on_demand_models()
    print("resident:", resident)
    print("on_demand:", on_demand)

    if len(resident) != 4:
        errors.append(f"expected 4 resident, got {len(resident)}: {resident}")
    if "deepseek-coder-v2:16b" not in on_demand:
        errors.append("coder missing from on_demand list")

    m, reason = select_model("重构整个 backend 多文件架构")
    if reason != "code" or "coder" not in m:
        errors.append(f"heavy code route expected coder, got {m!r} {reason!r}")
    else:
        print("router heavy code ->", m, reason)

    m2, r2 = select_model("写个 hello world")
    if r2 != "code_simple":
        errors.append(f"simple code expected code_simple, got {m2!r} {r2!r}")
    else:
        print("router simple code ->", m2, r2)

    if not is_on_demand_model("deepseek-coder-v2:16b"):
        errors.append("is_on_demand_model(coder) should be True")

    if os.environ.get("OLLAMA_VERIFY_SKIP_WARM", "").strip() not in ("1", "true", "yes"):
        warm = warm_all_pinned_models()
        print("warm:", json.dumps(warm, ensure_ascii=False))
        if warm.get("failed"):
            errors.append(f"warm failed: {warm['failed']}")
    else:
        print("warm: skipped (OLLAMA_VERIFY_SKIP_WARM)")

    coder = on_demand[0]
    before = ollama_ps_models()
    print("ps before coder load:", sorted(before))

    if not ensure_on_demand_loaded(coder):
        errors.append(f"ensure_on_demand_loaded failed for {coder}")
    else:
        after_load = ollama_ps_models()
        print("ps after coder load:", sorted(after_load))
        if coder not in after_load and not any(coder.split(":")[0] in x for x in after_load):
            errors.append(f"coder not visible in ollama ps after load: {after_load}")

    import time

    if not release_on_demand_model(coder):
        errors.append(f"release_on_demand_model failed for {coder}")
    else:
        time.sleep(2)
        after_release = ollama_ps_models()
        print("ps after coder release:", sorted(after_release))
        if coder in after_release or any("deepseek-coder" in x for x in after_release):
            errors.append(f"coder still loaded after release: {after_release}")

    if errors:
        print("\nFAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print("\nOK: resident/on-demand + router + coder load/unload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
