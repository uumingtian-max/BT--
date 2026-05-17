"""
本地 Agent：FastAPI + SQLite +（可选）HF 文本模型、Stable Diffusion、Whisper、TTS、MoviePy。

- 任务分解：默认 LLM；设 use_llm=false 则按 +/，/换行 纯规则拆分。
- 图像：需环境变量 ENABLE_LOCAL_SD=1，否则 /generate_image 返回说明（避免误加载占满显存）。
- 语音：Whisper 本地；TTS 使用 pyttsx3（Windows 离线，音质一般）。
- 桌面壳：见 local-agent-desktop/（Electron 打开 http://127.0.0.1:8000/app/）。
- LLM：默认 distilgpt2（体积小）；可用环境变量 LOCAL_LLM_ID=gpt2 等覆盖。权重缓存在项目下 .hf_cache/。
  若项目目录与 miniconda3 在同一父目录下，勿用裸 --reload，见 run_dev.ps1（排除 miniconda3）。
"""

from __future__ import annotations

import os
import re
import sqlite3
import tempfile
from pathlib import Path

import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_community.llms import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline as hf_pipeline

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
OUTPUTS_DIR = ROOT / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Local Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── SQLite ───────────────────────────────────────────────────────────────────
def init_db() -> None:
    conn = sqlite3.connect(ROOT / "agent_tasks.db")
    cursor = conn.cursor()
    cursor.execute(
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


def store_task(task_name: str, priority: int) -> None:
    conn = sqlite3.connect(ROOT / "agent_tasks.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (name, priority, status) VALUES (?, ?, ?)",
        (task_name, priority, "待执行"),
    )
    conn.commit()
    conn.close()


# ── LLM（懒加载）──────────────────────────────────────────────────────────────
prompt = PromptTemplate(
    input_variables=["query"],
    template=(
        "你是一个 AI Agent，可以分解任务并调整优先级。\n"
        "用户问：{query}\n"
        "请把任务拆成若干子任务，每行一条，以短横线 - 开头，不要其它前缀。"
    ),
)

_llm: HuggingFacePipeline | None = None


def _hf_pretrained_kwargs() -> dict:
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
    # distilgpt2：更小、不易与本地名为 gpt2 的文件夹冲突；仍可从 Hub 拉取
    return ["distilgpt2", "gpt2", "sshleifer/tiny-gpt2"]


def get_llm() -> HuggingFacePipeline:
    global _llm
    if _llm is not None:
        return _llm

    kw = _hf_pretrained_kwargs()
    last_err: Exception | None = None
    model_id: str | None = None
    tokenizer = None
    model = None
    for mid in _iter_llm_model_ids():
        try:
            tokenizer = AutoTokenizer.from_pretrained(mid, **kw)
            model = AutoModelForCausalLM.from_pretrained(mid, **kw)
            model_id = mid
            break
        except OSError as e:
            last_err = e
            continue
    if tokenizer is None or model is None or model_id is None:
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


class Task:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name


def decompose_tasks(query: str) -> list[Task]:
    chain = prompt | get_llm() | StrOutputParser()
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
    return [Task(name=t) for t in lines[:30]]


def decompose_rules_only(query: str) -> list[Task]:
    chunks = re.split(r"[+＋，,、;；\n]+", query)
    out: list[Task] = []
    for c in chunks:
        s = c.strip()
        if s:
            out.append(Task(s))
    if not out:
        t = query.strip()
        out.append(Task(t if t else "未命名任务"))
    return out[:30]


def priority_for(task_name: str) -> int:
    if "@紧急" in task_name:
        return 1
    if "@重要" in task_name:
        return 2
    return 3


# ── Stable Diffusion（可选，极重）────────────────────────────────────────────
_sd_pipe = None


def _get_sd_pipeline():
    global _sd_pipe
    if os.environ.get("ENABLE_LOCAL_SD", "0") != "1":
        return None
    if _sd_pipe is None:
        from diffusers import StableDiffusionPipeline

        model_id = os.environ.get("SD_MODEL_ID", "runwayml/stable-diffusion-v1-5")
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        dev = "cuda:0" if torch.cuda.is_available() else "cpu"
        _sd_pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype,
        ).to(dev)
    return _sd_pipe


# ── Whisper（懒加载）──────────────────────────────────────────────────────────
_whisper = None


def _get_whisper():
    global _whisper
    if _whisper is None:
        import whisper

        name = os.environ.get("WHISPER_MODEL", "tiny")
        _whisper = whisper.load_model(name)
    return _whisper


# ── Pydantic ─────────────────────────────────────────────────────────────────
class AgentRequest(BaseModel):
    query: str = Field(..., description="用户自然语言任务描述")
    use_llm: bool = Field(True, description="false 时按分隔符纯规则拆分，不加载 GPT2")


class GenImageBody(BaseModel):
    prompt: str
    output_path: str = "outputs/sd_out.png"


class GenVideoBody(BaseModel):
    image_paths: list[str] = Field(..., description="相对项目根或绝对路径的图片列表")
    output_path: str = "outputs/slideshow.mp4"
    fps: float = 1.0


class TTSBody(BaseModel):
    text: str
    output_path: str = "outputs/tts_out.wav"


# ── 路由 ─────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
@app.get("/healthcheck")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agent")
def run_agent(body: AgentRequest) -> dict:
    try:
        tasks = decompose_tasks(body.query) if body.use_llm else decompose_rules_only(body.query)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    for task in tasks:
        store_task(task.name, priority_for(task.name))
    return {"status": "success", "tasks": [t.name for t in tasks]}


@app.post("/generate_image")
def generate_image(body: GenImageBody) -> dict:
    pipe = _get_sd_pipeline()
    if pipe is None:
        return {
            "status": "skipped",
            "hint": "未开启本地 SD。PowerShell 先执行: $env:ENABLE_LOCAL_SD=\"1\" 再启动服务；并 pip install -r requirements-local-agent.txt",
        }
    out = ROOT / body.output_path
    out.parent.mkdir(parents=True, exist_ok=True)
    image = pipe(prompt=body.prompt).images[0]
    image.save(str(out))
    return {"status": "success", "image_path": str(out)}


@app.post("/generate_video")
def generate_video(body: GenVideoBody) -> dict:
    try:
        try:
            from moviepy.editor import ImageSequenceClip
        except ImportError:
            from moviepy import ImageSequenceClip
    except ImportError:
        return {"status": "error", "hint": "请安装 moviepy: pip install moviepy opencv-python-headless"}

    paths = []
    for p in body.image_paths:
        fp = Path(p)
        if not fp.is_absolute():
            fp = ROOT / fp
        if not fp.is_file():
            return {"status": "error", "missing": str(fp)}
        paths.append(str(fp))

    out = ROOT / body.output_path
    out.parent.mkdir(parents=True, exist_ok=True)
    clip = ImageSequenceClip(paths, fps=body.fps)
    write_kw = {"codec": "libx264", "audio": False}
    try:
        clip.write_videofile(str(out), **write_kw, logger=None)
    except TypeError:
        clip.write_videofile(str(out), **write_kw, verbose=False)
    clip.close()
    return {"status": "success", "video_path": str(out)}


@app.post("/speech_to_text")
async def speech_to_text(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    fd, tmp = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        data = await file.read()
        Path(tmp).write_bytes(data)
        model = _get_whisper()
        result = model.transcribe(tmp)
        return {"status": "success", "text": result.get("text", "").strip()}
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


@app.post("/text_to_speech")
def text_to_speech(body: TTSBody) -> dict:
    out = ROOT / body.output_path
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.save_to_file(body.text, str(out))
        engine.runAndWait()
    except Exception as e:
        return {"status": "error", "hint": str(e)}
    return {"status": "success", "audio_path": str(out)}


if STATIC_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(STATIC_DIR), html=True), name="app")


if __name__ == "__main__":
    import uvicorn

    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
