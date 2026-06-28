from __future__ import annotations

import json
import os
import sqlite_wal as sqlite3
import time
from collections import Counter
from typing import Any

from fastapi import APIRouter

DB_PATH = os.path.join(os.path.dirname(__file__), "workflow.db")
router = APIRouter()

_schema_initialized = False


def _ensure_schema() -> None:
    global _schema_initialized
    if not _schema_initialized:
        init_workflow_store()
        _schema_initialized = True


def _now_ts() -> int:
    return int(time.time())


def init_workflow_store() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS task_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at INTEGER NOT NULL,
            task_text TEXT NOT NULL,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL,
            tool_name TEXT,
            final_answer TEXT,
            detail_text TEXT,
            lessons TEXT,
            template_name TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            trigger_keywords_json TEXT NOT NULL,
            system_hint TEXT NOT NULL,
            steps_json TEXT NOT NULL,
            updated_at INTEGER NOT NULL,
            usage_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_reviews_created_at ON task_reviews(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_reviews_task_type ON task_reviews(task_type)")
    conn.commit()
    conn.close()
    seed_default_templates()


DEFAULT_TEMPLATES = [
    {
        "name": "deployment_troubleshooting",
        "trigger_keywords": [
            "部署",
            "启动",
            "端口",
            "uvicorn",
            "electron",
            "api",
            "后端",
            "前端",
        ],
        "system_hint": "这是部署/启动排障任务。先确认真实状态，再给最短排查链路，不要泛讲。",
        "steps": [
            "确认当前报错",
            "确认进程/端口",
            "确认配置文件",
            "给最短修复路径",
            "说明如何复测",
        ],
    },
    {
        "name": "desktop_file_organization",
        "trigger_keywords": ["桌面", "文件", "整理", "目录", "清单", "读取文件"],
        "system_hint": "这是桌面文件任务。优先用本地文件工具，直接给结果，不要教用户手动点。",
        "steps": ["先列目录", "再读关键文件", "最后做归类或总结"],
    },
    {
        "name": "agent_upgrade",
        "trigger_keywords": ["agent", "升级", "记忆", "自进化", "工具", "electron"],
        "system_hint": "这是本地 Agent 升级任务。优先保留现有结构，小步修改，修一条测一条。",
        "steps": ["确认当前版本", "定位问题文件", "只改必要模块", "给复测方法"],
    },
    {
        "name": "coding_agent_skills",
        "trigger_keywords": [
            "技能",
            "插件",
            "claude",
            "codex",
            "cursor",
            "最佳实践",
            "脚手架",
        ],
        "system_hint": "这是编码助手/技能包类问题：先对齐目标与约束，再给可复制的命令或最小代码块。",
        "steps": [
            "确认语言与运行环境",
            "给出最小可运行示例",
            "说明如何验证",
            "列出常见坑",
        ],
    },
    {
        "name": "research_and_stack_scan",
        "trigger_keywords": ["趋势", "github", "开源", "对比", "选型", "benchmark"],
        "system_hint": "这是调研/选型任务：先定义评价维度，再给对比表式结论与参考链接占位（由搜索工具补齐）。",
        "steps": [
            "列出必须对比的维度",
            "用搜索抓最新信息",
            "汇总表格",
            "给出推荐与取舍理由",
        ],
    },
    {
        "name": "model_asset_management",
        "trigger_keywords": ["模型", "ollama", "gguf", "训练", "lora", "量化", "权重"],
        "system_hint": "这是模型/训练资产任务。优先本地现状盘点，再给保留/清理/升级建议。",
        "steps": ["盘点现有模型", "识别重复与缺失", "给主保留集", "给下一步动作"],
    },
]


def seed_default_templates() -> None:
    conn = sqlite3.connect(DB_PATH)
    for item in DEFAULT_TEMPLATES:
        conn.execute(
            """
            INSERT INTO workflow_templates (name, trigger_keywords_json, system_hint, steps_json, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                trigger_keywords_json = excluded.trigger_keywords_json,
                system_hint = excluded.system_hint,
                steps_json = excluded.steps_json,
                updated_at = excluded.updated_at
            """,
            (
                item["name"],
                json.dumps(item["trigger_keywords"], ensure_ascii=False),
                item["system_hint"],
                json.dumps(item["steps"], ensure_ascii=False),
                _now_ts(),
            ),
        )
    conn.commit()
    conn.close()


def _classify_task_type(text: str) -> str:
    lower = (text or "").lower()
    mapping = {
        "deployment": [
            "部署",
            "启动",
            "端口",
            "uvicorn",
            "electron",
            "api",
            "后端",
            "前端",
        ],
        "files": ["桌面", "文件", "目录", "读取", "整理", "清单"],
        "agent_upgrade": ["agent", "升级", "记忆", "自进化", "工具", "electron"],
        "models": ["模型", "ollama", "gguf", "训练", "lora", "量化", "权重"],
        "coding": ["代码", "python", "脚本", "调试", "接口", "测试"],
    }
    for task_type, keywords in mapping.items():
        if any(k in lower for k in keywords):
            return task_type
    return "general"


def _derive_lessons(task_text: str, status: str, tool_name: str, final_answer: str, detail_text: str) -> str:
    if status == "failed":
        if "Not found:" in detail_text:
            return "遇到文件路径问题时，先做本地路径解析，再继续读写。"
        if "Tool error:" in detail_text or "error:" in detail_text.lower():
            return "工具执行失败时不要继续硬答，先明确失败点再重试。"
        if "没有真正把任务做完" in final_answer:
            return "这类任务缺真实结果时，应该先补执行，再给结论。"
        return "这次任务失败，下一次要先缩小目标并核对真实执行结果。"
    if tool_name in {"list_files", "read_file"}:
        return "文件类任务优先走本地文件工具，拿到真实内容后再总结。"
    if tool_name == "run_task_orchestration":
        return "复杂任务先拆解再汇总，效果比单轮直接回答更稳定。"
    if tool_name == "get_evolution_profile":
        return "涉及习惯和风格的问题，应先利用自进化画像再回答。"
    return "这类任务可以复用当前处理方式，但仍要优先基于真实结果回答。"


def _match_template(task_text: str) -> dict[str, Any] | None:
    _ensure_schema()
    lower = (task_text or "").lower()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT name, trigger_keywords_json, system_hint, steps_json, usage_count FROM workflow_templates"
    ).fetchall()
    conn.close()
    best: tuple[int, dict[str, Any]] | None = None
    for row in rows:
        keywords = json.loads(row[1] or "[]")
        score = sum(1 for kw in keywords if kw.lower() in lower)
        if score <= 0:
            continue
        item = {
            "name": row[0],
            "trigger_keywords": keywords,
            "system_hint": row[2],
            "steps": json.loads(row[3] or "[]"),
            "usage_count": row[4],
        }
        if best is None or score > best[0]:
            best = (score, item)
    return best[1] if best else None


def touch_template_usage(name: str) -> None:
    _ensure_schema()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE workflow_templates SET usage_count = usage_count + 1, updated_at = ? WHERE name = ?",
        (_now_ts(), name),
    )
    conn.commit()
    conn.close()


_TASK_REVIEWS_TTL_DAYS = 30


def record_task_review(
    task_text: str,
    status: str,
    tool_name: str = "",
    final_answer: str = "",
    detail_text: str = "",
) -> dict[str, Any]:
    task_type = _classify_task_type(task_text)
    template = _match_template(task_text)
    template_name = template["name"] if template else ""
    lessons = _derive_lessons(task_text, status, tool_name, final_answer, detail_text)
    ts = _now_ts()
    cutoff = ts - _TASK_REVIEWS_TTL_DAYS * 86400
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO task_reviews (
            created_at, task_text, task_type, status, tool_name, final_answer, detail_text, lessons, template_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ts,
            task_text,
            task_type,
            status,
            tool_name,
            final_answer[:1000],
            detail_text[:1000],
            lessons,
            template_name,
        ),
    )
    # 清理超过 30 天的旧复盘，防止 workflow.db 无限增长
    conn.execute("DELETE FROM task_reviews WHERE created_at < ?", (cutoff,))
    conn.commit()
    conn.close()
    if template_name:
        touch_template_usage(template_name)
    return {"task_type": task_type, "template_name": template_name, "lessons": lessons}


def list_task_reviews(limit: int = 50) -> list[dict[str, Any]]:
    _ensure_schema()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT created_at, task_text, task_type, status, tool_name, lessons, template_name
        FROM task_reviews
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {
            "created_at": row[0],
            "task_text": row[1],
            "task_type": row[2],
            "status": row[3],
            "tool_name": row[4],
            "lessons": row[5],
            "template_name": row[6],
        }
        for row in rows
    ]


def list_templates() -> list[dict[str, Any]]:
    _ensure_schema()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT name, trigger_keywords_json, system_hint, steps_json, usage_count, updated_at
        FROM workflow_templates
        ORDER BY usage_count DESC, name ASC
        """
    ).fetchall()
    conn.close()
    return [
        {
            "name": row[0],
            "trigger_keywords": json.loads(row[1] or "[]"),
            "system_hint": row[2],
            "steps": json.loads(row[3] or "[]"),
            "usage_count": row[4],
            "updated_at": row[5],
        }
        for row in rows
    ]


def build_workflow_context(task_text: str) -> str:
    task_type = _classify_task_type(task_text)
    template = _match_template(task_text)
    reviews = [item for item in list_task_reviews(20) if item["task_type"] == task_type][:5]
    lines = ["## 任务复盘与模板上下文"]
    lines.append(f"- 当前任务类型：{task_type}")
    if template:
        lines.append(f"- 匹配模板：{template['name']}")
        lines.append(f"- 模板提示：{template['system_hint']}")
        if template.get("steps"):
            lines.append("- 建议执行顺序：")
            for step in template["steps"]:
                lines.append(f"  - {step}")
    if reviews:
        lines.append("- 同类任务近期经验：")
        for item in reviews:
            lines.append(f"  - [{item['status']}] {item['lessons']}")
    return "\n".join(lines)


def get_workflow_dashboard() -> dict[str, Any]:
    reviews = list_task_reviews(200)
    templates = list_templates()
    type_counts = Counter(item["task_type"] for item in reviews)
    status_counts = Counter(item["status"] for item in reviews)
    return {
        "review_count": len(reviews),
        "type_counts": dict(type_counts),
        "status_counts": dict(status_counts),
        "recent_reviews": reviews[:20],
        "templates": templates,
    }


@router.get("/workflow/reviews")
def workflow_reviews():
    return list_task_reviews()


@router.get("/workflow/templates")
def workflow_templates():
    return list_templates()


@router.get("/workflow/dashboard")
def workflow_dashboard():
    return get_workflow_dashboard()
