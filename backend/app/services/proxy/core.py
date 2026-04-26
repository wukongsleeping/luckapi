"""代理服务核心转发模块。

包含核心代理路由逻辑、上游请求转发、响应处理等。
"""

import json
import logging
import time
from typing import Optional

import aiohttp
from aiohttp import ClientConnectionError
from app.core.model_status import track_request_end, track_request_start
from app.notification import sse_bridge
from app.services.proxy.auth import (
    _get_global_model_url,
    save_qa_record,
    update_user_quota_and_check,
)
from app.services.proxy.concurrency_limiter import get_global_concurrency_limiter
from app.services.proxy.utils import (
    extract_stream_tokens,
    extract_tokens,
    get_client_ip,
    get_qa_status,
    parse_authorization,
)
from fastapi import HTTPException
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def proxy_flow(
    request,
    db: AsyncSession,
    target_path: str,
    target_model: str,
    is_stream: bool,
    body: bytes,
    response_json: bool = False,
):
    """共享代理逻辑：认证、路由、构建上游请求、返回响应。

    Args:
        request: FastAPI Request 对象
        db: 数据库会话
        target_path: 目标路径（如 "chat/completions"）
        target_model: 目标模型名称
        is_stream: 是否流式响应
        body: 请求体字节数据
        response_json: 是否返回 JSON 响应

    Returns:
        FastAPI Response 对象
    """
    auth_header_raw = request.headers.get("authorization")
    if not auth_header_raw:
        raise HTTPException(
            status_code=401,
            detail="缺少 API Key，请在请求头中添加 Authorization: Bearer <your_api_key>",
        )
    api_key = parse_authorization(auth_header_raw)

    # 获取认证信息
    from app.services.proxy.auth import get_user_by_api_key

    auth_user, auth_key_obj = await get_user_by_api_key(api_key, db, request)
    if not auth_user:
        raise HTTPException(status_code=401, detail="API Key 无效或已被停用，请联系管理员")

    # 获取用户模型列表
    from app.services.proxy.auth import get_user_models_from_cache

    models = await get_user_models_from_cache(auth_user.id, db)
    if not models:
        raise HTTPException(status_code=403, detail="No models bound to this account")

    # 匹配目标模型
    target = None
    # 优先按访问名称匹配
    for m in models:
        if hasattr(m, "access_name") and m.access_name and m.access_name == target_model:
            target = m
            break
    # 再按模型名称精确匹配
    if not target:
        for m in models:
            if m.model_name == target_model:
                target = m
                break
    # 按 ID 匹配
    if not target and target_model.isdigit():
        for m in models:
            if m.id == int(target_model):
                target = m
                break
    # 找不到目标时，默认使用第一个模型
    if not target:
        target = models[0]

    # 构建上游请求头
    headers = {
        "Authorization": f"Bearer {target.api_key}",
        "Content-Type": "application/json",
    }

    for header in ["user-agent", "accept", "accept-encoding"]:
        if request.headers.get(header):
            headers[header] = request.headers[header]

    # 生成事件 ID 并记录开始时间
    from app.services.proxy.auth import push_qa_started
    from app.services.proxy.utils import gen_event_id

    event_id = gen_event_id()
    start_time = time.time()

    await push_qa_started(request, auth_user.id, target_model, event_id, start_time)

    request_body_str = body.decode("utf-8", errors="replace")

    record_data = {
        "user_id": auth_user.id,
        "api_key_id": auth_key_obj.id if auth_key_obj else None,
        "target_model": target_model,
        "method": "POST",
        "request_body": request_body_str,
        "start_time": start_time,
        "client_ip": get_client_ip(request),
        "event_id": event_id,
    }

    target_url = target.api_url.rstrip("/") + "/" + target_path.lstrip("/")
    logger.info("Proxy to: %s for model=%s", target_url, target_model)
    return await forward_chat(db, target_url, headers, body, is_stream, record_data)


async def forward_chat(
    db: AsyncSession,
    target_url: str,
    headers: dict,
    body: bytes,
    is_stream: bool,
    record_data: dict,
):
    """Forward request and return response with retry support.

    核心转发函数，处理：
    1. 上游并发限流（信号量控制）
    2. 上游请求发送
    3. 重试逻辑
    4. 流式/非流式响应分派
    5. Token 提取与 QA 记录
    6. 错误处理与资源清理

    Args:
        db: 数据库会话
        target_url: 上游 API 地址
        headers: 请求头（含上游 API Key）
        body: 请求体
        is_stream: 是否流式
        record_data: QA 记录数据

    Returns:
        FastAPI Response 对象
    """
    target_url_stripped = target_url.rstrip("/")
    # 追踪：如果匹配全局模型，使用全局模型的 api_url 作为追踪 key
    tracked_url = await _get_global_model_url(target_url_stripped, db)
    if tracked_url:
        target_url_stripped_for_tracking = tracked_url
        await track_request_start(tracked_url)
    else:
        target_url_stripped_for_tracking = target_url_stripped
        await track_request_start(target_url_stripped)

    # 并发限流：尝试获取上游模型的信号量
    limiter = get_global_concurrency_limiter()
    sem = None
    try:
        sem, acquired = await limiter.acquire(
            target_url_stripped_for_tracking,
            key=record_data.get("target_model"),
        )
        if not acquired:
            logger.warning(
                "[Concurrency] Request rejected for model=%s (queue full/timeout)",
                target_url_stripped_for_tracking,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "上游模型繁忙，请稍后重试。"},
            )
        return await _do_chat_request(
            db,
            target_url,
            headers,
            body,
            is_stream,
            record_data,
            target_url_stripped_for_tracking,
        )
    except Exception as e:
        logger.error("[Concurrency] Limiter error: %s", e, exc_info=True)
        logger.error("Proxy error: %s", str(e))
        return await handle_error_case(
            None, None, target_url_stripped_for_tracking, record_data, 0, "error"
        )
    finally:
        # 释放信号量（确保不阻塞）
        if sem:
            limiter.release(sem, target_url_stripped_for_tracking)


async def _do_chat_request(
    db: AsyncSession,
    target_url: str,
    headers: dict,
    body: bytes,
    is_stream: bool,
    record_data: dict,
    target_url_stripped_for_tracking: str,
):
    """执行实际的代理请求。"""
    _current_session = None

    async def _do_request():
        nonlocal _current_session
        session = aiohttp.ClientSession()
        try:
            resp = await session.post(
                target_url,
                headers=headers,
                data=body,
                timeout=aiohttp.ClientTimeout(total=300),
            )
            if _current_session and not _current_session.closed:
                await _close_aiohttp(None, _current_session)
            _current_session = session
            return resp, session
        except Exception:
            await _close_aiohttp(None, session)
            raise

    upstream_resp = None
    fw_session = None

    try:
        upstream_resp, fw_session = await _do_request()
        status_code = upstream_resp.status
        content_type = upstream_resp.headers.get("content-type", "")
        qa_status = get_qa_status(status_code)

        if status_code >= 400:
            error_body = await upstream_resp.read()
            logger.error(
                "[Upstream Error] model=%s status=%d ct=%s body=%s url=%s",
                record_data.get("target_model", ""),
                status_code,
                content_type,
                error_body[:500],
                target_url,
            )
            logger.warning(
                "[Auto Test] Starting health check url=%s model=%s",
                target_url,
                record_data.get("target_model", ""),
            )
            model_name = record_data.get("target_model", "")
            asyncio.create_task(test_upstream_health(target_url, headers, model_name))
            resp_body_str = error_body.decode("utf-8", errors="replace")
        else:
            resp_body_str = None
            logger.info("Upstream: %d, ct=%s, url=%s", status_code, content_type, target_url)

        if is_stream:
            latency_ms = int((time.time() - record_data.get("start_time", time.time())) * 1000)

            async def _collect_and_stream():
                upstream_lines = []
                _cleanup_done = False
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
                    logger.info("Client disconnected: %s", type(e).__name__)
                except OSError as e:
                    logger.info("Connection closed: %s", e)
                except GeneratorExit:
                    logger.info("Stream generator exited")
                finally:
                    if not _cleanup_done:
                        _cleanup_done = True
                        if record_data:
                            resp_body = b"".join(upstream_lines).decode("utf-8", errors="replace")
                            try:
                                request_tokens, response_tokens, total_tokens = (
                                    extract_stream_tokens(resp_body)
                                )
                            except Exception:
                                request_tokens = response_tokens = total_tokens = None
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

                            await save_qa_record(
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

                            try:
                                if target_url_stripped_for_tracking:
                                    await track_request_end(
                                        target_url_stripped_for_tracking,
                                        latency_ms,
                                        status_code < 400,
                                    )
                            except Exception:
                                pass

                            await update_user_quota_and_check(
                                db,
                                record_data.get("user_id", 0),
                                request_tokens or 0,
                                response_tokens or 0,
                            )
                        await _close_aiohttp(upstream_resp, fw_session)

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
            return await handle_non_stream_response(
                upstream_resp,
                fw_session,
                target_url_stripped_for_tracking,
                is_stream,
                record_data,
                status_code,
                qa_status,
                content_type,
                resp_body_str,
                headers,
                body,
            )
    except aiohttp.ServerTimeoutError:
        logger.error("Upstream timeout")
        return await handle_error_case(
            upstream_resp, fw_session, target_url_stripped_for_tracking, record_data, 504, "timeout"
        )
    except Exception as e:
        logger.error("Proxy error: %s", str(e))
        return await handle_error_case(
            upstream_resp, fw_session, target_url_stripped_for_tracking, record_data, 0, "error"
        )


async def handle_non_stream_response(
    upstream_resp,
    fw_session,
    target_url_stripped_for_tracking,
    is_stream: bool,
    record_data: dict,
    status_code: int,
    qa_status: str,
    content_type: str,
    resp_body_str: Optional[str],
    headers: dict,
    body: bytes,
):
    """处理非流式响应：统一提取数据、延迟、token 并构建 BackgroundTasks。"""
    extra_headers = {}
    if status_code >= 400 and resp_body_str:
        try:
            data = json.loads(resp_body_str)
        except (json.JSONDecodeError, TypeError):
            data = {"error": {"message": resp_body_str[:200], "type": "upstream_error"}}
        request_tokens = response_tokens = total_tokens = None
    else:
        if upstream_resp:
            for h in [
                "x-request-id",
                "x-ratelimit-remaining-tokens",
                "x-ratelimit-limit-tokens",
            ]:
                v = upstream_resp.headers.get(h)
                if v:
                    extra_headers[h] = v
            data = await upstream_resp.json() if upstream_resp else {}
            request_tokens, response_tokens, total_tokens = extract_tokens(data)
        else:
            data = {}
            request_tokens = response_tokens = total_tokens = None

    latency_ms = int((time.time() - record_data.get("start_time", time.time())) * 1000)

    bg = BackgroundTasks()
    bg.add_task(_close_aiohttp, upstream_resp, fw_session)
    bg.add_task(
        track_request_end,
        target_url_stripped_for_tracking,
        latency_ms,
        status_code < 400,
    )

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

        try:
            bg.add_task(
                save_qa_record,
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
        except Exception:
            logger.debug("QA record task add failed", exc_info=True)

    resp_headers = extra_headers if extra_headers else {}
    return JSONResponse(
        content=data,
        status_code=status_code,
        headers=resp_headers,
        background=bg,
    )


async def handle_error_case(
    upstream_resp,
    fw_session,
    target_url_stripped_for_tracking,
    record_data: dict,
    http_code: int,
    error_type: str,
):
    """统一错误处理：清理资源、追踪结束、保存 QA 记录。"""
    bg = BackgroundTasks()
    cleanup_resp = upstream_resp if upstream_resp else None
    bg.add_task(_close_aiohttp, cleanup_resp, fw_session)

    if record_data:
        latency_ms = int((time.time() - record_data.get("start_time", time.time())) * 1000)
        bg.add_task(
            track_request_end,
            target_url_stripped_for_tracking,
            latency_ms,
            False,
        )
        bg.add_task(
            save_qa_record,
            record_data.get("user_id", 0),
            record_data.get("api_key_id") or 0,
            record_data.get("target_model", ""),
            record_data.get("method", "POST"),
            record_data.get("request_body", ""),
            "",
            http_code,
            0,
            0,
            0,
            latency_ms,
            error_type,
            record_data.get("client_ip", ""),
        )

    if error_type == "error":
        raise HTTPException(status_code=502, detail="上游服务发生错误，请稍后重试")
    # timeout: return 504 via background tasks only
    return JSONResponse(
        content={"error": {"message": "上游服务超时", "type": "upstream_timeout"}},
        status_code=504,
        background=bg,
    )


async def test_upstream_health(target_url: str, headers: dict, model_name: str):
    """Test if upstream API is reachable with a minimal request and log error details."""
    import aiohttp

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
                target_url,
                resp.status,
                model_name,
                resp_body[:500],
            )
            return resp.status, resp_body
    except Exception as e:
        logger.warning(
            "[Auto Test] url=%s model=%s failed: %s", target_url, model_name, type(e).__name__
        )
    finally:
        try:
            await test_session.close()
        except Exception:
            pass
    return None, "connection failed"


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
