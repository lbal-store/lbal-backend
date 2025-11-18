from __future__ import annotations
from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError, ErrorCode
from app.core.rate_limit import listing_create_rate_limiter, login_rate_limiter, media_presign_rate_limiter
from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.auth_service import AuthService
from app.utils.redis_client import get_redis_client


async def get_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    redis_client = get_redis_client()
    return AuthService(db, redis_client)


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token, expected_type=TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    try:
        user_id = UUID(payload.sub)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identifier") from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing")

    return user


def enforce_login_rate_limit(request: Request) -> None:
    identifier = request.client.host if request.client else "unknown"
    if not login_rate_limiter.allow(identifier):
        raise ApplicationError(
            code=ErrorCode.RATE_LIMITED,
            message="Too many login attempts. Try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


def enforce_media_presign_rate_limit(current_user: User = Depends(get_current_user)) -> User:
    if not media_presign_rate_limiter.allow(str(current_user.id)):
        raise ApplicationError(
            code=ErrorCode.RATE_LIMITED,
            message="Upload limit reached. Try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return current_user


def enforce_listing_create_rate_limit(current_user: User = Depends(get_current_user)) -> User:
    if not listing_create_rate_limiter.allow(str(current_user.id)):
        raise ApplicationError(
            code=ErrorCode.RATE_LIMITED,
            message="Listing creation limit reached. Try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return current_user
