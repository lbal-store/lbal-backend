from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1 import deps
from app.api.v1.schemas.address import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
)
from app.db.models.user import User
from app.db.repositories.address_repository import AddressRepository
from app.services.address_service import AddressService


router = APIRouter(prefix="/users/me/addresses", tags=["addresses"])


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    payload: AddressCreateRequest,
    current_user: User = Depends(deps.get_current_user),
    address_service: AddressService = Depends(deps.get_address_service),
) -> AddressResponse:
    address = address_service.create_address(current_user.id, payload)
    return AddressResponse.from_orm(address)


@router.get("", response_model=list[AddressResponse])
def list_addresses(
    current_user: User = Depends(deps.get_current_user),
    address_repo: AddressRepository = Depends(deps.get_address_repository),
) -> list[AddressResponse]:
    addresses = address_repo.list_for_user(current_user.id)
    return [AddressResponse.from_orm(address) for address in addresses]


@router.put("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: UUID,
    payload: AddressUpdateRequest,
    current_user: User = Depends(deps.get_current_user),
    address_service: AddressService = Depends(deps.get_address_service),
) -> AddressResponse:
    address = address_service.update_address(current_user.id, address_id, payload)
    return AddressResponse.from_orm(address)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    address_service: AddressService = Depends(deps.get_address_service),
) -> None:
    address_service.delete_address(current_user.id, address_id)
