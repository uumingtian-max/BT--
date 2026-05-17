"""Notebook-style ingest + one-shot synthesis into the knowledge tree."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agent_runtime import get_runtime
from llm_client import chat_complete_async
from memory_store import ingest_notebook_corpus

router = APIRouter()


class IngestBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=400)
    text: str = Field("", max_length=500_000)


@router.post("/ingest")
def notebook_ingest(body: IngestBody):
    return ingest_notebook_corpus(body.title, body.text)


class SynthBody(BaseModel):
    title: str = Field("Synthesis", max_length=400)
    text: str = Field(..., min_length=1, max_length=500_000)


@router.post("/synthesize")
async def notebook_synthesize(body: SynthBody):
    rt = get_runtime()
    messages = [
        {
            "role": "system",
            "content": (
                "你是资料整理助手。把用户给的长材料整理成结构化中文笔记：小标题、要点列表、待核实问题；不要空话套话。"
            ),
        },
        {"role": "user", "content": f"标题偏好：{body.title}\n\n材料：\n{body.text}"},
    ]
    out = await chat_complete_async(messages, rt.default_chat_model, temperature=0.2)
    ing = ingest_notebook_corpus(f"{body.title} · 合成", out)
    return {"synthesis": out, "ingest": ing}
