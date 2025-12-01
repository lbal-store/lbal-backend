from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.wallet import Wallet


class WalletRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_for_user(self, user_id: UUID) -> Wallet:
        wallet = Wallet(user_id=user_id)
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def get_by_user_id(self, user_id: UUID) -> Wallet | None:
        return self.db.query(Wallet).filter(Wallet.user_id == user_id).one_or_none()

    def get_for_update(self, user_id: UUID) -> Wallet | None:
        return (
            self.db.query(Wallet)
            .filter(Wallet.user_id == user_id)
            .with_for_update()
            .one_or_none()
        )

    def save(self, wallet: Wallet) -> Wallet:
        self.db.add(wallet)
        self.db.flush()
        self.db.refresh(wallet)
        return wallet
