from __future__ import annotations

"""
本地行为观察与设备画像（对齐《总方案》第2–3阶段：会看 + 轻量会学）
仅 Windows 下读取前台窗口标题；全平台可做进程快照（psutil）。
"""
import logging

_logger = logging.getLogger(__name__)

import asyncio
import json
import os
import sqlite_wal as sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

BEHAVIOR_DB = os.path.join(os.path.dirname(__file__), "behavior.db")

# 可通过环境变量关闭后台采集：DISABLE_BACKGROUND_OBSERVE=1
# 采集间隔（秒）：OBSERVE_INTERVAL_SEC，默认 50


def init_observe_db() -> None:
    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            foreground_title TEXT,
            process_json TEXT NOT NULL,
            system_mem_percent REAL,
            cpu_percent REAL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_samples_ts ON activity_samples(ts)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL UNIQUE,
            summary TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inferred_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL UNIQUE,
            summary TEXT NOT NULL,
            adjustments_json TEXT NOT NULL DEFAULT '[]',
            signals_json TEXT NOT NULL DEFAULT '[]',
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS task_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL,
            tool_name TEXT,
            detail TEXT,
            latency_ms REAL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_outcomes_ts ON task_outcomes(ts)")
    conn.commit()
    conn.close()


init_observe_db()


def get_foreground_window_title() -> str:
    if sys.platform != "win32":
        return ""
    try:
        import ctypes
        from ctypes import wintypes  # noqa: F401

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buf, length)
        return (buf.value or "").strip()
    except Exception:
        return ""


def snapshot_processes(limit: int = 22) -> list[dict[str, Any]]:
    import psutil

    rows: list[tuple[str, int]] = []
    for proc in psutil.process_iter(["name", "memory_info"]):
        try:
            mi = proc.info.get("memory_info")
            if mi is None:
                continue
            name = proc.info.get("name") or "?"
            rows.append((name, int(mi.rss)))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    rows.sort(key=lambda x: -x[1])
    out: list[dict[str, Any]] = []
    for name, rss in rows[:limit]:
        out.append({"name": name, "mb": round(rss / (1024 * 1024), 1)})
    return out


def record_sample() -> dict[str, Any]:
    import psutil

    init_observe_db()
    ts = int(time.time())
    title = get_foreground_window_title()
    procs = snapshot_processes(22)
    try:
        vm = psutil.virtual_memory()
        sys_mem_p = float(vm.percent)
        cpu_p = float(psutil.cpu_percent(interval=0.12))
    except Exception:
        sys_mem_p, cpu_p = 0.0, 0.0

    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute(
        "DELETE FROM activity_samples WHERE ts < ?",
        (ts - 30 * 86400,),
    )
    conn.execute(
        """
        INSERT INTO activity_samples (ts, foreground_title, process_json, system_mem_percent, cpu_percent)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ts, title, json.dumps(procs, ensure_ascii=False), sys_mem_p, cpu_p),
    )
    conn.commit()
    conn.close()
    return {"ts": ts, "foreground_title": title, "processes": len(procs)}


def _since_ts(hours: int) -> int:
    return int(time.time()) - hours * 3600


def _query_samples(since_ts: int) -> list[tuple[int, str | None, str, float, float]]:
    conn = sqlite3.connect(BEHAVIOR_DB)
    rows = conn.execute(
        """
        SELECT ts, foreground_title, process_json, system_mem_percent, cpu_percent
        FROM activity_samples WHERE ts >= ? ORDER BY ts DESC
        """,
        (since_ts,),
    ).fetchall()
    conn.close()
    return rows


def aggregate_profile(hours: int = 24 * 7) -> dict[str, Any]:
    since = _since_ts(hours)
    rows = _query_samples(since)
    title_ctr: Counter[str] = Counter()
    proc_ctr: Counter[str] = Counter()
    hour_ctr: Counter[int] = Counter()
    mem_samples: list[float] = []
    cpu_samples: list[float] = []

    for ts, fgt, pjson, memp, cpup in rows:
        mem_samples.append(memp)
        cpu_samples.append(cpup)
        if fgt:
            norm = fgt.strip()
            if len(norm) > 200:
                norm = norm[:200] + "…"
            title_ctr[norm] += 1
        try:
            plist = json.loads(pjson)
            for p in plist:
                n = p.get("name") or "?"
                proc_ctr[n] += 1
        except json.JSONDecodeError:
            pass
        h = time.localtime(ts).tm_hour
        hour_ctr[h] += 1

    top_titles = [{"title": t, "count": c} for t, c in title_ctr.most_common(18)]
    top_processes = [{"name": n, "count": c} for n, c in proc_ctr.most_common(18)]
    hour_histogram = [{"hour": h, "count": c} for h, c in sorted(hour_ctr.items())]

    def avg(xs: list[float]) -> float | None:
        return round(sum(xs) / len(xs), 1) if xs else None

    return {
        "window_hours": hours,
        "sample_count": len(rows),
        "top_titles": top_titles,
        "top_processes": top_processes,
        "hour_histogram": hour_histogram,
        "avg_system_mem_percent": avg(mem_samples),
        "avg_cpu_percent": avg(cpu_samples),
    }


def build_insights(profile: dict[str, Any]) -> list[str]:
    out: list[str] = []
    n = profile.get("sample_count") or 0
    if n < 5:
        out.append("画像样本较少：保持后端运行一段时间，或多次点击「立即采集」后再看。")
    titles = profile.get("top_titles") or []
    if titles and titles[0].get("title"):
        t0 = titles[0]
        out.append(f"最常被采到的前台窗口：「{t0['title'][:80]}」({t0['count']} 次)。")
    procs = profile.get("top_processes") or []
    if procs:
        names = "、".join(p["name"] for p in procs[:6])
        out.append(f"内存快照里高频进程：{names}。")
    hist = profile.get("hour_histogram") or []
    if hist:
        peak = max(hist, key=lambda x: x.get("count", 0))
        out.append(f"采样相对密集的本地小时：约 {peak.get('hour', '?')} 点 — 基于本机系统时区。")
    am = profile.get("avg_system_mem_percent")
    ac = profile.get("avg_cpu_percent")
    if am is not None:
        out.append(f"采样期内系统内存占用均值约 {am}%。")
    if ac is not None:
        out.append(f"采样期内 CPU 占用均值约 {ac}%。")
    return out


def desktop_recent_files(limit: int = 28) -> list[dict[str, Any]]:
    """仅浅层扫描桌面，避免全盘递归拖慢机器。过滤快捷方式、临时与系统噪声文件。"""
    root = Path.home() / "Desktop"
    if not root.exists():
        return []
    now = time.time()
    # 黑名单：快捷方式、下载残留、Office/编辑器临时、本地 DB、字节码、系统元数据等
    _SKIP_EXTS = {
        ".lnk",
        ".tmp",
        ".temp",
        ".bak",
        ".old",
        ".db",
        ".db-shm",
        ".db-wal",
        ".pyc",
        ".pyo",
        ".crdownload",
        ".part",
        ".download",
        ".partial",
        ".autosave",
        ".swp",
        ".swo",
        ".ds_store",
        ".localized",
    }
    _SKIP_PREFIXES = ("~$", "._", "thumbs", "desktop.ini")
    _SKIP_NAMES = {"desktop.ini", "thumbs.db", ".ds_store"}
    # 桌面可能出现的「有意义」点文件，其余隐藏文件多属工具元数据
    _ALLOW_DOTFILES = {".env", ".env.local", ".gitignore"}

    def _is_junk(p: Path) -> bool:
        name = p.name
        name_lower = name.lower()
        if name_lower in _SKIP_NAMES:
            return True
        if any(name_lower.startswith(pfx) for pfx in _SKIP_PREFIXES):
            return True
        # macOS / 部分工具在桌面放的隐藏元数据
        if name.startswith(".") and name_lower not in _ALLOW_DOTFILES:
            return True
        # Emacs / 类 Unix 备份
        if name.endswith("~") or name.startswith("#") and name.endswith("#"):
            return True
        suf = p.suffix.lower()
        if suf in _SKIP_EXTS:
            return True
        # 无扩展名且极短文件名多为占位或噪声
        if not suf and len(name) <= 2:
            return True
        return False

    found: list[tuple[float, str]] = []
    try:
        for p in root.iterdir():
            try:
                if p.is_file() and not _is_junk(p):
                    st = p.stat()
                    if now - st.st_mtime < 86400 * 3:
                        found.append((st.st_mtime, str(p)))
                elif p.is_dir():
                    for sub in p.iterdir():
                        if sub.is_file() and not _is_junk(sub):
                            try:
                                st = sub.stat()
                                if now - st.st_mtime < 86400 * 3:
                                    found.append((st.st_mtime, str(sub)))
                            except OSError:
                                continue
            except OSError:
                continue
    except Exception:
        return []
    found.sort(reverse=True)
    return [{"path": path, "name": Path(path).name} for mtime, path in found[:limit]]


_TASK_OUTCOMES_TTL_DAYS = 30


def record_task_outcome(task_type: str, status: str, tool_name: str = "", detail: str = "", latency_ms: float | None = None) -> None:
    ts = int(time.time())
    cutoff = ts - _TASK_OUTCOMES_TTL_DAYS * 86400
    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute(
        """
        INSERT INTO task_outcomes (ts, task_type, status, tool_name, detail, latency_ms)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ts, task_type, status, tool_name, (detail or "")[:500], latency_ms),
    )
    # 顺手清理超过 30 天的旧记录，防止 behavior.db 无限增长
    conn.execute("DELETE FROM task_outcomes WHERE ts < ?", (cutoff,))
    conn.commit()
    conn.close()


def aggregate_task_outcomes(hours: int = 24 * 7) -> dict[str, Any]:
    since = _since_ts(hours)
    conn = sqlite3.connect(BEHAVIOR_DB)
    rows = conn.execute(
        """
        SELECT task_type, status, COALESCE(tool_name, ''), COUNT(*)
        FROM task_outcomes
        WHERE ts >= ?
        GROUP BY task_type, status, COALESCE(tool_name, '')
        """,
        (since,),
    ).fetchall()
    conn.close()

    by_tool: dict[str, dict[str, int]] = {}
    by_type: dict[str, dict[str, int]] = {}
    total_success = 0
    total_fail = 0
    for task_type, status, tool_name, count in rows:
        bucket = by_type.setdefault(task_type, {"success": 0, "failed": 0})
        bucket[status] = bucket.get(status, 0) + count
        if tool_name:
            tb = by_tool.setdefault(tool_name, {"success": 0, "failed": 0})
            tb[status] = tb.get(status, 0) + count
        if status == "success":
            total_success += count
        elif status == "failed":
            total_fail += count

    def _rate(item: dict[str, int]) -> float:
        total = item.get("success", 0) + item.get("failed", 0)
        return round((item.get("success", 0) / total) * 100, 1) if total else 0.0

    return {
        "hours": hours,
        "total_success": total_success,
        "total_fail": total_fail,
        "overall_success_rate": _rate({"success": total_success, "failed": total_fail}),
        "by_type": {k: {**v, "success_rate": _rate(v)} for k, v in by_type.items()},
        "by_tool": {k: {**v, "success_rate": _rate(v)} for k, v in by_tool.items()},
    }


def telemetry_export_snapshot() -> dict[str, Any]:
    """Compact stats for Telegraf/Prometheus scrape (24h outcomes + 1h row rates)."""
    out24 = aggregate_task_outcomes(24)
    since1h = _since_ts(1)
    conn = sqlite3.connect(BEHAVIOR_DB)
    row = conn.execute(
        "SELECT COUNT(*) FROM activity_samples WHERE ts >= ?",
        (since1h,),
    ).fetchone()
    samples_1h = int(row[0] or 0)
    row2 = conn.execute(
        "SELECT COUNT(*) FROM task_outcomes WHERE ts >= ?",
        (since1h,),
    ).fetchone()
    outcomes_1h = int(row2[0] or 0)
    conn.close()
    return {
        "window_24h": out24,
        "activity_samples_1h": samples_1h,
        "task_outcome_events_1h": outcomes_1h,
    }


def get_runtime_adjustments() -> dict[str, Any]:
    data = infer_behavior_patterns()
    outcome = aggregate_task_outcomes()
    signals = set(data.get("signals", []))
    preferred_tools: list[str] = []

    if "organize" in signals:
        preferred_tools += ["list_files", "read_file", "get_recent_desktop_files"]
    if "deployment" in signals:
        preferred_tools += ["get_device_profile", "run_task_orchestration", "execute_python"]
    if "models" in signals:
        preferred_tools += ["get_device_profile", "get_recent_work_summary", "run_task_orchestration"]
    if "agent" in signals:
        preferred_tools += ["get_evolution_profile", "run_task_orchestration", "read_file"]

    preferred_tools += ["list_files", "read_file", "get_recent_work_summary", "get_device_profile", "run_task_orchestration", "web_search", "execute_python", "write_file"]

    deduped: list[str] = []
    for tool in preferred_tools:
        if tool not in deduped:
            deduped.append(tool)

    prompt_hints = [
        "优先使用工具拿到可核验结果，再组织语言回答。",
        "涉及路径与文件时，先解析再读写，避免凭空猜测。",
        "回答保持中文、先结论后细节，避免复述用户原话。",
        "不确定时明确说缺什么信息或哪一步未执行，不要装作已完成。",
    ]

    tool_stats = outcome.get("by_tool", {})
    if tool_stats.get("web_search", {}).get("success_rate", 100) < 50:
        prompt_hints.append("联网搜索成功率偏低：结论需标注不确定性并尽量交叉验证。")
    if tool_stats.get("execute_python", {}).get("success_rate", 100) < 60:
        prompt_hints.append("代码执行失败偏多：缩小脚本范围、先打印中间结果再扩展。")
    if tool_stats.get("run_task_orchestration", {}).get("success_rate", 0) >= 60:
        prompt_hints.append("多模型编排效果稳定：复杂任务可优先走编排再汇总。")
    if tool_stats.get("list_files", {}).get("success_rate", 0) >= 60 or tool_stats.get("read_file", {}).get("success_rate", 0) >= 60:
        prompt_hints.append("文件类工具命中率高：桌面/文档类任务优先列目录再读文件。")

    return {
        "signals": list(signals),
        "preferred_tools": deduped,
        "prompt_hints": prompt_hints,
        "task_outcomes": outcome,
    }


def _upsert_pattern(scope: str, summary: str, adjustments: list[str], signals: list[str]) -> None:
    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute(
        """
        INSERT INTO inferred_patterns (scope, summary, adjustments_json, signals_json, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(scope) DO UPDATE SET
            summary = excluded.summary,
            adjustments_json = excluded.adjustments_json,
            signals_json = excluded.signals_json,
            updated_at = excluded.updated_at
        """,
        (scope, summary, json.dumps(adjustments, ensure_ascii=False), json.dumps(signals, ensure_ascii=False), int(time.time())),
    )
    conn.commit()
    conn.close()


def infer_behavior_patterns() -> dict[str, Any]:
    profile = aggregate_profile(24 * 7)
    recent_files = desktop_recent_files(28)
    title_text = "\n".join((item.get("title") or "") for item in profile.get("top_titles", []))
    proc_names = [item.get("name", "") for item in profile.get("top_processes", [])]
    file_names = [item.get("name", "") for item in recent_files]

    patterns: list[str] = []
    adjustments: list[str] = []
    signals: list[str] = []

    model_tokens = ("ollama", "model", "gguf", "safetensors", "comfy", "whisper", "train", "lora", "qwen")
    deploy_tokens = ("docker", "uvicorn", "electron", "frontend", "backend", "deploy", "端口", "启动", "api")
    agent_tokens = ("agent", "codex", "cline", "continue", "cursor")
    organize_tokens = ("desktop", "桌面", "assets", "文档", "memory", "report", "workspace")

    blob = (title_text + "\n" + "\n".join(proc_names) + "\n" + "\n".join(file_names)).lower()

    if any(tok in blob for tok in model_tokens):
        patterns.append("近期窗口与进程显示你在处理模型、训练或推理相关资产。")
        adjustments.append("涉及模型与权重时，先盘点本地目录与显存占用，再给出可执行整理方案。")
        signals.append("models")

    if any(tok in blob for tok in deploy_tokens):
        patterns.append("近期活动显示你在反复调试部署、服务启动或前后端联调。")
        adjustments.append("部署类问题优先查端口、日志与依赖版本，再给最小变更修复路径。")
        signals.append("deployment")

    if any(tok in blob for tok in agent_tokens):
        patterns.append("你在多种编程 Agent / IDE 助手之间切换，属于高密度开发节奏。")
        adjustments.append("本地 Agent 任务优先走工具链拿证据，避免与 IDE 内助手重复空转。")
        signals.append("agent")

    if any(tok in blob for tok in organize_tokens):
        patterns.append("你在整理桌面、资产清单或工作区文档类材料。")
        adjustments.append("文件类任务先列目录再读关键文件，输出结构化清单。")
        signals.append("organize")

    if not patterns:
        patterns.append("当前采样未形成强特征，按通用本地助手策略执行即可。")
        adjustments.append("缺证据时先提问或先列目录，不要猜测用户环境。")
        signals.append("generic")

    patterns.append("保持输出：中文、先结论、短段落、可执行下一步。")
    adjustments.append("长任务拆成可验证小步，每步对应工具或命令级产出。")
    signals.append("style")

    hour_hist = profile.get("hour_histogram") or []
    if hour_hist:
        peak = max(hour_hist, key=lambda x: x.get("count", 0))
        patterns.append(f"活跃高峰约在 {peak.get('hour', '?')} 点（本地时区）。")
        adjustments.append("在高峰时段优先安排需要交互与编译的重活。")
        signals.append("time")

    outcome = aggregate_task_outcomes()
    if outcome.get("total_success") or outcome.get("total_fail"):
        rate = outcome.get("overall_success_rate", 0.0)
        patterns.append(
            f"近一周工具调用总体成功率约 {rate}%，成功 {outcome.get('total_success', 0)} / 失败 {outcome.get('total_fail', 0)}。"
        )
        low_tools = [name for name, stat in outcome.get("by_tool", {}).items() if stat.get("failed", 0) >= 2 and stat.get("success_rate", 100) < 60]
        if low_tools:
            patterns.append("以下工具近期失败偏多：" + "、".join(low_tools[:5]))
            adjustments.append("对这些工具先缩小输入规模或换路径验证，再扩大任务范围。")
            signals.append("reliability")

    summary = "\n".join(f"- {item}" for item in patterns)
    _upsert_pattern("weekly", summary, adjustments, signals)
    return {
        "patterns": patterns,
        "adjustments": adjustments,
        "signals": signals,
        "recent_files": recent_files[:12],
        "profile": profile,
        "task_outcomes": outcome,
    }


def get_evolution_profile_text() -> str:
    data = infer_behavior_patterns()
    runtime = get_runtime_adjustments()
    outcome = data.get("task_outcomes", {})
    lines = ["## 自进化画像", "### 行为模式"]
    lines.extend(f"- {item}" for item in data["patterns"])
    lines.append("### 建议调整")
    lines.extend(f"- {item}" for item in data["adjustments"])
    if runtime.get("preferred_tools"):
        lines.append("### 工具优先级提示")
        for tool in runtime["preferred_tools"][:8]:
            lines.append(f"- {tool}")
    if runtime.get("prompt_hints"):
        lines.append("### 执行风格提示")
        for hint in runtime["prompt_hints"]:
            lines.append(f"- {hint}")
    if outcome:
        lines.append("### 工具成功率")
        lines.append(f"- 总体成功率约 {outcome.get('overall_success_rate', 0)}%")
        for name, stat in list((outcome.get("by_tool") or {}).items())[:6]:
            lines.append(
                f"- {name}: 成功 {stat.get('success', 0)} / 失败 {stat.get('failed', 0)} / 成功率 {stat.get('success_rate', 0)}%"
            )
    if data.get("recent_files"):
        lines.append("### 近期桌面文件")
        for row in data["recent_files"][:8]:
            lines.append(f"- {row.get('name', '?')}")
    return "\n".join(lines)


async def background_pattern_maintenance(interval_sec: int = 900, startup_delay_sec: int = 45) -> None:
    if startup_delay_sec > 0:
        try:
            await asyncio.sleep(startup_delay_sec)
        except asyncio.CancelledError:
            return

    while True:
        try:
            await asyncio.to_thread(infer_behavior_patterns)
        except Exception:
            _logger.exception("background_pattern_maintenance 出错，下次循环重试")
        try:
            await asyncio.sleep(interval_sec)
        except asyncio.CancelledError:
            break


def format_profile_for_llm() -> str:
    """供 Agent 工具读取的纯文本摘要。"""
    p24 = aggregate_profile(24)
    p7d = aggregate_profile(24 * 7)
    lines = [
        "## 设备画像（自动采样，仅供参考）",
        f"- 近24h 样本数: {p24['sample_count']}",
        f"- 近7天 样本数: {p7d['sample_count']}",
    ]
    if p7d["top_titles"]:
        lines.append("- 常见前台窗口（前5）：")
        for t in p7d["top_titles"][:5]:
            lines.append(f"  - {t['title'][:120]} ({t['count']})")
    if p7d["top_processes"]:
        lines.append("- 常见进程（前8）：")
        for pr in p7d["top_processes"][:8]:
            lines.append(f"  - {pr['name']} ({pr['count']})")
    for ins in build_insights(p7d):
        lines.append("- " + ins)
    return "\n".join(lines)


def upsert_daily_report() -> dict[str, Any]:
    day = time.strftime("%Y-%m-%d", time.localtime())
    p = aggregate_profile(24 * 7)
    insights = build_insights(p)
    lines = [f"# {day} 本地使用简报", "", "## 归纳", *("- " + i for i in insights), "", "## 数据概览", f"- 7日内样本: {p['sample_count']}"]
    summary = "\n".join(lines)
    ts = int(time.time())
    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute(
        """
        INSERT INTO daily_reports (day, summary, created_at) VALUES (?, ?, ?)
        ON CONFLICT(day) DO UPDATE SET summary = excluded.summary, created_at = excluded.created_at
        """,
        (day, summary, ts),
    )
    conn.commit()
    conn.close()
    return {"day": day, "summary": summary}


async def background_collector() -> None:
    if os.environ.get("DISABLE_BACKGROUND_OBSERVE", "").lower() in ("1", "true", "yes"):
        return
    interval = max(20, int(os.environ.get("OBSERVE_INTERVAL_SEC", "50")))
    while True:
        try:
            await asyncio.to_thread(record_sample)
        except Exception:
            _logger.exception("background_collector 出错，下次循环重试")
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break


class SampleResult(BaseModel):
    ok: bool
    detail: dict[str, Any]


@router.get("/status")
def observe_status() -> dict[str, Any]:
    since24 = _since_ts(24)
    conn = sqlite3.connect(BEHAVIOR_DB)
    n24 = conn.execute(
        "SELECT COUNT(*) FROM activity_samples WHERE ts >= ?", (since24,)
    ).fetchone()[0]
    last = conn.execute("SELECT MAX(ts) FROM activity_samples").fetchone()[0]
    conn.close()
    disabled = os.environ.get("DISABLE_BACKGROUND_OBSERVE", "").lower() in ("1", "true", "yes")
    return {
        "background_enabled": not disabled,
        "interval_sec_default": int(os.environ.get("OBSERVE_INTERVAL_SEC", "50")),
        "samples_last_24h": n24,
        "last_sample_ts": last,
    }


@router.post("/sample", response_model=SampleResult)
def observe_sample_now() -> SampleResult:
    d = record_sample()
    return SampleResult(ok=True, detail=d)


@router.get("/dashboard")
def observe_dashboard() -> dict[str, Any]:
    p24 = aggregate_profile(24)
    p7d = aggregate_profile(24 * 7)
    insights = build_insights(p7d)
    recent = desktop_recent_files(24)
    status = observe_status()
    return {
        "status": status,
        "profile_24h": p24,
        "profile_7d": p7d,
        "insights": insights,
        "desktop_recent_files": recent,
    }


@router.post("/report/today")
def observe_report_today() -> dict[str, Any]:
    return upsert_daily_report()


@router.get("/report/latest")
def observe_report_latest() -> dict[str, Any]:
    conn = sqlite3.connect(BEHAVIOR_DB)
    row = conn.execute(
        "SELECT day, summary, created_at FROM daily_reports ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return {"day": None, "summary": "", "hint": "尚无简报，请先调用 POST /observe/report/today"}
    return {"day": row[0], "summary": row[1], "created_at": row[2]}


@router.delete("/samples")
def observe_clear_samples() -> dict[str, bool]:
    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute("DELETE FROM activity_samples")
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/evolution")
def observe_evolution() -> dict[str, Any]:
    data = infer_behavior_patterns()
    return {
        "profile_text": get_evolution_profile_text(),
        "patterns": data["patterns"],
        "adjustments": data["adjustments"],
        "signals": data["signals"],
        "recent_files": data["recent_files"],
        "task_outcomes": data.get("task_outcomes", {}),
        "runtime_adjustments": get_runtime_adjustments(),
    }
