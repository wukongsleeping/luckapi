import logging
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class BodySizeLimitMiddleware:
    """限制请求体大小，防止内存溢出攻击。

    使用原始 ASGI 中间件而非 BaseHTTPMiddleware，兼容 WebSocket。
    """

    def __init__(self, app, max_size_mb: int = 10):
        self.app = app
        self.max_size = max_size_mb * 1024 * 1024

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            logger.warning(
                f"Request body too large: {int(content_length)} bytes "
                f"(max: {self.max_size}). client={request.client.host}"
            )
            response = JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request body too large. Max size: {self.max_size // (1024 * 1024)}MB"
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
