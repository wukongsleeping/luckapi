from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    display_name: str = Field("", max_length=100)
    password: str = Field(..., min_length=6)
    role: str = Field("user", pattern="^(user|admin)$")
    initial_balance: int = Field(0, ge=0)
    allowed_ips: Optional[str] = Field(None, max_length=2000)


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = Field(None, pattern="^(user|admin)$")
    status: Optional[str] = Field(None, pattern="^(active|banned|disabled)$")
    initial_balance: Optional[int] = Field(None, ge=0)
    allowed_ips: Optional[str] = Field(None, max_length=2000)


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    status: str
    balance: int
    total_usage: int
    allowed_ips: Optional[str] = None
    group_ids: List[int] = []
    group_names: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserOut]


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
