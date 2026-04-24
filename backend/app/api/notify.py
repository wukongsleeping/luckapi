"""WebSocket 通知端点。

FastAPI WebSocket 推送，客户端连接到此端点后持续接收代理请求事件。
"""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.notification import sse_bridge

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/v1/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket 推送流。连接到此端点即可持续接收事件。"""
    # 检查认证：从 query param 获取 token
    token = websocket.query_params.get("token", "")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    await websocket.accept()
    q = None
    try:
        async for queue in sse_bridge.subscribe():
            q = queue
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30)
                    await websocket.send_text(data)
                except asyncio.TimeoutError:
                    # 每 30s 发一次心跳包
                    await websocket.send_text("heartbeat")
                finally:
                    q = None
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        if q:
            await sse_bridge._cleanup(q)


# ─── 最近事件查询 ─────────────────────────────

_recent_events: list[dict] = []
_recent_events_lock = asyncio.Lock()
_MAX_RECENT = 100


@router.get("/v1/events/recent")
async def recent_events(since: int = 0):
    """查询最近 N 条记录，supports since timestamp (ms) for reconnect recovery."""
    async with _recent_events_lock:
        if since > 0:
            cutoff = since / 1000.0  # ms → s
            return [
                e for e in _recent_events[-_MAX_RECENT:] if e.get("ts", 0) >= cutoff
            ]
        return _recent_events[-_MAX_RECENT:]


# ─── 工具端点 ─────────────────────────────


@router.get("/v1/events/stats")
async def events_stats():
    """查看当前 WebSocket 连接统计。"""
    return {"connected_clients": sse_bridge.client_count()}
