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
    get_password_hash,
    get_token_ttl_seconds,
    verify_password,
)
from app.db.models.session import Session as SessionModel
from app.db.models.user import User, UserRole
from app.db.repositories.session_repository import SessionRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.wallet_repository import WalletRepository


BLACKLIST_PREFIX = "auth:refresh:blacklist:"


class AuthService:
    def __init__(self, db: Session, redis_client: Redis) -> None:
        self.db = db
        self.redis = redis_client
        self.user_repository = UserRepository(db)
        self.session_repository = SessionRepository(db)
        self.wallet_repository = WalletRepository(db)
        self.settings = get_settings()

    def signup(self, *, name: str, email: str, password: str, user_agent: str | None, ip: str | None) -> dict[str, Any]:
        if self.user_repository.get_by_email(email=email):
            raise ApplicationError(
                code=ErrorCode.CONFLICT,
                message="Email already in use.",
                status_code=409,
            )

        try:
            password_hash = get_password_hash(password)
        except ValueError as exc:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message=str(exc),
                status_code=400,
            ) from exc

        user = self.user_repository.create(name=name, email=email, password_hash=password_hash)
        self.wallet_repository.create_for_user(user.id)

        return self._issue_tokens(user=user, user_agent=user_agent, ip=ip, include_session_id=False)

    def login(self, *, email: str, password: str, user_agent: str | None, ip: str | None) -> dict[str, Any]:
        user = self.user_repository.get_by_email(email=email)
        if not user or not verify_password(password, user.password_hash):
            raise ApplicationError(code=ErrorCode.UNAUTHORIZED, message="Invalid email or password.", status_code=401)
        if not user.is_active:
            raise ApplicationError(code=ErrorCode.ACCESS_DENIED, message="User account is disabled.", status_code=403)

        return self._issue_tokens(user=user, user_agent=user_agent, ip=ip, include_session_id=True)

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

        return self._build_auth_payload(
            user=user,
            session=session,
            access_token=access_token,
            refresh_token=new_refresh,
            include_session_id=True,
        )

    def logout(self, *, refresh_token: str, all_sessions: bool) -> None:
        payload = self._decode_refresh_token(refresh_token)
        session = self._validate_session(payload)
        user = self._get_user(payload)

        if all_sessions:
            self.logout_all(user_id=user.id)
        else:
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

    def _issue_tokens(self, *, user: User, user_agent: str | None, ip: str | None, include_session_id: bool) -> dict[str, Any]:
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

        return self._build_auth_payload(
            user=user,
            session=session,
            access_token=access_token,
            refresh_token=refresh_token,
            include_session_id=include_session_id,
        )

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

    def _serialize_user(self, user: User) -> dict[str, Any]:
        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": _role_value(user.role),
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
        }

    def _build_auth_payload(
        self,
        *,
        user: User,
        session: SessionModel,
        access_token: IssuedToken,
        refresh_token: IssuedToken,
        include_session_id: bool,
    ) -> dict[str, Any]:
        payload = {
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
            "token_type": "bearer",
            "user": self._serialize_user(user),
        }

        if include_session_id:
            payload["session_id"] = str(session.id)

        return payload


def _role_value(role: UserRole | str) -> str:
    if isinstance(role, UserRole):
        return role.value
    return str(role)
