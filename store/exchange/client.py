import logging

import httpx
from fastapi import HTTPException, status

from store.exchange.models import Rate

log = logging.getLogger(__name__)


class ExchangeRateClient:

    def __init__(self, base_url: str):
        self._http = httpx.AsyncClient(base_url=base_url, timeout=3.0)

    async def fetch_rate(self, origin: str, target: str) -> Rate:
        log.info("upstream_call pair=%s-%s", origin, target)
        try:
            response = await self._http.get(f"/json/last/{origin}-{target}")
        except httpx.HTTPError as e:
            log.error("Exchange API call failed: pair=%s-%s error=%r", origin, target, e)
            raise self._unavailable() from e

        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"Currency pair not found: {origin}-{target}",
            )
        if response.status_code != status.HTTP_200_OK:
            log.error(
                "Exchange API call failed: pair=%s-%s status=%s",
                origin, target, response.status_code,
            )
            raise self._unavailable()

        try:
            quote = response.json()[f"{origin}{target}"]
            # ask is the price the market sells at, bid the price it buys at
            return Rate(sell=quote["ask"], buy=quote["bid"], date=quote["create_date"])
        except (ValueError, KeyError, TypeError) as e:
            log.error("Unexpected Exchange API response: pair=%s-%s error=%r", origin, target, e)
            raise self._unavailable() from e

    async def close(self) -> None:
        await self._http.aclose()

    @staticmethod
    def _unavailable() -> HTTPException:
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Exchange API unavailable")
