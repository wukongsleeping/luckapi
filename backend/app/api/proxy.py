import asyncio
import aiohttp
import json
import time
import logging
from typing import Any
from aiohttp import ClientConnectionError
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.background import BackgroundTasks
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.redis import get_redis
from app.models.models import ApiKey, User, UserModel, QaRecord
from app.core.utils import now
from app.notification import sse_bridge

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter()


def _gen_event_id() -> str:
    """Generate a unique event ID for correlating qa_started/qa_completed."""
    return f"{time.time():.6f}{id(asyncio.current_task()):x}"


def parse_authorization(auth_header: str) -> str:
    if not auth_header:
        return ""
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return auth_header


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def _check_ip_whitelist(allowed_ips: str, client_ip: str) -> bool:
    if not allowed_ips or not allowed_ips.strip():
        return True
    ip_list = [ip.strip() for ip in allowed_ips.split(",") if ip.strip()]
    if not ip_list:
        return True
    return client_ip in ip_list


async def get_user_by_api_key(
    api_key: str, db: AsyncSession, request: Request = None
):
    client_ip = _get_client_ip(request) if request else ""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key == api_key,
            ApiKey.status == "active",
        )
    )
    api_key_obj = result.scalar_one_or_none()
    if not api_key_obj:
        return None, None

    if api_key_obj.expires_at and api_key_obj.expires_at < now():
        await db.execute(
            update(ApiKey).where(ApiKey.id == api_key_obj.id).values(status="expired")
        )
        await db.commit()
        return None, None

    result = await db.execute(select(User).where(User.id == api_key_obj.user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None, None

    if user.status != "active":
        return None, None

    if request and client_ip:
        if not _check_ip_whitelist(user.allowed_ips, client_ip):
            logger.warning(f"IP {client_ip} not in whitelist for user {user.username}")
            return None, None

    api_key_obj.last_used_at = now()
    await db.commit()

    return user, api_key_obj


async def _get_user_models_from_cache(user_id: int, db: AsyncSession):
    cache_key = f"user_models:{user_id}"
    try:
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            model_ids = json.loads(cached)
            if isinstance(model_ids, list):
                result = await db.execute(
                    select(UserModel).where(
                        UserModel.user_id == user_id,
                        UserModel.status == "active",
                        UserModel.id.in_(model_ids),
                    ),
                )
                return result.scalars().all()
            else:
                pass
    except Exception:
        pass

    result = await db.execute(
        select(UserModel).where(
            UserModel.user_id == user_id,
            UserModel.status == "active",
        )
    )
    models = result.scalars().all()

    try:
        redis = await get_redis()
        await redis.set(
            cache_key,
            json.dumps([m.id for m in models]),
            ex=180,
        )
    except Exception:
        pass

    return models


async def _save_qa_record(
    user_id: int,
    api_key_id: int,
    target_model: str,
    method: str,
    request_body: str,
    response_body: str,
    upstream_status: int,
    request_tokens: int,
    response_tokens: int,
    total_tokens: int,
    latency_ms: int,
    status: str,
    client_ip: str,
):
    """异步保存 Q&A 记录到数据库（非阻塞，使用新 session 避免生命周期问题）。"""
    logger.info(f"[QA Save] user_id={user_id}, model={target_model}, status={status}")
    from app.db.session import get_async_session_ctx

    try:
        async with get_async_session_ctx() as session:
            record = QaRecord(
                user_id=user_id,
                api_key_id=api_key_id,
                target_model=target_model,
                method=method,
                request_body=request_body,
                response_body=response_body,
                upstream_status=upstream_status,
                request_tokens=request_tokens,
                response_tokens=response_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                status=status,
                client_ip=client_ip or None,
            )
            session.add(record)
            await session.commit()
            logger.info(f"[QA Save] saved record_id={record.id}")
    except Exception:
        logger.error("Failed to save QA record", exc_info=True)


def _extract_tokens(data: dict) -> tuple:
    usage = data.get("usage", {})
    return (
        usage.get("prompt_tokens"),
        usage.get("completion_tokens"),
        usage.get("total_tokens"),
    )


def _extract_stream_tokens(sse_text: str) -> tuple:
    for line in sse_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("data: [DONE]") or line == "[DONE]":
            continue
        if line.startswith("data:"):
            line = line[5:].strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            usage = data.get("usage") or (
                data.get("choices") and data["choices"][-1].get("usage")
            )
            if usage and isinstance(usage, dict):
                return (
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    usage.get("total_tokens"),
                )
        except (json.JSONDecodeError, TypeError):
            pass
    return None, None, None


async def _proxy_flow(
    request: Request,
    db: AsyncSession,
    target_path: str,
    target_model: str,
    is_stream: bool,
    body: bytes,
    response_json: bool = False,
):
    """Shared proxy flow for chat and completions endpoints."""
    auth_header = request.headers.get("authorization")
    api_key = parse_authorization(auth_header)

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    user, key_obj = await get_user_by_api_key(api_key, db, request)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    models = await _get_user_models_from_cache(user.id, db)
    if not models:
        raise HTTPException(status_code=403, detail="No models bound to this account")

    target = None
    for m in models:
        if m.model_name == target_model:
            target = m
            break
        if target_model.isdigit() and m.id == int(target_model):
            target = m
            break
    if not target:
        if target_model.isdigit():
            for m in models:
                if m.id == int(target_model):
                    target = m
                    break
    if not target:
        target = models[0]

    headers = {
        "Authorization": f"Bearer {target.api_key}",
        "Content-Type": "application/json",
    }

    for header in ["user-agent", "accept", "accept-encoding"]:
        if request.headers.get(header):
            headers[header] = request.headers[header]

    event_id = _gen_event_id()
    start_time = time.time()

    try:
        await sse_bridge.push(
            "qa_started",
            {
                "event_id": event_id,
                "user_id": user.id,
                "model": target_model,
                "client_ip": _get_client_ip(request),
                "start_time": start_time,
            },
        )
    except Exception:
        logger.debug("SSE push failed (best-effort)", exc_info=True)

    request_body_str = body.decode("utf-8", errors="replace")

    record_data = {
        "user_id": user.id,
        "api_key_id": key_obj.id if key_obj else None,
        "target_model": target_model,
        "method": "POST",
        "request_body": request_body_str,
        "start_time": start_time,
        "client_ip": _get_client_ip(request),
        "event_id": event_id,
    }

    target_url = target.api_url.rstrip("/") + "/" + target_path.lstrip("/")
    logger.info(f"Proxy to: {target_url} for model={target_model}")
    return await _forward_chat(
        target_url, headers, body, is_stream, record_data
    )


@router.api_route("/v1/chat/completions", methods=["GET", "POST"])
async def proxy_chat(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    request_data = json.loads(body) if body else {}
    is_stream = request_data.get("stream", False)
    target_model = request_data.get("model", "default")

    return await _proxy_flow(
        request, db, "chat/completions",
        target_model, is_stream, body,
    )


@router.api_route("/v1/completions", methods=["GET", "POST"])
async def proxy_completions(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    request_data = json.loads(body) if body else {}
    is_stream = request_data.get("stream", False)
    target_model = request_data.get("model", "default")

    return await _proxy_flow(
        request, db, "completions",
        target_model, is_stream, body,
    )


async def _test_upstream_health(target_url: str, headers: dict, model_name: str):
    """Test if upstream API is reachable with a minimal request and log error details."""
    test_session = aiohttp.ClientSession()
    try:
        test_body = json.dumps({"model": "test", "messages": [], "max_tokens": 1}).encode()
        req_headers = {**headers, "Content-Type": "application/json"}
        async with test_session.post(
            target_url,
            data=test_body,
            headers=req_headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp_body = await resp.text()
            logger.warning(
                "[Auto Test] url=%s status=%d model=%s body=%s",
                target_url, resp.status, model_name, resp_body[:500],
            )
            return resp.status, resp_body
    except Exception as e:
        logger.warning("[Auto Test] url=%s model=%s failed: %s", target_url, model_name, type(e).__name__)
    finally:
        try:
            await test_session.close()
        except Exception:
            pass
    return None, "connection failed"


def _get_qa_status(code: int) -> str:
    if 200 <= code < 400:
        return "success"
    return f"error_{code}"


async def _forward_chat(
    target_url: str,
    headers: dict,
    body: bytes,
    is_stream: bool,
    record_data: dict,
):
    """Forward request and return response with retry support."""
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
    )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((aiohttp.ServerTimeoutError, ConnectionError)),
        reraise=True,
    )
    async def _do_request():
        fw_session = aiohttp.ClientSession()
        upstream_resp = await fw_session.post(
            target_url,
            headers=headers,
            data=body,
            timeout=aiohttp.ClientTimeout(total=300),
        )
        return upstream_resp, fw_session

    upstream_resp = None
    fw_session = None

    try:
        upstream_resp, fw_session = await _do_request()
        status_code = upstream_resp.status
        content_type = upstream_resp.headers.get("content-type", "")
        qa_status = _get_qa_status(status_code)

        if status_code >= 400:
            error_body = await upstream_resp.read()
            logger.error(
                "[Upstream Error] model=%s status=%d ct=%s body=%s url=%s",
                record_data.get("target_model", ""),
                status_code, content_type, error_body[:500], target_url,
            )
            logger.warning(
                "[Auto Test] Starting health check url=%s model=%s",
                target_url, record_data.get("target_model", ""),
            )
            model_name = record_data.get("target_model", "")
            asyncio.create_task(
                _test_upstream_health(target_url, headers, model_name)
            )
            resp_body_str = error_body.decode("utf-8", errors="replace")
        else:
            resp_body_str = None
            logger.info(f"Upstream: {status_code}, ct={content_type}, url={target_url}")

        if is_stream:
            async def _collect_and_stream():
                upstream_lines = []
                try:
                    async for line in upstream_resp.content:
                        upstream_lines.append(line)
                        yield line
                except (
                    ClientConnectionError,
                    asyncio.TimeoutError,
                    BrokenPipeError,
                    ConnectionResetError,
                ) as e:
                    logger.info(f"Client disconnected: {type(e).__name__}")
                except OSError as e:
                    logger.info(f"Connection closed: {e}")
                except GeneratorExit:
                    logger.info("Stream generator exited")
                finally:
                    if record_data:
                        resp_body = b"".join(upstream_lines).decode(
                            "utf-8", errors="replace"
                        )
                        try:
                            request_tokens, response_tokens, total_tokens = (
                                _extract_stream_tokens(resp_body)
                            )
                        except Exception:
                            request_tokens = response_tokens = total_tokens = None
                        latency_ms = int(
                            (time.time() - record_data.get("start_time", time.time()))
                            * 1000
                        )
                        try:
                            await sse_bridge.push(
                                "qa_completed",
                                {
                                    "event_id": record_data.get("event_id", ""),
                                    "status": qa_status,
                                    "latency_ms": latency_ms,
                                    "model": record_data.get("target_model", ""),
                                    "user_id": record_data.get("user_id"),
                                    "request_tokens": request_tokens,
                                    "response_tokens": response_tokens,
                                    "total_tokens": total_tokens or 0,
                                    "upstream_status": status_code,
                                },
                            )
                        except Exception:
                            logger.debug("SSE push failed", exc_info=True)

                        asyncio.create_task(
                            _save_qa_record(
                                record_data.get("user_id", 0),
                                record_data.get("api_key_id") or 0,
                                record_data.get("target_model", ""),
                                record_data.get("method", "POST"),
                                record_data.get("request_body", ""),
                                resp_body,
                                status_code,
                                request_tokens or 0,
                                response_tokens or 0,
                                total_tokens or 0,
                                latency_ms,
                                qa_status,
                                record_data.get("client_ip", ""),
                            )
                        )
                    try:
                        if fw_session and not fw_session.closed:
                            await fw_session.close()
                    except Exception:
                        pass
                    try:
                        if upstream_resp and not upstream_resp.closed:
                            await upstream_resp.close()
                    except Exception:
                        pass

            return StreamingResponse(
                _collect_and_stream(),
                status_code=upstream_resp.status,
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            if status_code >= 400 and resp_body_str:
                try:
                    data = json.loads(resp_body_str)
                except (json.JSONDecodeError, TypeError):
                    data = {"error": {"message": resp_body_str[:200], "type": "upstream_error"}}
                request_tokens = response_tokens = total_tokens = None
            else:
                data = await upstream_resp.json() if upstream_resp else {}
                extra_headers = {}
                for h in [
                    "x-request-id",
                    "x-ratelimit-remaining-tokens",
                    "x-ratelimit-limit-tokens",
                ]:
                    if upstream_resp.headers.get(h):
                        extra_headers[h] = upstream_resp.headers[h]

                request_tokens, response_tokens, total_tokens = _extract_tokens(data)

            latency_ms = int(
                (time.time() - record_data.get("start_time", time.time())) * 1000
            )

            bg = BackgroundTasks()
            bg.add_task(_close_aiohttp, upstream_resp, fw_session)

            if record_data:
                try:
                    await sse_bridge.push(
                        "qa_completed",
                        {
                            "event_id": record_data.get("event_id", ""),
                            "status": qa_status,
                            "latency_ms": latency_ms,
                            "model": record_data.get("target_model", ""),
                            "user_id": record_data.get("user_id"),
                            "request_tokens": request_tokens,
                            "response_tokens": response_tokens,
                            "total_tokens": record_data.get("total_tokens", total_tokens or 0),
                            "upstream_status": status_code,
                        },
                    )
                except Exception:
                    logger.debug("SSE push failed", exc_info=True)

                bg.add_task(
                    _save_qa_record,
                    record_data.get("user_id", 0),
                    record_data.get("api_key_id") or 0,
                    record_data.get("target_model", ""),
                    record_data.get("method", "POST"),
                    record_data.get("request_body", ""),
                    json.dumps(data, ensure_ascii=False),
                    status_code,
                    request_tokens or 0,
                    response_tokens or 0,
                    record_data.get("total_tokens", total_tokens or 0),
                    latency_ms,
                    qa_status,
                    record_data.get("client_ip", ""),
                )

            return JSONResponse(
                content=data,
                status_code=status_code,
                headers=extra_headers or None if status_code < 400 else None,
                background=bg,
            )
    except aiohttp.ServerTimeoutError:
        logger.error("Upstream timeout")
        bg = BackgroundTasks()
        if record_data:
            latency_ms = int((time.time() - record_data.get("start_time", time.time())) * 1000)
            bg.add_task(
                _save_qa_record,
                record_data.get("user_id", 0),
                record_data.get("api_key_id") or 0,
                record_data.get("target_model", ""),
                record_data.get("method", "POST"),
                record_data.get("request_body", ""),
                "",
                504,
                0,
                0,
                0,
                latency_ms,
                "timeout",
                record_data.get("client_ip", ""),
            )
        raise HTTPException(status_code=504, detail="Upstream server timeout")
    except Exception as e:
        logger.error("Proxy error: %s", str(e))
        if upstream_resp:
            await _close_aiohttp(upstream_resp, None)
        bg = BackgroundTasks()
        if record_data:
            latency_ms = int((time.time() - record_data.get("start_time", time.time())) * 1000)
            bg.add_task(
                _save_qa_record,
                record_data.get("user_id", 0),
                record_data.get("api_key_id") or 0,
                record_data.get("target_model", ""),
                record_data.get("method", "POST"),
                record_data.get("request_body", ""),
                "",
                0,
                0,
                0,
                0,
                latency_ms,
                "error",
                record_data.get("client_ip", ""),
            )
        raise HTTPException(status_code=502, detail="Upstream server error")


def _make_stream_gen(captured_resp, captured_session):
    async def stream_chunks():
        try:
            async for chunk in captured_resp.content.iter_chunked(8192):
                if chunk:
                    yield chunk
        except (
            ClientConnectionError,
            asyncio.TimeoutError,
            BrokenPipeError,
            ConnectionResetError,
        ) as e:
            logger.info(f"Client disconnected: {type(e).__name__}")
        except OSError as e:
            logger.info(f"Connection closed: {e}")
        except GeneratorExit:
            logger.info("Generator closed")
        finally:
            await _close_aiohttp(captured_resp, captured_session)

    return stream_chunks()


async def _close_aiohttp(resp, session):
    """Cleanup aiohttp resources."""
    try:
        if resp and not resp.closed:
            await resp.close()
    except Exception:
        pass
    try:
        if session and not session.closed:
            await session.close()
    except Exception:
        pass


@router.get("/health")
async def health_check():
    status = {"status": "ok", "timestamp": time.time(), "services": {}}

    try:
        from app.db.session import engine as _db_engine
        if _db_engine:
            async with _db_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            status["services"]["database"] = "healthy"
        else:
            status["status"] = "degraded"
            status["services"]["database"] = "uninitialized"
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["database"] = f"unhealthy: {str(e)}"

    try:
        redis = await get_redis()
        await redis.ping()
        status["services"]["redis"] = "healthy"
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["redis"] = f"unhealthy: {str(e)}"

    return status


@router.get("/v1/models")
async def list_models(request: Request, db: AsyncSession = Depends(get_db)):
    auth_header = request.headers.get("authorization")
    api_key = parse_authorization(auth_header)

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    user, key_obj = await get_user_by_api_key(api_key, db, request)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    models = await _get_user_models_from_cache(user.id, db)

    items = []
    for m in models:
        items.append({
            "id": m.model_name,
            "object": "model",
            "created": int(m.created_at.timestamp()) if m.created_at else int(time.time()),
            "owned_by": "user",
        })

    return {"data": items}
