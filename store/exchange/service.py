import re

from fastapi import HTTPException, status

from store.exchange.cache import RateCache
from store.exchange.client import ExchangeRateClient
from store.exchange.models import Rate

CURRENCY_CODE = re.compile(r"[A-Z]{3}")


class ExchangeService:

    def __init__(self, client: ExchangeRateClient, cache: RateCache):
        self._client = client
        self._cache = cache

    async def exchange(self, origin: str, target: str) -> tuple[Rate, bool]:
        origin, target = self._normalize(origin), self._normalize(target)

        cached = await self._cache.get(origin, target)
        if cached is not None:
            return cached, True

        rate = await self._client.fetch_rate(origin, target)
        await self._cache.put(origin, target, rate)
        return rate, False

    @staticmethod
    def _normalize(currency: str) -> str:
        code = currency.upper()
        if not CURRENCY_CODE.fullmatch(code):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Invalid currency code: {currency}",
            )
        return code
