from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import json as json_lib
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import QaRecord, User
from app.schemas.qa import QaRecordOut, QaRecordList
from app.api.auth import admin_required

router = APIRouter()


@router.get("/qa-records", response_model=QaRecordList)
async def list_qa_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Query(None),
    status: str = Query(None),
    model: str = Query(""),
    date_from: str = Query(""),
    date_to: str = Query(""),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    conditions = []

    if user_id:
        conditions.append(QaRecord.user_id == user_id)
    if status:
        conditions.append(QaRecord.status == status)
    if model:
        escaped = model.replace("%", "\\%").replace("_", "\\_")
        conditions.append(QaRecord.target_model.ilike(f"%{escaped}%", escape="\\"))
    if date_from:
        conditions.append(QaRecord.created_at >= date_from)
    if date_to:
        conditions.append(QaRecord.created_at <= date_to)

    filter_clause = (*conditions,)
    if filter_clause:
        count_query = select(func.count(QaRecord.id)).where(*filter_clause)
    else:
        count_query = select(func.count(QaRecord.id))

    result = await db.execute(count_query)
    total = result.scalar() or 0

    if filter_clause:
        items_query = (
            select(QaRecord)
            .where(*filter_clause)
            .order_by(QaRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    else:
        items_query = (
            select(QaRecord)
            .order_by(QaRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

    result = await db.execute(items_query)
    items = result.scalars().all()

    return QaRecordList(total=total, page=page, page_size=page_size, items=items)


@router.get("/qa-records/{record_id}", response_model=QaRecordOut)
async def get_qa_record(
    record_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QaRecord).where(QaRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")
    return record


@router.delete("/qa-records/{record_id}", status_code=204)
async def delete_qa_record(
    record_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QaRecord).where(QaRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")
    await db.delete(record)
    await db.commit()


@router.get("/qa-records/export")
async def export_qa_records(
    user_id: int = Query(None),
    status: str = Query(None),
    model: str = Query(""),
    date_from: str = Query(""),
    date_to: str = Query(""),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    conditions = []

    if user_id:
        conditions.append(QaRecord.user_id == user_id)
    if status:
        conditions.append(QaRecord.status == status)
    if model:
        escaped = model.replace("%", "\\%").replace("_", "\\_")
        conditions.append(QaRecord.target_model.ilike(f"%{escaped}%", escape="\\"))
    if date_from:
        conditions.append(QaRecord.created_at >= date_from)
    if date_to:
        conditions.append(QaRecord.created_at <= date_to)

    filter_clause = (*conditions,)
    if not filter_clause:
        items_query = select(QaRecord).order_by(QaRecord.created_at.desc())
    else:
        items_query = (
            select(QaRecord).where(*filter_clause).order_by(QaRecord.created_at.desc())
        )

    result = await db.execute(items_query)
    records = result.scalars().all()

    # Batch query all users for export (fix N+1)
    user_ids = {r.user_id for r in records if r.user_id}
    user_map: dict[int, User] = {}
    if user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in user_result.scalars().all():
            user_map[u.id] = u

    # Build JSONL export with OpenAI fine-tuning format
    lines = []
    for r in records:
        line = {
            "metadata": {
                "source": "luckapi",
                "record_id": r.id,
                "user_id": r.user_id,
                "api_key_id": r.api_key_id,
                "model": r.target_model,
                "latency_ms": r.latency_ms,
                "status": r.status,
                "upstream_status": r.upstream_status,
                "request_tokens": r.request_tokens,
                "response_tokens": r.response_tokens,
                "total_tokens": r.total_tokens,
                "client_ip": r.client_ip,
            },
            "record": {
                "user_id": r.user_id,
                "model": r.target_model,
                "method": r.method,
                "request": r.request_body,
                "response": r.response_body,
                "status": r.status,
                "upstream_status": r.upstream_status,
                "tokens": {
                    "prompt": r.request_tokens,
                    "completion": r.response_tokens,
                    "total": r.total_tokens,
                },
            },
        }
        _user = user_map.get(r.user_id)
        if _user:
            line["record"]["username"] = _user.username
        # Attach messages from request for direct fine-tuning use
        try:
            req_data = (
                json_lib.loads(r.request_body)
                if isinstance(r.request_body, str)
                else r.request_body
            )
            if "messages" in req_data:
                line["messages"] = req_data["messages"]
        except (json_lib.JSONDecodeError, TypeError):
            pass

        lines.append(json_lib.dumps(line, ensure_ascii=False))

    content = "\n".join(lines)

    return StreamingResponse(
        iter([content]),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f"attachment; filename=qa-records-{len(lines)}.jsonl",
        },
    )
