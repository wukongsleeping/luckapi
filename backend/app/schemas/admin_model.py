from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class GlobalModelCreate(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=100)
    api_url: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    status: str = "active"


class GlobalModelUpdate(BaseModel):
    model_name: Optional[str] = Field(None, max_length=100)
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    status: Optional[str] = None


class GlobalModelOut(BaseModel):
    id: int
    model_name: str
    api_url: str
    api_key: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GlobalModelList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[GlobalModelOut]
