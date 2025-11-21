from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.email_verification import EmailVerification


class EmailVerificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: UUID, code: str, expires_at: datetime) -> EmailVerification:
        verification = EmailVerification(user_id=user_id, code=code, expires_at=expires_at)
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        return verification

    def get_valid_code(self, *, user_id: UUID, code: str, now: datetime) -> EmailVerification | None:
        return (
            self.db.query(EmailVerification)
            .filter(
                EmailVerification.user_id == user_id,
                EmailVerification.code == code,
                EmailVerification.expires_at > now,
            )
            .order_by(EmailVerification.created_at.desc())
            .first()
        )

    def delete_for_user(self, *, user_id: UUID) -> None:
        self.db.query(EmailVerification).filter(EmailVerification.user_id == user_id).delete()
        self.db.commit()
