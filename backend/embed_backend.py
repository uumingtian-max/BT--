"""Unified text embedding: OpenVINO NPU (Windows) or Ollama fallback."""

from __future__ import annotations

import json
import logging
import math
import os
import threading
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_OV_RUNTIME: dict[str, Any] | None = None


def embed_backend_name() -> str:
    return (os.environ.get("EMBED_BACKEND") or "ollama").strip().lower()


def _env_path(key: str, default: str = "") -> Path | None:
    raw = (os.environ.get(key) or default).strip()
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_dir() else None


def _ov_model_dir() -> Path | None:
    for key in ("EMBED_OV_NPU_DIR", "EMBED_OV_DIR", "EMBED_LOCAL_DIR"):
        p = _env_path(key)
        if p and (p / "openvino_model.xml").is_file():
            return p
    return None


def _ov_device() -> str:
    return (os.environ.get("EMBED_OV_DEVICE") or "NPU").strip().upper()


def _ollama_base_url() -> str:
    return (os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")


def _ollama_embed_model() -> str:
    return (
        os.environ.get("SKILL_EMBED_MODEL")
        or os.environ.get("EMBED_MODEL")
        or "nomic-embed-text"
    ).strip()


def _ollama_embed_one(text: str) -> list[float]:
    model = _ollama_embed_model()
    timeout = float(os.environ.get("SKILL_EMBED_TIMEOUT_SEC", "8") or "8")
    payload = {"model": model, "input": text}
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(f"{_ollama_base_url()}/api/embed", json=payload)
        if resp.status_code == 404:
            resp = client.post(
                f"{_ollama_base_url()}/api/embeddings",
                json={"model": model, "prompt": text},
            )
        resp.raise_for_status()
        data = resp.json()
    if isinstance(data.get("embeddings"), list) and data["embeddings"]:
        return [float(x) for x in data["embeddings"][0]]
    if isinstance(data.get("embedding"), list):
        return [float(x) for x in data["embedding"]]
    raise RuntimeError("Ollama embedding response missing embedding vector")


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 0:
        return vec
    return [x / norm for x in vec]


def _mean_l2_pool(token_vecs: Any, attention_mask: Any) -> list[float]:
    import numpy as np

    arr = np.asarray(token_vecs, dtype=np.float32)
    mask = np.asarray(attention_mask, dtype=np.float32)
    if arr.ndim == 3:
        if mask.ndim == 1:
            mask = mask.reshape(1, -1)
        weights = mask[..., None]
        denom = float(weights.sum()) or 1.0
        pooled = (arr * weights).sum(axis=1) / denom
        vec = pooled[0]
    elif arr.ndim == 2:
        vec = arr[0] if arr.shape[0] == 1 else arr.mean(axis=0)
    else:
        vec = arr.reshape(-1)
    return _l2_normalize(vec.tolist())


def _load_openvino_runtime() -> dict[str, Any]:
    global _OV_RUNTIME
    if _OV_RUNTIME is not None:
        return _OV_RUNTIME

    model_dir = _ov_model_dir()
    if model_dir is None:
        raise FileNotFoundError(
            "OpenVINO embed dir missing or no openvino_model.xml "
            "(set EMBED_OV_NPU_DIR)"
        )

    meta_path = model_dir / "bt_embed_meta.json"
    seq_len = 512
    pooling = "mean_l2"
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            seq_len = int(meta.get("seq_len") or seq_len)
            pooling = str(meta.get("pooling") or pooling)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    from openvino import Core
    from transformers import AutoTokenizer

    device = _ov_device()
    core = Core()
    last_err: Exception | None = None
    compiled = None
    for candidate in (device, "CPU"):
        try:
            compiled = core.compile_model(
                str(model_dir / "openvino_model.xml"),
                candidate,
            )
            device = candidate
            break
        except Exception as e:
            last_err = e
    if compiled is None:
        raise RuntimeError(f"OpenVINO compile failed: {last_err}") from last_err

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
    _OV_RUNTIME = {
        "model_dir": model_dir,
        "device": device,
        "compiled": compiled,
        "tokenizer": tokenizer,
        "seq_len": seq_len,
        "pooling": pooling,
    }
    logger.info(
        "embed openvino ready dir=%s device=%s dim_probe=ok",
        model_dir,
        device,
    )
    return _OV_RUNTIME


def _openvino_embed_one(text: str) -> list[float]:
    import numpy as np

    with _LOCK:
        rt = _load_openvino_runtime()

    enc = rt["tokenizer"](
        text,
        padding="max_length",
        truncation=True,
        max_length=int(rt["seq_len"]),
        return_tensors="np",
    )
    inputs = {
        k: np.asarray(v, dtype=np.int64)
        for k, v in enc.items()
        if k in ("input_ids", "attention_mask")
    }
    result = rt["compiled"](inputs)
    if hasattr(result, "__getitem__"):
        try:
            out = result[0]
        except (KeyError, TypeError):
            out = result[list(result)[0]]
    else:
        out = result

    arr = np.asarray(out, dtype=np.float32)
    if arr.ndim == 2 and arr.shape[-1] == 2048 and arr.shape[0] == 1:
        return _l2_normalize(arr[0].tolist())
    if arr.ndim == 3:
        return _mean_l2_pool(arr, inputs["attention_mask"])
    flat = arr.reshape(-1).tolist()
    return _l2_normalize(flat)


def embed_one(text: str) -> list[float]:
    """Return embedding vector for *text* using configured backend."""
    backend = embed_backend_name()
    if backend in ("openvino", "ov", "npu"):
        try:
            return _openvino_embed_one(text)
        except Exception as e:
            logger.warning("OpenVINO embed failed, falling back to Ollama: %s", e)
    return _ollama_embed_one(text)


def embed_status(*, probe: bool = False) -> dict[str, object]:
    """Diagnostics for /meta/doctor. Set probe=True to compile NPU and run one vector."""
    backend = embed_backend_name()
    ov_dir = _ov_model_dir()
    status: dict[str, object] = {
        "backend": backend,
        "ollama_base": _ollama_base_url(),
        "ollama_model": _ollama_embed_model(),
        "ov_dir": str(ov_dir or ""),
        "ov_device": _ov_device(),
        "ov_xml_present": bool(ov_dir and (ov_dir / "openvino_model.xml").is_file()),
    }
    if backend in ("openvino", "ov", "npu"):
        if not status["ov_xml_present"]:
            status["openvino_ok"] = False
            status["openvino_error"] = "EMBED_OV_NPU_DIR missing openvino_model.xml"
        elif probe:
            try:
                vec = _openvino_embed_one("ping")
                with _LOCK:
                    rt = _OV_RUNTIME or {}
                status["openvino_ok"] = True
                status["openvino_device"] = rt.get("device")
                status["dim"] = len(vec)
            except Exception as e:
                status["openvino_ok"] = False
                status["openvino_error"] = str(e)
        else:
            status["openvino_ok"] = True
            status["openvino_probe"] = "skipped"
    return status
