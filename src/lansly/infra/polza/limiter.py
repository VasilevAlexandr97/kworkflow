import asyncio
import logging

from limits import RateLimitItemPerMinute
from limits.aio.storage import RedisStorage
from limits.aio.strategies import MovingWindowRateLimiter

from lansly.common.interfaces.limiter import RateLimiter

logger = logging.getLogger(__name__)


class PolzaRateLimiter(RateLimiter):
    def __init__(self, redis_uri: str, limit_per_minute: int = 180):
        self.storage = RedisStorage(uri=redis_uri, implementation="redispy")
        self.limiter = MovingWindowRateLimiter(storage=self.storage)
        self.limit = RateLimitItemPerMinute(limit_per_minute)
        self._key = "polza-ratelimit"

    async def acquire(self):
        while True:
            if await self.limiter.hit(self.limit, self._key):
                logger.debug("Polza rate limiter hit True")
                return
            logger.debug("Polza rate limiter hit False, sleep 0.2 sec")
            await asyncio.sleep(0.2)
