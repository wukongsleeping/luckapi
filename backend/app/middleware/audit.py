"""请求审计日志，记录所有 API 调用用于监控和计费。"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from starlette.requests import Request

audit_logger = logging.getLogger("luckapi.audit")
audit_logger.setLevel(logging.INFO)
if not audit_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s AUDIT [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)

_audit_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="audit")


class AuditMiddleware:
    """记录所有 API 请求的审计日志。

    使用原始 ASGI 中间件而非 BaseHTTPMiddleware，兼容 WebSocket。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        start_time = time.time()

        api_key = "anonymous"
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:20] + "..."

        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        # 处理请求
        await self.app(scope, receive, send)

        # 计算耗时（响应状态码需要等中间件链完成才能获取）
        duration_ms = (time.time() - start_time) * 1000

        duration_ms = round(duration_ms, 2)
        message = (
            f"method={method} path={path} ip={client_ip} "
            f"api_key={api_key} duration={duration_ms}ms"
        )
        _audit_executor.submit(audit_logger.info, message)
