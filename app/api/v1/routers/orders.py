from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.v1 import deps
from app.api.v1.schemas.orders import OrderCreateRequest, OrderResponse, OrderStatusUpdateRequest
from app.db.models.user import User
from app.services.order_service import OrderService


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(deps.get_current_user),
    order_service: OrderService = Depends(deps.get_order_service),
) -> OrderResponse:
    order = order_service.create_order(current_user.id, payload)
    return OrderResponse.model_validate(order)


@router.get("/me", response_model=list[OrderResponse])
def list_buyer_orders(
    current_user: User = Depends(deps.get_current_user),
    order_service: OrderService = Depends(deps.get_order_service),
) -> list[OrderResponse]:
    orders = order_service.get_buyer_orders(current_user.id)
    return [OrderResponse.model_validate(order) for order in orders]


@router.get("/sold", response_model=list[OrderResponse])
def list_seller_orders(
    current_user: User = Depends(deps.get_current_user),
    order_service: OrderService = Depends(deps.get_order_service),
) -> list[OrderResponse]:
    orders = order_service.get_seller_orders(current_user.id)
    return [OrderResponse.model_validate(order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    order_service: OrderService = Depends(deps.get_order_service),
) -> OrderResponse:
    order = order_service.get_order(order_id, current_user)
    return OrderResponse.model_validate(order)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdateRequest,
    current_user: User = Depends(deps.get_current_user),
    order_service: OrderService = Depends(deps.get_order_service),
) -> OrderResponse:
    order = order_service.update_status(order_id, new_status=payload.status, actor=current_user)
    return OrderResponse.model_validate(order)
