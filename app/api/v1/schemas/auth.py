from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    all: bool = False


class AuthUser(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str
    avatar_url: str | None = None
    is_active: bool


class TokenBundle(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SignupResponse(TokenBundle):
    user: AuthUser


class LoginResponse(SignupResponse):
    session_id: UUID
