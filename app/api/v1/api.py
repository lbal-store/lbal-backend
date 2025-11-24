from fastapi import APIRouter

from app.api.v1.routers import addresses, auth, categories, notifications, orders, users


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(addresses.router)
api_router.include_router(categories.router)
api_router.include_router(orders.router)
api_router.include_router(notifications.router)
