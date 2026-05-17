"""Routes for BKLT local content processing pipeline."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from content_pipeline import process_content

router = APIRouter()


class ContentProcessRequest(BaseModel):
    source: str = Field(..., description="URL, local path, or pasted text")
    source_type: Literal["auto", "url", "path", "text"] = "auto"
    output_type: Literal["report", "slides", "mindmap", "quiz", "podcast_script", "notes"] = "report"
    title: str | None = None
    ingest: bool = False


@router.get("/capabilities")
def content_capabilities():
    return {
        "ok": True,
        "source_types": ["auto", "url", "path", "text"],
        "output_types": ["report", "slides", "mindmap", "quiz", "podcast_script", "notes"],
        "safe_policy": [
            "public URL, user-provided text, or local files only",
            "no login bypass, subscription bypass, or access-control bypass",
            "external NotebookLM upload should be added as a confirm-level tool",
        ],
    }


@router.post("/process")
def content_process(body: ContentProcessRequest):
    try:
        result = process_content(
            source=body.source,
            source_type=body.source_type,
            output_type=body.output_type,
            title=body.title,
            ingest=body.ingest,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
