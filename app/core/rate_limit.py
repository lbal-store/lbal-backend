import time
from dataclasses import dataclass

import redis

from app.core.config import get_settings


@dataclass
class RateLimiter:
    prefix: str

    def __post_init__(self) -> None:
        self.settings = get_settings()
        self.client = redis.Redis.from_url(self.settings.redis_url, decode_responses=True)

    def hit(self, key: str) -> bool:
        redis_key = f"{self.prefix}:{key}"
        with self.client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(redis_key)
                    current = pipe.get(redis_key)
                    pipe.multi()
                    if current is None:
                        pipe.setex(redis_key, 60, 1)
                        pipe.execute()
                        return True
                    if int(current) >= self.settings.rate_limit_per_minute:
                        pipe.reset()
                        return False
                    pipe.setex(redis_key, 60, int(current) + 1)
                    pipe.execute()
                    return True
                except redis.WatchError:
                    continue
