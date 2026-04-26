"""代理路由模块。

提供 OpenAI 兼容的代理接口，转发请求到上游模型服务。
路由层仅负责参数解析和调用服务层。
"""

import json
import logging
import time

from app.core.model_status import track_request_end, track_request_start
from app.db.session import get_db
from app.models.models import UserModel
from app.services.proxy.core import forward_chat
from app.services.proxy.utils import parse_authorization
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.proxy.auth import get_user_by_api_key, get_user_models_from_cache

logger = logging.getLogger(__name__)

router = APIRouter()


@router.api_route("/v1/chat/completions", methods=["GET", "POST"])
async def proxy_chat(request: Request, db: AsyncSession = Depends(get_db)):
    """Chat 补全代理入口。"""
    body = await request.body()
    request_data = json.loads(body) if body else {}
    is_stream = request_data.get("stream", False)
    target_model = request_data.get("model", "default")

    from app.services.proxy.core import proxy_flow

    return await proxy_flow(
        request,
        db,
        "chat/completions",
        target_model,
        is_stream,
        body,
    )


@router.api_route("/v1/completions", methods=["GET", "POST"])
async def proxy_completions(request: Request, db: AsyncSession = Depends(get_db)):
    """文本补全代理入口。"""
    body = await request.body()
    request_data = json.loads(body) if body else {}
    is_stream = request_data.get("stream", False)
    target_model = request_data.get("model", "default")

    from app.services.proxy.core import proxy_flow

    return await proxy_flow(
        request,
        db,
        "completions",
        target_model,
        is_stream,
        body,
    )


@router.get("/health")
async def health_check():
    """健康检查，不暴露内部服务细节。"""
    return {"status": "ok"}


@router.get("/metrics")
async def metrics():
    """Prometheus 监控指标端点。

    返回并发限流器的统计指标，供 Prometheus 抓取。
    """
    from app.services.proxy.concurrency_limiter import _global_concurrency_limiter

    return JSONResponse(
        content={"status": "ok", "metrics": _global_concurrency_limiter.get_all_stats()},
    )


@router.get("/v1/models")
async def list_models(request: Request, db: AsyncSession = Depends(get_db)):
    """OpenAI 兼容的模型列表接口。"""
    auth_header = request.headers.get("authorization")
    api_key = parse_authorization(auth_header or "")

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="缺少 API Key，请在请求头中添加 Authorization: Bearer <your_api_key>",
        )

    user, key_obj = await get_user_by_api_key(api_key, db, request)
    if not user:
        raise HTTPException(status_code=401, detail="API Key 无效或已被停用，请联系管理员")

    models = await get_user_models_from_cache(user.id, db)

    items = []
    for m in models:
        items.append(
            {
                "id": (
                    m.access_name if hasattr(m, "access_name") and m.access_name else m.model_name
                ),
                "object": "model",
                "created": int(m.created_at.timestamp()) if m.created_at else int(time.time()),
                "owned_by": "user",
            }
        )

    return {"data": items}
