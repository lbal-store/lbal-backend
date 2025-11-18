from __future__ import annotations

from dataclasses import dataclass

import redis
from redis.exceptions import RedisError

from app.core.config import get_settings


@dataclass
class RateLimiter:
    prefix: str
    limit: int
    window_seconds: int

    def __post_init__(self) -> None:
        settings = get_settings()
        self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def allow(self, identifier: str) -> bool:
        key = f"{self.prefix}:{identifier or 'unknown'}"
        try:
            count = self.client.incr(key)
            if count == 1:
                self.client.expire(key, self.window_seconds)
            if count > self.limit:
                return False
            return True
        except RedisError:
            return True


login_rate_limiter = RateLimiter(prefix="rate:login", limit=5, window_seconds=60)
media_presign_rate_limiter = RateLimiter(prefix="rate:media:presign", limit=10, window_seconds=60)
listing_create_rate_limiter = RateLimiter(prefix="rate:listings:create", limit=10, window_seconds=60 * 60)
public_get_rate_limiter = RateLimiter(prefix="rate:public:get", limit=120, window_seconds=60)
