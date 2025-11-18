from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    session_id: UUID
