"""轻量级 SSE 消息推送桥接器。

在代理请求完成（写入 QaRecord 后）触发 push()，所有连接的客户端实时收到事件。
"""

import asyncio
import json
import time
import logging
from asyncio import Queue

logger = logging.getLogger(__name__)


class SSEBridge:
    """内存队列广播，支持有限数量客户端。"""

    def __init__(self, max_clients: int = 50, queue_max: int = 30):
        self._clients: set[Queue] = set()
        self._max_clients = max_clients
        self._queue_max = queue_max
        self._callbacks: list = []

    async def subscribe(self):
        """创建一个订阅队列，yield 供生成器使用。"""
        if len(self._clients) >= self._max_clients:
            logger.warning("SSE clients at capacity: %d", len(self._clients))
            return
        q = Queue(maxsize=self._queue_max)
        self._clients.add(q)
        try:
            yield q
        finally:
            self._clients.discard(q)

    def on_push(self, callback):
        """注册 push 事件回调（用于存储/审计）。"""
        self._callbacks.append(callback)

    async def push(self, event: str, data: dict):
        data["ts"] = time.time()
        payload = {"event": event, **data}
        text = json.dumps(payload, ensure_ascii=False)

        # Callbacks (e.g., _store_event) - call synchronously, they're fast
        for cb in self._callbacks:
            try:
                cb(event, data)
            except Exception:
                logger.debug("Push callback failed", exc_info=True)

        # Fire-and-forget: run client broadcast in a task to not block the handler
        async def _broadcast():
            for q in self._clients:
                try:
                    q.put_nowait(text)
                except asyncio.QueueFull:
                    logger.warning("SSE client queue full, disconnecting")
                    await self._cleanup(q)

        asyncio.create_task(_broadcast())

    @staticmethod
    async def _cleanup(q: Queue):
        """清理死亡队列。"""
        try:
            q.get_nowait()
        except Exception:
            pass

    def client_count(self) -> int:
        return len(self._clients)


# 全局单例
sse_bridge = SSEBridge(max_clients=50, queue_max=30)
