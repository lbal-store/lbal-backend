from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import ErrorCode, error_content
from app.core.rate_limit import public_get_rate_limiter


class PublicRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "GET" and not request.headers.get("Authorization"):
            identifier = request.client.host if request.client else "unknown"
            if not public_get_rate_limiter.allow(identifier):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=error_content(ErrorCode.RATE_LIMITED, "Too many requests. Try again later."),
                )
        response = await call_next(request)
        return response
