from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class TokenPayload:
    sub: str
    jti: str
    token_type: TokenType
    role: str | None = None
    session_id: str | None = None
    exp: int | None = None
    iat: int | None = None


@dataclass
class IssuedToken:
    token: str
    expires_at: datetime
    jti: str


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be decoded or validated."""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    return pwd_context.hash(password)


def create_access_token(
    *,
    user_id: str,
    role: str,
    expires_delta: timedelta | None = None,
    jti: str | None = None,
) -> IssuedToken:
    settings = get_settings()
    return _issue_token(
        claims={"sub": str(user_id), "role": role, "token_type": TokenType.ACCESS.value, "jti": jti},
        expires_delta=expires_delta or timedelta(minutes=settings.access_token_expire_minutes),
        algorithm=settings.jwt_algorithm,
        secret=settings.secret_key,
    )


def create_refresh_token(
    *,
    user_id: str,
    session_id: str,
    expires_delta: timedelta | None = None,
    jti: str | None = None,
) -> IssuedToken:
    settings = get_settings()
    return _issue_token(
        claims={"sub": str(user_id), "session_id": str(session_id), "token_type": TokenType.REFRESH.value, "jti": jti},
        expires_delta=expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes),
        algorithm=settings.jwt_algorithm,
        secret=settings.secret_key,
    )


def _issue_token(*, claims: dict[str, Any], expires_delta: timedelta, algorithm: str, secret: str) -> IssuedToken:
    now = datetime.now(timezone.utc)
    payload = claims.copy()
    payload["jti"] = payload.get("jti") or str(uuid.uuid4())
    payload["iat"] = int(now.timestamp())
    expires_at = now + expires_delta
    payload["exp"] = int(expires_at.timestamp())
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return IssuedToken(token=token, expires_at=expires_at, jti=payload["jti"])


def decode_token(token: str, expected_type: TokenType | None = None) -> TokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:  # pragma: no cover - defensive branch
        raise InvalidTokenError("Could not decode token") from exc

    token_type = payload.get("token_type")
    if token_type is None:
        raise InvalidTokenError("token_type claim missing")

    try:
        parsed_token_type = TokenType(token_type)
    except ValueError as exc:
        raise InvalidTokenError("Unknown token_type") from exc

    if expected_type and parsed_token_type is not expected_type:
        raise InvalidTokenError("Unexpected token type")

    if "sub" not in payload or "jti" not in payload:
        raise InvalidTokenError("Token missing required claims")

    return TokenPayload(
        sub=str(payload["sub"]),
        jti=str(payload["jti"]),
        token_type=parsed_token_type,
        role=payload.get("role"),
        session_id=payload.get("session_id"),
        exp=int(payload["exp"]) if payload.get("exp") is not None else None,
        iat=int(payload["iat"]) if payload.get("iat") is not None else None,
    )


def get_token_ttl_seconds(payload: TokenPayload) -> int:
    if payload.exp is None:
        return 0
    now_ts = int(datetime.now(timezone.utc).timestamp())
    return max(int(payload.exp) - now_ts, 0)
