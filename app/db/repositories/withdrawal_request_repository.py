from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.withdrawal_request import WithdrawalRequest


class WithdrawalRequestRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        amount,
        destination: str,
        status,
        idempotency_key: str | None = None,
    ) -> WithdrawalRequest:
        request = WithdrawalRequest(
            user_id=user_id,
            amount=amount,
            destination=destination,
            status=status,
            idempotency_key=idempotency_key,
        )
        self.db.add(request)
        self.db.flush()
        self.db.refresh(request)
        return request

    def get_by_idempotency_key(self, key: str) -> WithdrawalRequest | None:
        if not key:
            return None
        return self.db.query(WithdrawalRequest).filter(WithdrawalRequest.idempotency_key == key).one_or_none()
