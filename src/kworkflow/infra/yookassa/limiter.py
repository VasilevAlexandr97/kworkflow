import asyncio
import logging

from limits import RateLimitItemPerMinute
from limits.aio.storage import RedisStorage
from limits.aio.strategies import MovingWindowRateLimiter

from kworkflow.common.interfaces.limiter import RateLimiter

logger = logging.getLogger(__name__)


class YookassaRateLimiter(RateLimiter):
    def __init__(
        self,
        shop_id: str,
        redis_uri: str,
        limit_per_minute: int = 100,
    ):
        self.shop_id = shop_id

        self.storage = RedisStorage(uri=redis_uri, implementation="redispy")
        self.limiter = MovingWindowRateLimiter(storage=self.storage)
        self.limit = RateLimitItemPerMinute(limit_per_minute)

        self._key = f"yookassa-ratelimit:{self.shop_id}"

    async def acquire(self):
        while True:
            if await self.limiter.hit(self.limit, self._key):
                logger.debug("Rate limiter hit True")
                return
            logger.debug("Rate limiter hit False, sleep 0.2 sec")
            await asyncio.sleep(0.2)
