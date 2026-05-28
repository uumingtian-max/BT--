from __future__ import annotations

import os
import sqlite_wal as sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agent_runtime import get_runtime
from context_pack import compress_for_llm
from llm_client import chat_complete_sync
from observe import record_task_outcome
from workflow_store import build_workflow_context, record_task_review

DB_PATH = os.path.join(os.path.dirname(__file__), "orchestrator.db")
router = APIRouter()


def init_orchestrator_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS task_runs (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            model_name TEXT NOT NULL,
            status TEXT NOT NULL,
            input_text TEXT,
            output_text TEXT,
            error_text TEXT,
            retries INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_runs_parent_id ON task_runs(parent_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_runs_created_at ON task_runs(created_at)")
    conn.commit()
    conn.close()


init_orchestrator_db()


def _now_ts() -> int:
    return int(time.time())


def _save_task(
    task_id: str,
    parent_id: str | None,
    kind: str,
    title: str,
    model_name: str,
    status: str,
    input_text: str,
    output_text: str = "",
    error_text: str = "",
    retries: int = 0,
) -> None:
    ts = _now_ts()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO task_runs (
            id, parent_id, kind, title, model_name, status,
            input_text, output_text, error_text, retries, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            parent_id=excluded.parent_id,
            kind=excluded.kind,
            title=excluded.title,
            model_name=excluded.model_name,
            status=excluded.status,
            input_text=excluded.input_text,
            output_text=excluded.output_text,
            error_text=excluded.error_text,
            retries=excluded.retries,
            updated_at=excluded.updated_at
        """,
        (
            task_id,
            parent_id,
            kind,
            title,
            model_name,
            status,
            input_text,
            output_text,
            error_text,
            retries,
            ts,
            ts,
        ),
    )
    conn.commit()
    conn.close()


def _list_children(parent_id: str) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT id, kind, title, model_name, status, output_text, error_text, retries, updated_at
        FROM task_runs WHERE parent_id = ? ORDER BY created_at ASC
        """,
        (parent_id,),
    ).fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "kind": row[1],
            "title": row[2],
            "model_name": row[3],
            "status": row[4],
            "output_text": row[5],
            "error_text": row[6],
            "retries": row[7],
            "updated_at": row[8],
        }
        for row in rows
    ]


def _call_llm_once(model: str, system_prompt: str, user_prompt: str) -> str:
    rt = get_runtime()
    sp = compress_for_llm(system_prompt, rt.context_block_max_chars, "orch_system")
    up = compress_for_llm(user_prompt, rt.tool_result_max_chars, "orch_user")
    messages = [
        {"role": "system", "content": sp},
        {"role": "user", "content": up},
    ]
    return chat_complete_sync(messages, model, temperature=0.2)


def _call_with_retry(model: str, system_prompt: str, user_prompt: str, retries: int = 1) -> tuple[str, int]:
    last_error = None
    attempt = 0
    while attempt <= retries:
        try:
            return _call_llm_once(model, system_prompt, user_prompt), attempt
        except Exception as exc:
            last_error = exc
            attempt += 1
    raise RuntimeError(str(last_error))


@dataclass
class ModelProfile:
    planner_model: str = ""
    coder_model: str = ""
    reviewer_model: str = ""
    vision_model: str = ""
    speech_model: str = ""


def _base_profile() -> ModelProfile:
    r = get_runtime()
    return ModelProfile(
        planner_model=r.planner_model,
        coder_model=r.coder_model,
        reviewer_model=r.reviewer_model,
        vision_model=r.vision_model,
        speech_model=r.speech_model,
    )


def _profile_from_request(payload: dict[str, Any]) -> ModelProfile:
    base = _base_profile()
    return ModelProfile(
        planner_model=payload.get("planner_model") or base.planner_model,
        coder_model=payload.get("coder_model") or base.coder_model,
        reviewer_model=payload.get("reviewer_model") or base.reviewer_model,
        vision_model=payload.get("vision_model") or base.vision_model,
        speech_model=payload.get("speech_model") or base.speech_model,
    )


def route_model_profile(message: str, base: ModelProfile, evolution_context: str = "") -> ModelProfile:
    text = (message or "").lower()
    evo = (evolution_context or "").lower()
    r = get_runtime()
    profile = ModelProfile(
        planner_model=base.planner_model,
        coder_model=base.coder_model,
        reviewer_model=base.reviewer_model,
        vision_model=base.vision_model,
        speech_model=base.speech_model,
    )

    if any(k in text for k in ["代码", "python", "脚本", "接口", "调试", "测试", "bug"]):
        profile.planner_model = r.coder_model
        profile.coder_model = r.coder_model
        profile.reviewer_model = r.reviewer_model
    elif any(k in text for k in ["部署", "启动", "端口", "api", "后端", "前端", "electron", "uvicorn"]):
        profile.planner_model = r.reviewer_model
        profile.coder_model = r.coder_model
        profile.reviewer_model = r.reviewer_model
    elif any(k in text for k in ["记忆", "总结", "画像", "习惯", "知识库", "长期记忆"]):
        profile.planner_model = r.planner_model
        profile.coder_model = r.planner_model
        profile.reviewer_model = r.reviewer_model
    elif any(k in text for k in ["arxiv", "论文", "文献", "综述", "pubmed", "学术", "引用", "开题"]):
        profile.planner_model = r.planner_model
        profile.coder_model = r.planner_model
        profile.reviewer_model = r.reviewer_model
    elif any(k in text for k in ["模型", "ollama", "gguf", "训练", "量化", "权重", "lora"]):
        profile.planner_model = r.planner_model
        profile.coder_model = r.coder_model
        profile.reviewer_model = r.reviewer_model
    elif any(k in text for k in ["桌面", "文件", "目录", "清单", "整理"]):
        profile.planner_model = r.planner_model
        profile.coder_model = r.planner_model
        profile.reviewer_model = r.reviewer_model
    elif any(
        k in text
        for k in [
            "sre",
            "可用性",
            "线上故障",
            "告警",
            "监控",
            "故障复盘",
            "on-call",
            "sla",
            "slo",
            "可观测",
        ]
    ):
        profile.planner_model = r.planner_model
        profile.coder_model = r.coder_model
        profile.reviewer_model = r.reviewer_model

    if "中文" in evo or "本地优先" in evo:
        if "代码" not in text and "python" not in text:
            profile.planner_model = r.planner_model
    return profile


def _decompose_task(message: str, profile: ModelProfile, evolution_context: str = "") -> list[dict[str, str]]:
    text = message.lower()
    rt = get_runtime()
    workflow_context = compress_for_llm(build_workflow_context(message), rt.context_block_max_chars, "workflow")
    subtasks: list[dict[str, str]] = [
        {
            "kind": "planner",
            "title": "需求拆解与执行计划",
            "model_name": profile.planner_model,
            "prompt": (
                "请把这个任务拆成明确的执行计划，按 1-5 条输出，每条一句话。\n"
                f"{evolution_context}\n\n{workflow_context}\n\n任务：{message}"
            ),
        }
    ]

    if any(k in text for k in ["代码", "python", "脚本", "项目", "接口", "bug", "调试", "测试"]):
        research_tail = ""
        if any(k in text for k in ["arxiv", "论文", "文献", "pubmed", "学术", "综述", "引用", "开题"]):
            research_tail = (
                "\n此外从学术与可溯源角度：核查引用是否可核验（题名/年份/DOI 或稳定链接）；"
                "不要把二手博客当作原始论文结论的唯一依据。"
            )
        subtasks.extend(
            [
                {
                    "kind": "coder",
                    "title": "代码实现方案",
                    "model_name": profile.coder_model,
                    "prompt": (
                        "请基于这个需求给出直接可落地的代码实现方案，尽量本地优先。\n"
                        f"{evolution_context}\n\n{workflow_context}\n\n任务：{message}"
                    ),
                },
                {
                    "kind": "reviewer",
                    "title": "测试与风险检查",
                    "model_name": profile.reviewer_model,
                    "prompt": (
                        "请从测试、错误处理、边界情况角度检查这个任务，并指出最可能踩坑处。\n"
                        f"{evolution_context}\n\n{workflow_context}\n\n任务：{message}" + research_tail
                    ),
                },
            ]
        )

    if any(k in text for k in ["语音", "音频", "说话", "whisper", "tts"]):
        subtasks.append(
            {
                "kind": "speech",
                "title": "语音链路方案",
                "model_name": profile.speech_model,
                "prompt": (
                    "请给出这项任务的本地语音输入/输出接入方案。\n"
                    f"{evolution_context}\n\n{workflow_context}\n\n任务：{message}"
                ),
            }
        )

    if any(k in text for k in ["图像", "图片", "视觉", "识图", "视频"]):
        subtasks.append(
            {
                "kind": "vision",
                "title": "图像/视觉链路方案",
                "model_name": profile.vision_model,
                "prompt": (
                    "请给出这项任务的本地图像/视觉处理方案。\n"
                    f"{evolution_context}\n\n{workflow_context}\n\n任务：{message}"
                ),
            }
        )

    if len(subtasks) == 1:
        exec_prompt = (
            "请给出这项任务下一步最应该执行的动作和落地方式。\n"
            f"{evolution_context}\n\n{workflow_context}\n\n任务：{message}"
        )
        if any(
            k in text
            for k in [
                "sre",
                "可用性",
                "告警",
                "监控",
                "故障",
                "复盘",
                "on-call",
                "sla",
                "slo",
                "可观测",
            ]
        ):
            exec_prompt = (
                "你是本地 SRE/可观测顾问。输出：1) 现象与假设 2) 需要看的指标/日志/追踪 3) 最小验证步骤 "
                "4) 止损/回滚与沟通要点。避免空话。\n"
                f"{evolution_context}\n\n{workflow_context}\n\n任务：{message}"
            )
        subtasks.append(
            {
                "kind": "executor",
                "title": "执行建议",
                "model_name": profile.coder_model,
                "prompt": exec_prompt,
            }
        )

    return subtasks


def run_orchestration(message: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    profile = _profile_from_request(payload)
    parent_id = str(uuid.uuid4())
    _save_task(
        task_id=parent_id,
        parent_id=None,
        kind="root",
        title=message[:80],
        model_name=profile.planner_model,
        status="running",
        input_text=message,
    )

    rt = get_runtime()
    evolution_context = compress_for_llm(
        str(payload.get("evolution_context", "")),
        rt.context_block_max_chars,
        "evolution",
    )
    profile = route_model_profile(message, profile, evolution_context)
    subtasks = _decompose_task(message, profile, evolution_context)
    results: list[dict[str, Any]] = []

    for sub in subtasks:
        task_id = str(uuid.uuid4())
        _save_task(
            task_id=task_id,
            parent_id=parent_id,
            kind=sub["kind"],
            title=sub["title"],
            model_name=sub["model_name"],
            status="running",
            input_text=sub["prompt"],
        )
        try:
            output, retry_count = _call_with_retry(
                sub["model_name"],
                f"你是负责{sub['title']}的本地 Agent 子模型。请直接输出结果。",
                sub["prompt"],
            )
            _save_task(
                task_id=task_id,
                parent_id=parent_id,
                kind=sub["kind"],
                title=sub["title"],
                model_name=sub["model_name"],
                status="completed",
                input_text=sub["prompt"],
                output_text=output,
                retries=retry_count,
            )
            record_task_outcome("orchestrator_subtask", "success", sub["kind"], sub["title"])
            record_task_review(message, "success", sub["kind"], output, sub["title"])
            results.append(
                {
                    "kind": sub["kind"],
                    "title": sub["title"],
                    "model_name": sub["model_name"],
                    "output": output,
                }
            )
        except Exception as exc:
            _save_task(
                task_id=task_id,
                parent_id=parent_id,
                kind=sub["kind"],
                title=sub["title"],
                model_name=sub["model_name"],
                status="failed",
                input_text=sub["prompt"],
                error_text=str(exc),
                retries=1,
            )
            record_task_outcome("orchestrator_subtask", "failed", sub["kind"], str(exc))
            record_task_review(message, "failed", sub["kind"], f"子任务失败：{exc}", sub["title"])
            results.append(
                {
                    "kind": sub["kind"],
                    "title": sub["title"],
                    "model_name": sub["model_name"],
                    "output": f"子任务失败：{exc}",
                }
            )

    synthesis_prompt = (
        f"原始任务：{message}\n\n"
        "下面是多个本地模型子任务的结果，请汇总成中文执行结论。\n"
        "要求：\n"
        "1. 先给 3-6 条核心判断\n"
        "2. 再给一个推荐的下一步\n"
        "3. 不要解释你是怎么调用模型的\n\n"
        + "\n\n".join(
            f"[{item['kind']} | {item['model_name']} | {item['title']}]\n"
            f"{compress_for_llm(str(item.get('output', '')), min(rt.tool_result_max_chars, 12000), item['kind'])}"
            for item in results
        )
    )
    synthesis_prompt = compress_for_llm(synthesis_prompt, rt.tool_result_max_chars * 2, "synthesis")
    final_text, retry_count = _call_with_retry(
        profile.planner_model,
        "你是总控模型，负责整合多个子模型的结果，输出最终结论。",
        synthesis_prompt,
    )
    _save_task(
        task_id=parent_id,
        parent_id=None,
        kind="root",
        title=message[:80],
        model_name=profile.planner_model,
        status="completed",
        input_text=message,
        output_text=final_text,
        retries=retry_count,
    )
    record_task_outcome("orchestrator_root", "success", "run_task_orchestration", message[:200])
    record_task_review(message, "success", "run_task_orchestration", final_text, "多模型协作汇总完成")
    return {
        "task_id": parent_id,
        "message": message,
        "models": profile.__dict__,
        "subtasks": _list_children(parent_id),
        "final_output": final_text,
    }


class OrchestrateRequest(BaseModel):
    message: str = Field(..., description="复杂任务描述")
    planner_model: str = ""
    coder_model: str = ""
    reviewer_model: str = ""
    vision_model: str = ""
    speech_model: str = ""

    def resolved_models(self) -> dict[str, str]:
        base = _base_profile()
        return {
            "planner_model": self.planner_model or base.planner_model,
            "coder_model": self.coder_model or base.coder_model,
            "reviewer_model": self.reviewer_model or base.reviewer_model,
            "vision_model": self.vision_model or base.vision_model,
            "speech_model": self.speech_model or base.speech_model,
        }


@router.post("/orchestrate")
def orchestrate(req: OrchestrateRequest):
    return run_orchestration(req.message, req.resolved_models())


@router.get("/orchestrate/{task_id}")
def get_orchestration(task_id: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        """
        SELECT id, title, model_name, status, input_text, output_text, error_text, retries, created_at, updated_at
        FROM task_runs WHERE id = ?
        """,
        (task_id,),
    ).fetchone()
    conn.close()
    if not row:
        return {"ok": False, "error": "task not found"}
    return {
        "task_id": row[0],
        "title": row[1],
        "model_name": row[2],
        "status": row[3],
        "input_text": row[4],
        "output_text": row[5],
        "error_text": row[6],
        "retries": row[7],
        "created_at": row[8],
        "updated_at": row[9],
        "subtasks": _list_children(task_id),
    }
