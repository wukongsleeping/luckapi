"""请求限流中间件，防止 API 滥用。"""

import logging
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """基于 API Key 的 Redis 限流，支持分布式部署。

    使用原始 ASGI 中间件而非 BaseHTTPMiddleware，兼容 WebSocket。
    """

    def __init__(self, app, requests_per_minute: int = 60):
        self.app = app
        self.requests_per_minute = requests_per_minute

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        api_key = self._get_api_key(request)
        path = request.url.path

        # 只对代理接口限流
        if path.startswith("/v1/"):
            if api_key:
                try:
                    from app.db.redis import get_redis

                    redis = await get_redis()
                    key = f"ratelimit:{api_key}"
                    window = 60

                    current = await redis.incr(key)
                    if current == 1:
                        await redis.expire(key, window)

                    if current > self.requests_per_minute:
                        logger.warning(f"Rate limit exceeded for key: {api_key[:10]}...")
                        response = JSONResponse(
                            status_code=429,
                            content={
                                "detail": "Too many requests. Please retry after 1 minute.",
                                "retry_after": 60,
                            },
                            headers={"Retry-After": "60"},
                        )
                        await response(scope, receive, send)
                        return
                except Exception:
                    logger.warning("Redis unavailable for rate limiting, allowing request")

        await self.app(scope, receive, send)

    @staticmethod
    def _get_api_key(request: Request) -> str:
        """从请求中提取 API Key。"""
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        if auth_header:
            return auth_header
        return ""
