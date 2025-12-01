from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.db.models.user import UserRole


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    avatar_url: Optional[str] = Field(default=None, max_length=512)
    role: UserRole
    language: Optional[str] = Field(default=None, max_length=10)
    is_active: bool
    has_unread_notifications: bool


class UserPublicProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    avatar_url: Optional[str] = Field(default=None, max_length=512)
    language: Optional[str] = Field(default=None, max_length=10)
    is_active: bool


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[str] = None
