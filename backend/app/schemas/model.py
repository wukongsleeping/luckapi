from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserModelCreate(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=100)
    api_url: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)


class UserModelOut(BaseModel):
    id: int
    user_id: int
    model_name: str
    api_url: str
    api_key: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserModelList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserModelOut]


class ApiKeyOut(BaseModel):
    id: int
    user_id: int
    key: str
    name: str
    status: str
    last_used_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
