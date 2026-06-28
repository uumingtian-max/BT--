"""
屏幕流 WebSocket 路由
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from screen_capture import get_capture_buffer, PIL_AVAILABLE

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/screen/latest")
def get_latest_screen():
    """获取最新屏幕截图（REST API）"""
    if not PIL_AVAILABLE:
        return {"ok": False, "error": "screen capture not available"}

    buf = get_capture_buffer()
    frame = buf.get_latest()

    if not frame:
        return {"ok": False, "error": "no frames captured yet"}

    return {
        "ok": True,
        "timestamp": frame.timestamp,
        "width": frame.width,
        "height": frame.height,
        "data": f"data:image/jpeg;base64,{frame.base64_jpg}",
        "size_bytes": frame.size_bytes,
    }


@router.get("/screen/info")
def get_screen_info():
    """获取屏幕捕获状态"""
    if not PIL_AVAILABLE:
        return {"available": False, "reason": "Pillow not installed"}

    buf = get_capture_buffer()
    return {
        "available": True,
        "running": buf.running,
        "frame_count": buf.frame_count(),
        "max_frames": buf.max_frames,
        "capture_interval_ms": buf.capture_interval_ms,
    }


@router.websocket("/ws/screen")
async def websocket_screen_stream(websocket: WebSocket):
    """WebSocket 实时屏幕流"""
    if not PIL_AVAILABLE:
        await websocket.close(code=1000, reason="screen capture not available")
        return

    await websocket.accept()
    logger.info("WebSocket 屏幕流已连接")

    buf = get_capture_buffer()
    last_frame_ts = 0.0

    try:
        while True:
            frame = buf.get_latest()

            if frame and frame.timestamp > last_frame_ts:
                await websocket.send_json(
                    {
                        "type": "screen",
                        "timestamp": frame.timestamp,
                        "width": frame.width,
                        "height": frame.height,
                        "data": frame.base64_jpg,  # 注意：这里直接发 base64，不需要前缀
                        "size_kb": round(frame.size_bytes / 1024, 2),
                    }
                )
                last_frame_ts = frame.timestamp

            # 非阻塞等待，避免 CPU 占用
            import asyncio

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info("WebSocket 屏幕流已断开")
    except Exception as exc:
        logger.error("WebSocket 屏幕流出错: %s", exc)
        await websocket.close(code=1011, reason=str(exc))
