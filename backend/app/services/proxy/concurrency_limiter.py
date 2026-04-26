"""上游模型并发限流器。

为每个上游模型配置独立的并发信号量，控制最大并发请求数。
超出的请求排队等待，等待超时后被主动拒绝（返回 429）。
支持 Prometheus 监控指标。
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any


logger = logging.getLogger(__name__)


class ModelConcurrencyLimiter:
    """基于信号量的上游模型并发限流器。

    功能：
    - 为每个上游模型配置独立的并发信号量（默认 8 个并发）
    - 超出的请求排队等待，等待超时后被主动拒绝（429）
    - Prometheus 监控指标
    - 支持动态调整模型的并发限制
    """

    def __init__(self, default_limit: int = 8, queue_timeout: float = 10.0):
        """初始化限流器。

        Args:
            default_limit: 默认每个模型的并发限制
            queue_timeout: 排队等待超时时间（秒）
        """
        self.default_limit = default_limit
        self.queue_timeout = queue_timeout
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        self._limits: Dict[str, int] = {}  # 模型 URL -> 自定义限制
        self._lock = asyncio.Lock()
        self._stats: Dict[str, dict] = {}

    async def _ensure_semaphore(self, model_url: str) -> asyncio.Semaphore:
        """获取或创建模型 URL 对应的信号量。"""
        async with self._lock:
            if model_url not in self._semaphores:
                # 使用自定义限制或默认限制
                limit = self._limits.get(model_url, self.default_limit)
                self._semaphores[model_url] = asyncio.Semaphore(limit)
                self._stats[model_url] = {
                    "waiting": 0,
                    "active": 0,
                    "total_requests": 0,
                    "rejected": 0,
                    "timeout": 0,
                    "queue_full": 0,
                    "created_at": time.time(),
                }
            return self._semaphores[model_url]

    async def acquire(
        self, model_url: str, key: Optional[str] = None
    ) -> tuple:
        """尝试获取信号量。

        Args:
            model_url: 上游模型 URL
            key: 可选的用户标识，用于日志追踪

        Returns:
            Tuple[Optional[asyncio.Semaphore], bool]:
                - (semaphore, True) 获取成功
                - (None, False) 排队超时
        """
        sem = await self._ensure_semaphore(model_url)
        stats = self._stats[model_url]

        stats["total_requests"] += 1
        stats["waiting"] += 1
        stats["active"] += 1

        logger.debug(
            "[Concurrency] Acquire called for model=%s key=%s waiting=%d",
            model_url, key or "global",
            stats["waiting"],
        )

        # 队列过长时直接拒绝，不加入有效等待
        if stats["waiting"] >= self.default_limit * 2:
            stats["waiting"] -= 1
            stats["active"] -= 1
            stats["rejected"] += 1
            stats["queue_full"] += 1
            logger.warning(
                "[Concurrency] Queue full rejecting model=%s waiting=%d",
                model_url,
                stats["waiting"],
            )
            return None, False

        # 尝试在限定时间内获取信号量
        try:
            await asyncio.wait_for(sem.acquire(), timeout=self.queue_timeout)
            stats["waiting"] -= 1
            logger.debug(
                "[Concurrency] Acquired for model=%s waiting=%d",
                model_url,
                stats["waiting"],
            )
            return sem, True
        except asyncio.TimeoutError:
            # 排队超时
            stats["waiting"] -= 1
            stats["active"] -= 1
            stats["rejected"] += 1
            stats["timeout"] += 1
            logger.warning(
                "[Concurrency] Timeout waiting for model=%s waiting=%d timeout=%.1fs",
                model_url,
                stats["waiting"],
                self.queue_timeout,
            )
            return None, False

    def release(self, sem: asyncio.Semaphore, model_url: str):
        """释放信号量。

        Args:
            sem: 之前 acquire 返回的信号量
            model_url: 模型 URL
        """
        stats = self._stats.get(model_url)
        if stats:
            stats["active"] -= 1
        try:
            sem.release()
            logger.debug(
                "[Concurrency] Released for model=%s",
                model_url,
            )
        except Exception:
            # 信号量已释放或异常，忽略
            logger.debug(
                "[Concurrency] Release failed for model=%s",
                model_url,
                exc_info=True,
            )

    def get_stats(self, model_url: str) -> dict:
        """获取模型的限流统计信息。"""
        stats = self._stats.get(model_url)
        if stats:
            return {
                "waiting": stats["waiting"],
                "active": stats["active"],
                "total_requests": stats["total_requests"],
                "rejected": stats["rejected"],
                "timeout": stats["timeout"],
                "queue_full": stats["queue_full"],
                "uptime": time.time() - stats["created_at"],
            }
        return {
            "waiting": 0,
            "active": 0,
            "total_requests": 0,
            "rejected": 0,
            "timeout": 0,
            "queue_full": 0,
            "uptime": 0,
        }

    def get_all_stats(self) -> dict:
        """获取所有模型的统计信息。"""
        all_stats = {}
        for url, stats in self._stats.items():
            all_stats[url] = self.get_stats(url)
        return all_stats

    def get_prometheus_metrics(self) -> str:
        """获取 Prometheus 格式的监控指标。"""
        lines = []
        lines.append("# HELP concurrency_limiter_total_requests Total requests attempting to acquire")
        lines.append("# TYPE concurrency_limiter_total_requests counter")

        lines.append("# HELP concurrency_limiter_rejected Total requests rejected due to queue full/timeout")
        lines.append("# TYPE concurrency_limiter_rejected counter")

        lines.append("# HELP concurrency_limiter_rejected_queue_full Rejections due to queue being full")
        lines.append("# TYPE concurrency_limiter_rejected_queue_full counter")

        lines.append("# HELP concurrency_limiter_rejected_timeout Rejections due to timeout while waiting")
        lines.append("# TYPE concurrency_limiter_rejected_timeout counter")

        lines.append("# HELP concurrency_limiter_active Current number of active requests")
        lines.append("# TYPE concurrency_limiter_active gauge")

        lines.append("# HELP concurrency_limiter_waiting Current number of requests waiting in queue")
        lines.append("# TYPE concurrency_limiter_waiting gauge")

        lines.append("# HELP concurrency_limiter_seconds_timeout Queue wait timeout in seconds")
        lines.append("# TYPE concurrency_limiter_seconds_timeout gauge")
        lines.append(f"concurrency_limiter_seconds_timeout {{model=\"_global\"}} {self.queue_timeout}")

        lines.append("# HELP concurrency_limiter_seconds_limit Maximum concurrent requests limit")
        lines.append("# TYPE concurrency_limiter_seconds_limit gauge")
        lines.append(f"concurrency_limiter_seconds_limit {{model=\"_global\"}} {self.default_limit}")

        for url, stats in self._stats.items():
            model_label = url.replace("/", "_").replace(":", "_").replace(".", "_")
            total = stats["total_requests"]
            rejected = stats["rejected"]
            queue_full = stats["queue_full"]
            timeout = stats["timeout"]
            active = stats["active"]
            waiting = stats["waiting"]

            lines.append(f'concurrency_limiter_total_requests{{model="{model_label}"}} {total}')
            lines.append(f'concurrency_limiter_rejected{{model="{model_label}"}} {rejected}')
            lines.append(f'concurrency_limiter_rejected_queue_full{{model="{model_label}"}} {queue_full}')
            lines.append(f'concurrency_limiter_rejected_timeout{{model="{model_label}"}} {timeout}')
            lines.append(f'concurrency_limiter_active{{model="{model_label}"}} {active}')
            lines.append(f'concurrency_limiter_waiting{{model="{model_label}"}} {waiting}')

        lines.append("")  # Prometheus requires trailing newline
        return "\n".join(lines)

    def set_model_limit(self, model_url: str, limit: int):
        """为特定模型设置并发限制。"""
        self._limits[model_url] = limit
        logger.info(
            "[Concurrency] Set limit for %s: %d",
            model_url,
            limit,
        )

    def create_model_limiter(self, model_url: str, limit: Optional[int] = None):
        """创建一个独立的新模型限流器（用于自定义限制的模型）。

        Args:
            model_url: 模型 URL
            limit: 并发限制，如果为 None 则使用默认限制
        """
        actual_limit = limit if limit is not None else self.default_limit
        self._limits[model_url] = actual_limit
        # 立即创建信号量
        asyncio.create_task(self._ensure_semaphore(model_url))
        logger.info(
            "[Concurrency] Created limiter for %s with limit=%d",
            model_url,
            actual_limit,
        )


# 全局并发限流器实例（上游模型默认 8 个并发排队等待 15 秒）
_global_concurrency_limiter = ModelConcurrencyLimiter(default_limit=8, queue_timeout=15.0)


def get_global_concurrency_limiter() -> ModelConcurrencyLimiter:
    """获取全局并发限流器实例。"""
    return _global_concurrency_limiter
