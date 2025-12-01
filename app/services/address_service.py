from __future__ import annotations

from typing import Sequence
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from app.api.v1.schemas.address import AddressCreateRequest, AddressUpdateRequest
from app.core.errors import ApplicationError
from app.db.models.address import Address
from app.db.repositories.address_repository import AddressRepository
from app.db.repositories.user_repository import UserRepository


class AddressService:
    def __init__(
        self,
        db: Session,
        address_repo: AddressRepository,
        user_repo: UserRepository | None = None,
    ) -> None:
        self.db = db
        self.address_repo = address_repo
        self.user_repo = user_repo

    def list_addresses(self, user_id: UUID) -> Sequence[Address]:
        return self.address_repo.list_for_user(user_id)

    def create_address(self, user_id: UUID, payload: AddressCreateRequest) -> Address:
        data = payload.dict(exclude_unset=True)
        requested_default = data.get("is_default")

        if requested_default:
            self.address_repo.clear_default_for_user(user_id)
            data["is_default"] = True
        else:
            existing_addresses = self.address_repo.list_for_user(user_id)
            if not existing_addresses:
                data["is_default"] = True
            else:
                data.setdefault("is_default", False)

        return self.address_repo.create_for_user(user_id, **data)

    def update_address(self, user_id: UUID, address_id: UUID, payload: AddressUpdateRequest) -> Address:
        address = self.address_repo.get_by_id_and_user(address_id, user_id)
        if not address:
            raise ApplicationError(
                code="NOT_FOUND",
                message="Address not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        data = payload.dict(exclude_unset=True)
        if data.get("is_default"):
            self.address_repo.clear_default_for_user(user_id)
            data["is_default"] = True

        return self.address_repo.update(address, **data)

    def delete_address(self, user_id: UUID, address_id: UUID) -> None:
        address = self.address_repo.get_by_id_and_user(address_id, user_id)
        if not address:
            raise ApplicationError(
                code="NOT_FOUND",
                message="Address not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        self.address_repo.delete(address)
