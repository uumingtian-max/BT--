#!/usr/bin/env python3
"""
BT（黑光）统一启动器
旧名 BKLT 黑光、ONYX-OVERRIDE 作为历史兼容名保留。

用法：python start.py [mode]

模式（mode）：
  app          - 默认：启动 Electron 桌面应用（后端 + 前端 + Electron）
  dev          - 开发模式：后端 hot-reload + React dev server
  backend      - 仅启动后端 FastAPI
  mobile       - 局域网/Tailscale 手机访问模式
  vllm         - 先启动本机 vLLM，再启动应用
  tts          - 仅启动 F5-TTS 服务
  help         - 显示帮助

示例：
  python start.py            # 等同 python start.py app
  python start.py dev        # 开发模式
  python start.py mobile     # 手机访问模式
"""

import sys
import os
import subprocess
import platform
import shutil
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
ELECTRON_DIR = ROOT / "electron"
SCRIPTS_DIR = ROOT / "scripts"

IS_WINDOWS = platform.system() == "Windows"
PYTHON = sys.executable
NPM = shutil.which("npm") or "npm"
NODE = shutil.which("node") or "node"


# ─── 颜色输出 ───────────────────────────────────────────────
def c(text, color):
    colors = {"red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
              "blue": "\033[94m", "cyan": "\033[96m", "reset": "\033[0m"}
    if IS_WINDOWS and "WT_SESSION" not in os.environ:
        return text  # 普通 cmd 不支持 ANSI
    return f"{colors.get(color,'')}{text}{colors['reset']}"


def info(msg):  print(c(f"[INFO]  {msg}", "cyan"))
def ok(msg):    print(c(f"[OK]    {msg}", "green"))
def warn(msg):  print(c(f"[WARN]  {msg}", "yellow"))
def err(msg):   print(c(f"[ERROR] {msg}", "red"))


# ─── 环境预检 ────────────────────────────────────────────────
def check_env():
    issues = []

    # Python 版本
    if sys.version_info < (3, 10):
        issues.append(f"Python 3.10+ 必须，当前 {sys.version}")

    # Node.js
    try:
        ver = subprocess.check_output([NODE, "--version"], text=True).strip()
        major = int(ver.lstrip("v").split(".")[0])
        if major < 18:
            issues.append(f"Node.js 18+ 必须，当前 {ver}")
        else:
            ok(f"Node.js {ver}")
    except Exception:
        issues.append("Node.js 未安装或不在 PATH")

    # .env 文件
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        warn(".env 不存在，将从 .env.example 复制")
        example = BACKEND_DIR / ".env.example"
        if example.exists():
            shutil.copy(example, env_file)
            ok("已创建 backend/.env（请检查配置）")
        else:
            issues.append("backend/.env 和 backend/.env.example 均不存在")

    # Ollama（仅警告）
    if shutil.which("ollama") is None:
        warn("ollama 未在 PATH 中，Ollama 路线将不可用")

    if issues:
        err("环境检测发现问题：")
        for i in issues:
            print(f"  • {i}")
        sys.exit(1)

    ok("环境检测通过")


# ─── 进程管理 ────────────────────────────────────────────────
procs: list[subprocess.Popen] = []


def run(cmd, cwd=None, env=None, shell=False):
    """启动子进程并加入全局列表"""
    p = subprocess.Popen(
        cmd, cwd=cwd or ROOT, env=env,
        shell=shell and IS_WINDOWS,  # Windows 需要 shell=True 跑 npm
    )
    procs.append(p)
    return p


def wait_for_port(port: int, timeout=30):
    """等待端口就绪"""
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def kill_all():
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass


# ─── 各模式启动函数 ──────────────────────────────────────────
def start_backend(dev: bool = False, host: str | None = None) -> subprocess.Popen:
    info("启动后端 FastAPI …")
    bind_host = host or os.environ.get("BACKEND_HOST", "127.0.0.1")
    reload_flag = ["--reload"] if dev else []
    cmd = [PYTHON, "-m", "uvicorn", "main:app",
           "--host", bind_host, "--port", "8000"] + reload_flag
    p = run(cmd, cwd=BACKEND_DIR)
    if not wait_for_port(8000, timeout=20):
        err("后端启动超时（8000 端口未就绪）")
        kill_all(); sys.exit(1)
    ok("后端就绪 → http://127.0.0.1:8000")
    return p


def start_frontend_dev():
    info("启动 React 开发服务器 …")
    cmd = [NPM, "run", "dev"] if IS_WINDOWS else ["npm", "run", "dev"]
    p = run(cmd, cwd=FRONTEND_DIR, shell=True)
    if not wait_for_port(3000, timeout=30):
        warn("React dev server 可能尚未就绪，继续等待 …")
    else:
        ok("前端就绪 → http://localhost:3000")
    return p


def start_electron():
    info("启动 Electron 桌面壳 …")
    cmd = [NPM, "start"] if IS_WINDOWS else ["npm", "start"]
    return run(cmd, cwd=ROOT, shell=True)


def start_tts():
    info("启动 F5-TTS …")
    tts_script = SCRIPTS_DIR / "start_f5_tts.py"
    if not tts_script.exists():
        err(f"找不到 TTS 启动脚本：{tts_script}")
        return None
    return run([PYTHON, str(tts_script)])


def start_vllm():
    info("启动本机 vLLM（Gemma-4）…")
    vllm_script = SCRIPTS_DIR / "START_VLLM_GEMMA4.bat"
    if IS_WINDOWS and vllm_script.exists():
        return run([str(vllm_script)], shell=True)
    else:
        err("vLLM 启动脚本仅支持 Windows，或脚本不存在")
        return None


# ─── 模式入口 ────────────────────────────────────────────────
def mode_app():
    check_env()
    start_backend()
    start_electron()
    info("BKLT 黑光已启动，关闭窗口或按 Ctrl+C 退出")
    try:
        procs[-1].wait()
    except KeyboardInterrupt:
        pass
    finally:
        kill_all()


def mode_dev():
    check_env()
    start_backend(dev=True)
    start_frontend_dev()
    info("BKLT 黑光开发模式就绪，按 Ctrl+C 退出")
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        kill_all()


def mode_backend():
    check_env()
    p = start_backend()
    info("仅后端模式，按 Ctrl+C 退出")
    try:
        p.wait()
    except KeyboardInterrupt:
        pass
    finally:
        kill_all()


def mode_mobile():
    import socket
    check_env()
    # 获取本机局域网 IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"

    start_backend(host="0.0.0.0")
    ok(f"手机访问地址 → http://{local_ip}:8000")
    info("保持运行，按 Ctrl+C 退出")
    try:
        procs[-1].wait()
    except KeyboardInterrupt:
        pass
    finally:
        kill_all()


def mode_vllm():
    check_env()
    p = start_vllm()
    if p:
        info("等待 vLLM 就绪（8001 端口）…")
        if wait_for_port(8001, timeout=120):
            ok("vLLM 就绪")
            start_backend()
            start_electron()
            try:
                procs[-1].wait()
            except KeyboardInterrupt:
                pass
            finally:
                kill_all()
        else:
            err("vLLM 启动超时")
            kill_all(); sys.exit(1)


def mode_tts():
    p = start_tts()
    if p:
        info("F5-TTS 已启动，按 Ctrl+C 退出")
        try:
            p.wait()
        except KeyboardInterrupt:
            pass


# ─── 主入口 ──────────────────────────────────────────────────
MODES = {
    "app": mode_app,
    "dev": mode_dev,
    "backend": mode_backend,
    "mobile": mode_mobile,
    "vllm": mode_vllm,
    "tts": mode_tts,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BKLT 黑光 / BLACKLIGHT 统一启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("mode", nargs="?", default="app",
                        choices=list(MODES.keys()) + ["help"],
                        help="启动模式（默认 app）")
    args = parser.parse_args()

    if args.mode == "help":
        parser.print_help()
        sys.exit(0)

    print(c("\n  ██████╗ ██╗  ██╗██╗  ████████╗", "cyan"))
    print(c("  ██╔══██╗██║ ██╔╝██║  ╚══██╔══╝", "cyan"))
    print(c("  ██████╔╝█████╔╝ ██║     ██║   ", "cyan"))
    print(c("  ██╔══██╗██╔═██╗ ██║     ██║   ", "cyan"))
    print(c("  ██████╔╝██║  ██╗███████╗██║   ", "cyan"))
    print(c("  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝   ", "cyan"))
    print(c("  黑光 / BLACKLIGHT  —  Local AI Agent Workbench\n", "yellow"))

    MODES[args.mode]()
