from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.db.models.user import UserRole


class UserMeResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    avatar_url: Optional[str] = Field(default=None, max_length=512)
    role: UserRole
    language: Optional[str] = Field(default=None, max_length=10)
    is_active: bool

    class Config:
        orm_mode = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[str] = None

    class Config:
        orm_mode = True
