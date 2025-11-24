from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1)


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
    has_unread_notifications: bool


class TokenBundle(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthPayload(TokenBundle):
    user: AuthUser


class SignupResponse(BaseModel):
    message: str = "Verification code sent"


class LoginResponse(AuthPayload):
    session_id: UUID


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str
