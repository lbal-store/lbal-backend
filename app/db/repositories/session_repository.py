from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.session import Session as SessionModel


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: UUID,
        refresh_jti: str,
        user_agent: str | None,
        ip: str | None,
        *,
        session_id: UUID | None = None,
    ) -> SessionModel:
        session = SessionModel(
            id=session_id or uuid.uuid4(),
            user_id=user_id,
            refresh_jti=refresh_jti,
            user_agent=user_agent,
            ip=ip,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_id(self, session_id: UUID) -> SessionModel | None:
        return self.db.get(SessionModel, session_id)

    def update_refresh_jti(self, session: SessionModel, new_refresh_jti: str) -> SessionModel:
        session.refresh_jti = new_refresh_jti
        session.revoked_at = None
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def revoke(self, session: SessionModel) -> SessionModel:
        session.revoked_at = datetime.now(timezone.utc)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def revoke_all_active(self, user_id: UUID) -> Sequence[SessionModel]:
        stmt = select(SessionModel).where(SessionModel.user_id == user_id, SessionModel.revoked_at.is_(None))
        sessions = list(self.db.execute(stmt).scalars().all())
        now = datetime.now(timezone.utc)
        for session in sessions:
            session.revoked_at = now
            self.db.add(session)
        if sessions:
            self.db.commit()
            for session in sessions:
                self.db.refresh(session)
        return sessions
