import asyncio
import logging
import time
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import users, models, proxy, auth, groups, admin_models, qa, notify
from app.middleware.body_size_limit import BodySizeLimitMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.audit import AuditMiddleware
from app.core.config import get_settings
from app.notification import sse_bridge

logger = logging.getLogger("validation")

settings = get_settings()

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


# CORS - 生产环境应配置具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求体大小限制 (10MB)
app.add_middleware(BodySizeLimitMiddleware, max_size_mb=10)

# 审计日志 (记录所有 API 请求)
app.add_middleware(AuditMiddleware)

# API 限流 (60 次/分钟)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Register routers
app.include_router(users.router, prefix="/admin/api", tags=["admin-users"])
app.include_router(models.router, prefix="/admin/api", tags=["admin-models"])
app.include_router(auth.router, prefix="/admin/api/auth", tags=["admin-auth"])
app.include_router(
    admin_models.router, prefix="/admin/api", tags=["admin-global-models"]
)
app.include_router(groups.router, prefix="/admin/api", tags=["admin-groups"])
app.include_router(qa.router, prefix="/admin/api", tags=["admin-qa-records"])
app.include_router(proxy.router)  # no prefix, mounted at root
app.include_router(notify.router)


def _store_event(event, data):
    data["_event"] = event
    from app.api.notify import _recent_events, _recent_events_lock, _MAX_RECENT

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
