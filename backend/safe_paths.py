"""Small path helpers for generated artifacts.

Agent/media endpoints accept paths from model output and HTTP clients.  Keep
those writes inside ``outputs`` so a malformed request cannot overwrite an
arbitrary local file.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = (PROJECT_ROOT / "outputs").resolve()


def safe_output_path(output_path: str | Path, *, default_name: str) -> Path:
    raw = str(output_path or "").strip().strip("\"'")
    if not raw:
        raw = default_name
    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        parts = candidate.parts
        if parts and parts[0].lower() == "outputs":
            candidate = Path(*parts[1:]) if len(parts) > 1 else Path(default_name)
        resolved = (OUTPUTS_DIR / candidate).resolve()
    try:
        resolved.relative_to(OUTPUTS_DIR)
    except ValueError as exc:
        raise ValueError(f"output_path must stay inside {OUTPUTS_DIR}") from exc
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved
