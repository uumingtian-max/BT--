"""
与 C:\\Users\\ROG\\main.py「Local Agent API」同一路由能力合并进本后端。
重型依赖（torch / diffusers / whisper / moviepy / pyttsx3）仅在调用对应接口时懒加载。

数据与输出根目录：环境变量 LOCAL_AGENT_ROOT；未设置则为 backend 的上一级（通常为 C:\\Users\\ROG），与旧 main.py 一致。
"""

from __future__ import annotations

import os
import re
import sqlite_wal as sqlite3
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from agent_runtime import get_runtime
from llm_client import chat_complete_sync
from paths import legacy_agent_db_path
from safe_paths import safe_output_path

router = APIRouter(tags=["local-agent"])


def _legacy_root() -> Path:
    env = os.environ.get("LOCAL_AGENT_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


ROOT = _legacy_root()
OUTPUTS_DIR = ROOT / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR = OUTPUTS_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024)))


def init_legacy_db() -> None:
    conn = sqlite3.connect(legacy_agent_db_path())
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            priority INTEGER,
            status TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def _store_task(task_name: str, priority: int) -> None:
    conn = sqlite3.connect(legacy_agent_db_path())
    conn.execute(
        "INSERT INTO tasks (name, priority, status) VALUES (?, ?, ?)",
        (task_name, priority, "待执行"),
    )
    conn.commit()
    conn.close()


def _safe_upload_name(name: str) -> str:
    raw = Path(name or "attachment.bin").name
    stem = Path(raw).stem or "attachment"
    suffix = Path(raw).suffix[:16]
    stem = re.sub(r"[^A-Za-z0-9_.\-\u4e00-\u9fff]+", "_", stem).strip("._") or "attachment"
    return f"{int(time.time() * 1000)}_{stem[:80]}{suffix}"


# ── LLM 懒加载 ──────────────────────────────────────────
prompt_template = (
    "你是一个 AI Agent，可以分解任务并调整优先级。\n"
    "用户问：{query}\n"
    "请把任务拆成若干子任务，每行一条，以短横线 - 开头，不要其它前缀。"
)

_llm = None
_llm_lock = threading.Lock()


def _hf_pretrained_kwargs() -> dict[str, Any]:
    cache = ROOT / ".hf_cache"
    cache.mkdir(parents=True, exist_ok=True)
    return {
        "cache_dir": str(cache),
        "local_files_only": os.environ.get("HF_HUB_OFFLINE", "0") == "1",
    }


def _iter_llm_model_ids() -> list[str]:
    env = os.environ.get("LOCAL_LLM_ID", "").strip()
    if env:
        return [env]
    return ["distilgpt2", "gpt2", "sshleifer/tiny-gpt2"]


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm
    with _llm_lock:
        if _llm is not None:  # double-check after acquiring lock
            return _llm
        import torch
        from langchain_community.llms import HuggingFacePipeline
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            pipeline as hf_pipeline,
        )

        kw = _hf_pretrained_kwargs()
        last_err: Exception | None = None
        tokenizer = None
        model = None
        for mid in _iter_llm_model_ids():
            try:
                tokenizer = AutoTokenizer.from_pretrained(mid, **kw)
                model = AutoModelForCausalLM.from_pretrained(mid, **kw)
                break
            except OSError as e:
                last_err = e
                continue
        if tokenizer is None or model is None:
            hint = (
                "无法从 Hugging Face 加载文本模型。请检查网络/代理；"
                "或设置 HF_HUB_OFFLINE=1 并事先把模型缓存到 .hf_cache；"
                "或设置 LOCAL_LLM_ID=本机已缓存的模型名。"
                "若曾下载中断，可删除目录后重试："
                f"{ROOT / '.hf_cache'}"
            )
            raise RuntimeError(hint) from last_err

        if getattr(tokenizer, "pad_token", None) is None and getattr(tokenizer, "eos_token", None) is not None:
            tokenizer.pad_token = tokenizer.eos_token

        use_cuda = torch.cuda.is_available()
        dtype = torch.float16 if use_cuda else torch.float32
        if use_cuda:
            model = model.to("cuda:0")
        pipe = hf_pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            device=0 if use_cuda else -1,
            torch_dtype=dtype,
        )
        _llm = HuggingFacePipeline(pipeline=pipe)
        return _llm


class _LegacyTask:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name


def _decompose_tasks(query: str) -> list[_LegacyTask]:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import PromptTemplate

    prompt = PromptTemplate(input_variables=["query"], template=prompt_template)
    chain = prompt | _get_llm() | StrOutputParser()
    raw = chain.invoke({"query": query})
    lines: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        s = s.lstrip("-").strip()
        if s:
            lines.append(s)
    if not lines:
        lines = [raw.strip()[:500]]
    return [_LegacyTask(name=t) for t in lines[:30]]


def _decompose_tasks_llm(query: str) -> list[_LegacyTask]:
    rt = get_runtime()
    model = os.environ.get("OLLAMA_TASK_MODEL", "").strip() or getattr(rt, "task_model", rt.default_chat_model)
    system = (
        "你是任务分解助手。把用户描述拆成可执行的子任务。每行一条，以短横线 - 开头；不要编号；不要其它前缀；不要解释。"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    raw = chat_complete_sync(messages, model, temperature=0.25) or ""
    lines: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        s = s.lstrip("-").strip()
        if s:
            lines.append(s)
    if not lines:
        lines = [raw.strip()[:500] if raw.strip() else "未命名任务"]
    return [_LegacyTask(name=t) for t in lines[:30]]


def _decompose_rules_only(query: str) -> list[_LegacyTask]:
    chunks = re.split(r"[+＋，,、;；\n]+", query)
    out: list[_LegacyTask] = []
    for c in chunks:
        s = c.strip()
        if s:
            out.append(_LegacyTask(s))
    if not out:
        t = query.strip()
        out.append(_LegacyTask(t if t else "未命名任务"))
    return out[:30]


def _priority_for(task_name: str) -> int:
    if "@紧急" in task_name:
        return 1
    if "@重要" in task_name:
        return 2
    return 3


# ── SD / Whisper 懒加载 ─────────────────────────────────
_sd_pipe = None
_sd_pipe_lock = threading.Lock()


def _get_sd_pipeline():
    global _sd_pipe
    if os.environ.get("ENABLE_LOCAL_SD", "0") != "1":
        return None
    if _sd_pipe is not None:
        return _sd_pipe
    with _sd_pipe_lock:
        if _sd_pipe is not None:
            return _sd_pipe
        import torch
        from diffusers import StableDiffusionPipeline

        model_id = os.environ.get("SD_MODEL_ID", "runwayml/stable-diffusion-v1-5")
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        dev = "cuda:0" if torch.cuda.is_available() else "cpu"
        _sd_pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype).to(dev)
    return _sd_pipe


_whisper = None
_whisper_lock = threading.Lock()


def _get_whisper():
    global _whisper
    if _whisper is not None:
        return _whisper
    with _whisper_lock:
        if _whisper is not None:
            return _whisper
        import whisper

        name = os.environ.get("WHISPER_MODEL", "tiny")
        _whisper = whisper.load_model(name)
    return _whisper


# ── Pydantic（与 Swagger 中名称对齐，避免与 agent 模块冲突）──
class TaskDecomposeBody(BaseModel):
    """与原 Swagger「AgentRequest」同字段；类名避免与 agent.py 中模型冲突。"""

    model_config = ConfigDict(title="AgentRequest")

    query: str = Field(..., description="用户自然语言任务描述")
    use_llm: bool = Field(
        True,
        description="false=按分隔符规则拆分。true 时由 TASK_DECOMPOSE_BACKEND 选择：ollama/local/openhuman（走 chat_complete_sync，与 LLM_BACKEND 一致）或 hf（本机 Transformers）",
    )


class GenImageBody(BaseModel):
    model_config = ConfigDict(title="GenImageBody")

    prompt: str
    output_path: str = "outputs/sd_out.png"


class GenVideoBody(BaseModel):
    model_config = ConfigDict(title="GenVideoBody")

    prompt: str = Field("", description="文生视频提示词（需 VIDEO_GEN_BACKEND=wan|cogvideox|auto）")
    image_paths: list[str] = Field(
        default_factory=list,
        description="图片列表合成幻灯片；与 prompt 二选一或优先图片",
    )
    output_path: str = "outputs/agent_video.mp4"
    fps: float = 1.0


class TTSBody(BaseModel):
    model_config = ConfigDict(title="TTSBody")

    text: str
    output_path: str = "outputs/tts_out.wav"


@router.get("/healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/agent")
def run_legacy_task_agent(body: TaskDecomposeBody) -> dict[str, Any]:
    """原 Local Agent：任务分解 + 写入 SQLite（与 Ollama /agent/run 不同）。"""
    if not body.use_llm:
        tasks = _decompose_rules_only(body.query)
    else:
        backend = os.environ.get("TASK_DECOMPOSE_BACKEND", "ollama").strip().lower()
        if backend in (
            "ollama",
            "local",
            "openhuman",
            "openai",
            "openai_compatible",
            "vllm",
            "litellm",
            "localai",
        ):
            try:
                tasks = _decompose_tasks_llm(body.query)
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"LLM 任务分解失败: {e}") from e
        else:
            try:
                tasks = _decompose_tasks(body.query)
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e)) from e
    for task in tasks:
        _store_task(task.name, _priority_for(task.name))
    return {"status": "success", "tasks": [t.name for t in tasks]}


@router.post("/generate_image")
def generate_image(body: GenImageBody) -> dict[str, Any]:
    from media_fallback import (
        generate_placeholder_image,
        local_sd_enabled,
        placeholder_enabled,
    )

    pipe = _get_sd_pipeline()
    if pipe is None:
        if placeholder_enabled() and not local_sd_enabled():
            return generate_placeholder_image(body.prompt, body.output_path)
        return {
            "status": "skipped",
            "hint": "未开启本地 SD。设置 ENABLE_LOCAL_SD=1 并 pip install -r requirements-media.txt；或保持 ENABLE_IMAGE_PLACEHOLDER=1 使用占位图",
        }
    try:
        out = safe_output_path(body.output_path, default_name="sd_out.png")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    image = pipe(prompt=body.prompt).images[0]
    image.save(str(out))
    return {"status": "success", "image_path": str(out)}


@router.post("/upload_file")
async def upload_file(file: UploadFile = File(...)) -> dict[str, Any]:
    safe_name = _safe_upload_name(file.filename or "attachment.bin")
    out = UPLOADS_DIR / safe_name
    size = 0
    with out.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                try:
                    out.unlink(missing_ok=True)
                except OSError:
                    pass
                raise HTTPException(status_code=413, detail=f"文件超过上限 {MAX_UPLOAD_BYTES} bytes")
            f.write(chunk)
    return {
        "status": "success",
        "filename": file.filename or safe_name,
        "content_type": file.content_type or "application/octet-stream",
        "size": size,
        "path": str(out),
        "url": f"/outputs/uploads/{safe_name}",
    }


@router.post("/generate_video")
def generate_video(body: GenVideoBody) -> dict[str, Any]:
    from video_gen import generate_video_unified

    return generate_video_unified(
        ROOT,
        OUTPUTS_DIR,
        prompt=body.prompt,
        image_paths=body.image_paths,
        output_path=body.output_path,
        fps=body.fps,
    )


@router.post("/speech_to_text")
async def speech_to_text(file: UploadFile = File(...)) -> dict[str, Any]:
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    fd, tmp = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        size = 0
        with Path(tmp).open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"音频超过上限 {MAX_UPLOAD_BYTES} bytes")
                f.write(chunk)
        model = _get_whisper()
        result = model.transcribe(tmp)
        return {"status": "success", "text": result.get("text", "").strip()}
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


@router.post("/text_to_speech")
def text_to_speech(body: TTSBody) -> dict[str, Any]:
    try:
        out = safe_output_path(body.output_path, default_name="tts_out.wav")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.save_to_file(body.text, str(out))
        engine.runAndWait()
    except Exception as e:
        return {"status": "error", "hint": str(e)}
    return {"status": "success", "audio_path": str(out)}
