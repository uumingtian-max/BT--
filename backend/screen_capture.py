"""
实时屏幕捕获与 WebSocket 推送
用于 Agent 操作可视化
"""

import base64
import io
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PIL import ImageGrab

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available, screen capture disabled")


@dataclass
class ScreenCapture:
    """屏幕快照"""

    timestamp: float
    base64_jpg: str
    width: int
    height: int
    size_bytes: int


class ScreenCaptureBuffer:
    """环形缓冲池，存储最近 N 帧"""

    def __init__(self, max_frames: int = 60, capture_interval_ms: float = 500):
        self.max_frames = max_frames
        self.capture_interval_ms = capture_interval_ms
        self.frames: deque[ScreenCapture] = deque(maxlen=max_frames)
        self.lock = threading.Lock()
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.last_capture_time = 0.0

    def start(self):
        """启动后台捕获线程"""
        if self.running or not PIL_AVAILABLE:
            return

        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True, name="ScreenCaptureWorker")
        self.capture_thread.start()
        logger.info("屏幕捕获已启动（每 %.0fms 一帧，最多 %d 帧缓冲）", self.capture_interval_ms, self.max_frames)

    def stop(self):
        """停止捕获"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        logger.info("屏幕捕获已停止")

    def _capture_loop(self):
        """后台捕获线程"""
        while self.running:
            try:
                now = time.time()
                elapsed = (now - self.last_capture_time) * 1000

                if elapsed < self.capture_interval_ms:
                    time.sleep((self.capture_interval_ms - elapsed) / 1000)
                    continue

                self._do_capture()
                self.last_capture_time = time.time()

            except Exception as exc:
                logger.debug("屏幕捕获出错: %s", exc)
                time.sleep(0.5)

    def _do_capture(self):
        """执行一次屏幕捕获"""
        try:
            if not PIL_AVAILABLE:
                return

            # 捕获整个屏幕
            screenshot = ImageGrab.grab()
            width, height = screenshot.size

            # 压缩为 JPEG
            buffer = io.BytesIO()
            screenshot.save(buffer, format="JPEG", quality=75, optimize=True)
            jpeg_bytes = buffer.getvalue()

            # 编码为 Base64
            b64 = base64.b64encode(jpeg_bytes).decode("ascii")

            capture = ScreenCapture(
                timestamp=time.time(), base64_jpg=b64, width=width, height=height, size_bytes=len(jpeg_bytes)
            )

            with self.lock:
                self.frames.append(capture)

        except Exception as exc:
            logger.debug("捕获失败: %s", exc)

    def get_latest(self) -> Optional[ScreenCapture]:
        """获取最新帧"""
        with self.lock:
            return self.frames[-1] if self.frames else None

    def get_frames(self, limit: int = 10) -> list[ScreenCapture]:
        """获取最近 N 帧"""
        with self.lock:
            return list(self.frames)[-limit:]

    def frame_count(self) -> int:
        """当前缓冲帧数"""
        with self.lock:
            return len(self.frames)


# 全局单例
_capture_buffer: Optional[ScreenCaptureBuffer] = None


def get_capture_buffer() -> ScreenCaptureBuffer:
    """获取或初始化全局捕获缓冲"""
    global _capture_buffer
    if _capture_buffer is None:
        _capture_buffer = ScreenCaptureBuffer()
    return _capture_buffer


def init_screen_capture():
    """初始化屏幕捕获（在应用启动时调用）"""
    if not PIL_AVAILABLE:
        logger.warning("屏幕捕获不可用（缺少 Pillow）")
        return

    buf = get_capture_buffer()
    buf.start()


def shutdown_screen_capture():
    """关闭屏幕捕获（在应用关闭时调用）"""
    global _capture_buffer
    if _capture_buffer:
        _capture_buffer.stop()
        _capture_buffer = None
