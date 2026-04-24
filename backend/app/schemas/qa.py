from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class QaRecordOut(BaseModel):
    id: int
    user_id: int
    target_model: str
    method: str
    request_body: str
    response_body: Optional[str] = None
    upstream_status: Optional[int] = None
    request_tokens: Optional[int] = None
    response_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: int
    status: str
    client_ip: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QaRecordList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[QaRecordOut]
