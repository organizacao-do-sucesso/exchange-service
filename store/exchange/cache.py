import logging

from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff
from redis.exceptions import RedisError

from store.exchange.models import Rate

log = logging.getLogger(__name__)


class RateCache:

    def __init__(self, host: str, port: int, ttl_seconds: int):
        self._ttl_seconds = ttl_seconds
        self._redis = Redis(
            host=host,
            port=port,
            socket_timeout=0.5,
            socket_connect_timeout=0.5,
            # a cache must fail fast: the default retries would add seconds per call
            retry=Retry(NoBackoff(), 0),
            decode_responses=True,
        )

    # the rate does not depend on the account, so it is left out of the key
    @staticmethod
    def _key(origin: str, target: str) -> str:
        return f"exchange:rate:{origin}:{target}"

    # if redis is down, log and fall back to calling the exchange API directly
    async def get(self, origin: str, target: str) -> Rate | None:
        try:
            value = await self._redis.get(self._key(origin, target))
        except (RedisError, OSError) as e:
            log.warning("Cache get failed: pair=%s-%s error=%r", origin, target, e)
            return None
        return Rate.model_validate_json(value) if value else None

    async def put(self, origin: str, target: str, rate: Rate) -> None:
        try:
            await self._redis.set(
                self._key(origin, target),
                rate.model_dump_json(),
                ex=self._ttl_seconds,
            )
        except (RedisError, OSError) as e:
            log.warning("Cache put failed: pair=%s-%s error=%r", origin, target, e)

    async def close(self) -> None:
        await self._redis.aclose()
