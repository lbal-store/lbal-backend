from fastapi import FastAPI

from app.api.v1.routers import admin, auth, disputes, listings, media, orders, shipments, users, wallet
from app.core.errors import setup_error_handlers
from app.middleware.public_rate_limit import PublicRateLimitMiddleware


app = FastAPI(title="LBAL Backend", version="0.1.0")
setup_error_handlers(app)
app.add_middleware(PublicRateLimitMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(listings.router)
app.include_router(media.router)
app.include_router(orders.router)
app.include_router(wallet.router)
app.include_router(shipments.router)
app.include_router(disputes.router)
app.include_router(admin.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
