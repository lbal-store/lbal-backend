from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.address import Address


class AddressRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_for_user(self, user_id: UUID, **address_fields: object) -> Address:
        address = Address(user_id=user_id, **address_fields)
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    def list_for_user(self, user_id: UUID) -> Sequence[Address]:
        query = (
            self.db.query(Address)
            .filter(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        return query.all()

    def get_by_id_and_user(self, address_id: UUID, user_id: UUID) -> Address | None:
        return (
            self.db.query(Address)
            .filter(Address.id == address_id, Address.user_id == user_id)
            .one_or_none()
        )

    def update(self, address: Address, **fields: object) -> Address:
        for key, value in fields.items():
            if value is not None:
                setattr(address, key, value)
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    def delete(self, address: Address) -> None:
        self.db.delete(address)
        self.db.commit()

    def clear_default_for_user(self, user_id: UUID) -> None:
        (
            self.db.query(Address)
            .filter(Address.user_id == user_id, Address.is_default.is_(True))
            .update({Address.is_default: False})
        )
        self.db.commit()
