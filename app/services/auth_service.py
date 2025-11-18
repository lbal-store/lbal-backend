from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApplicationError, ErrorCode
from app.core.security import (
    InvalidTokenError,
    IssuedToken,
    TokenPayload,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_ttl_seconds,
    verify_password,
)
from app.db.models.session import Session as SessionModel
from app.db.models.user import User, UserRole
from app.db.repositories.session_repository import SessionRepository
from app.db.repositories.user_repository import UserRepository


BLACKLIST_PREFIX = "auth:refresh:blacklist:"


class AuthService:
    def __init__(self, db: Session, redis_client: Redis) -> None:
        self.db = db
        self.redis = redis_client
        self.user_repository = UserRepository(db)
        self.session_repository = SessionRepository(db)
        self.settings = get_settings()

    def login(self, *, email: str, password: str, user_agent: str | None, ip: str | None) -> dict[str, Any]:
        user = self.user_repository.get_by_email(email=email)
        if not user or not verify_password(password, user.password_hash):
            raise ApplicationError(code=ErrorCode.UNAUTHORIZED, message="Invalid email or password.", status_code=401)
        if not user.is_active:
            raise ApplicationError(code=ErrorCode.ACCESS_DENIED, message="User account is disabled.", status_code=403)

        session_id = uuid.uuid4()
        refresh_jti = str(uuid.uuid4())
        session = self.session_repository.create(
            user_id=user.id,
            refresh_jti=refresh_jti,
            user_agent=user_agent,
            ip=ip,
            session_id=session_id,
        )

        refresh_token = create_refresh_token(user_id=str(user.id), session_id=str(session.id), jti=refresh_jti)
        access_token = create_access_token(user_id=str(user.id), role=_role_value(user.role))

        return self._build_token_response(user=user, session=session, access_token=access_token, refresh_token=refresh_token)

    def refresh(self, *, refresh_token: str) -> dict[str, Any]:
        payload = self._decode_refresh_token(refresh_token)
        session = self._validate_session(payload)
        user = self._get_user(payload)

        old_jti = payload.jti
        new_refresh_jti = str(uuid.uuid4())
        session = self.session_repository.update_refresh_jti(session, new_refresh_jti)

        new_refresh = create_refresh_token(user_id=str(user.id), session_id=str(session.id), jti=new_refresh_jti)
        access_token = create_access_token(user_id=str(user.id), role=_role_value(user.role))

        ttl = get_token_ttl_seconds(payload)
        self._blacklist_jti(old_jti, ttl or self._default_refresh_ttl())

        return self._build_token_response(user=user, session=session, access_token=access_token, refresh_token=new_refresh)

    def logout(self, *, refresh_token: str) -> None:
        payload = self._decode_refresh_token(refresh_token)
        session = self._validate_session(payload)
        self.session_repository.revoke(session)
        ttl = get_token_ttl_seconds(payload) or self._default_refresh_ttl()
        self._blacklist_jti(payload.jti, ttl)

    def logout_all(self, *, user_id: UUID) -> None:
        sessions = self.session_repository.revoke_all_active(user_id)
        if not sessions:
            return
        ttl = self._default_refresh_ttl()
        for session in sessions:
            if session.refresh_jti:
                self._blacklist_jti(session.refresh_jti, ttl)

    def _build_token_response(
        self,
        *,
        user: User,
        session: SessionModel,
        access_token: IssuedToken,
        refresh_token: IssuedToken,
    ) -> dict[str, Any]:
        return {
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
            "token_type": "bearer",
            "session_id": str(session.id),
        }

    def _decode_refresh_token(self, token: str) -> TokenPayload:
        try:
            payload = decode_token(token, expected_type=TokenType.REFRESH)
        except InvalidTokenError as exc:
            raise ApplicationError(code=ErrorCode.TOKEN_INVALID, message="Invalid refresh token.", status_code=401) from exc

        if self._is_blacklisted(payload.jti):
            raise ApplicationError(
                code=ErrorCode.TOKEN_REVOKED,
                message="Refresh token is no longer valid.",
                status_code=401,
            )

        return payload

    def _validate_session(self, payload: TokenPayload) -> SessionModel:
        if not payload.session_id:
            raise ApplicationError(code=ErrorCode.TOKEN_INVALID, message="Refresh token missing session.", status_code=401)
        try:
            session_id = UUID(payload.session_id)
        except ValueError as exc:
            raise ApplicationError(code=ErrorCode.TOKEN_INVALID, message="Invalid session identifier.", status_code=401) from exc

        session = self.session_repository.get_by_id(session_id)
        if not session:
            raise ApplicationError(code=ErrorCode.TOKEN_INVALID, message="Session not found.", status_code=401)
        if session.revoked_at is not None:
            raise ApplicationError(code=ErrorCode.TOKEN_REVOKED, message="Session revoked.", status_code=401)
        if session.refresh_jti != payload.jti:
            raise ApplicationError(
                code=ErrorCode.TOKEN_REVOKED,
                message="Refresh token is no longer valid.",
                status_code=401,
            )

        if str(session.user_id) != payload.sub:
            raise ApplicationError(code=ErrorCode.TOKEN_INVALID, message="Session/user mismatch.", status_code=401)

        return session

    def _get_user(self, payload: TokenPayload) -> User:
        try:
            user_id = UUID(payload.sub)
        except ValueError as exc:
            raise ApplicationError(code=ErrorCode.TOKEN_INVALID, message="Invalid user identifier.", status_code=401) from exc

        user = self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise ApplicationError(code=ErrorCode.UNAUTHORIZED, message="User not available.", status_code=401)
        return user

    def _blacklist_jti(self, jti: str, ttl_seconds: int) -> None:
        ttl = max(ttl_seconds, 1)
        self.redis.setex(f"{BLACKLIST_PREFIX}{jti}", ttl, "1")

    def _is_blacklisted(self, jti: str) -> bool:
        return bool(self.redis.get(f"{BLACKLIST_PREFIX}{jti}"))

    def _default_refresh_ttl(self) -> int:
        return int(self.settings.refresh_token_expire_minutes) * 60


def _role_value(role: UserRole | str) -> str:
    if isinstance(role, UserRole):
        return role.value
    return str(role)
