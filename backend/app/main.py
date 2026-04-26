import asyncio
import logging
import os
import time

from app.api import admin_models, auth, groups, model_status, models, notify, proxy, qa, users
from app.core.config import get_settings
from app.core.model_status import start_health_probe_scheduler
from app.middleware.audit import AuditMiddleware
from app.middleware.body_size_limit import BodySizeLimitMiddleware
from app.middleware.ip_limit import IPLimitMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.session_control import SessionControlMiddleware
from app.notification import sse_bridge
from app.tasks.cleanup import start_cleanup_scheduler
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("validation")

settings = get_settings()

# CORS 允许来源 — 通过环境变量控制，支持逗号分隔多个域名
_allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "")
if _allowed_origins_str:
    ALLOWED_ORIGINS = [o.strip() for o in _allowed_origins_str.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:80"]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# --- validation error logging ---
@app.exception_handler(RequestValidationError)
async def log_validation_error(request: Request, exc: RequestValidationError):
    try:
        body = await request.json()
    except Exception:
        body = None
    logger.error("422 body=%s errors=%s", body, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# CORS — 生产环境请通过 ALLOWED_ORIGINS 环境变量配置具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 请求体大小限制 (10MB)
app.add_middleware(BodySizeLimitMiddleware, max_size_mb=10)

# IP 访问次数限制（600 次/分钟，超过即阻断）
app.add_middleware(IPLimitMiddleware, max_requests=600, window_seconds=60)

# 单用户会话互斥控制（同一用户只允许单端同时访问）
app.add_middleware(SessionControlMiddleware, max_concurrent_sessions=1, timeout=10)

# 审计日志 (记录所有 API 请求)
app.add_middleware(AuditMiddleware)

# API 限流 (60 次/分钟)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Register routers
app.include_router(users.router, prefix="/admin/api", tags=["admin-users"])
app.include_router(models.router, prefix="/admin/api", tags=["admin-models"])
app.include_router(auth.router, prefix="/admin/api/auth", tags=["admin-auth"])
app.include_router(admin_models.router, prefix="/admin/api", tags=["admin-global-models"])
app.include_router(groups.router, prefix="/admin/api", tags=["admin-groups"])
app.include_router(qa.router, prefix="/admin/api", tags=["admin-qa-records"])
app.include_router(model_status.router, prefix="/admin/api", tags=["admin-model-status"])
app.include_router(proxy.proxy_router)  # 公开代理路由（/v1/*, /health）
app.include_router(proxy.admin_router, prefix='/admin/api')  # 管理路由（/metrics）
app.include_router(notify.router)


def _store_event(event, data):
    data["_event"] = event
    from app.api.notify import _MAX_RECENT, _recent_events, _recent_events_lock

    async def append():
        async with _recent_events_lock:
            _recent_events.append({**data, "ts": time.time()})
            if len(_recent_events) > _MAX_RECENT:
                _recent_events.clear()
                _recent_events.extend(_recent_events[-_MAX_RECENT:])

    _loop = asyncio.get_event_loop()
    try:
        _loop.create_task(append())
    except RuntimeError:
        asyncio.create_task(append())


sse_bridge.on_push(_store_event)


# 启动定时清理任务
start_cleanup_scheduler()

# 启动上游模型健康探测定时任务
start_health_probe_scheduler()
