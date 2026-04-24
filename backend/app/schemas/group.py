from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, max_length=100)
    model_url: Optional[str] = Field(None, max_length=500)
    model_api_key: Optional[str] = Field(None)


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    model_name: Optional[str] = Field(None, max_length=100)
    model_url: Optional[str] = Field(None, max_length=500)
    model_api_key: Optional[str] = None


class GroupOut(BaseModel):
    id: int
    name: str
    model_name: Optional[str] = None
    model_url: Optional[str] = None
    model_api_key: Optional[str] = None
    status: str
    member_ids: List[int] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupList(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[GroupOut]


class GroupAssignUser(BaseModel):
    user_id: int
