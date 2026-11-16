import asyncio
import logging
from datetime import date, timedelta

import httpx
from fastapi import HTTPException, status

from store.exchange.models import Rate

log = logging.getLogger(__name__)

# PTAX quotes every currency against the real, so BRL itself is worth exactly 1
BRL = {"buy": 1.0, "sell": 1.0, "date": None}


class ExchangeRateClient:
    """Client of PTAX, the public exchange-rate API of the Central Bank of Brazil (BCB).

    Unlike commercial APIs, PTAX does not block requests coming from cloud
    providers, so the service works the same on a laptop and on EKS.
    """

    def __init__(self, base_url: str, timeout: float = 3.0):
        self._base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(timeout=timeout)

    async def fetch_rate(self, origin: str, target: str) -> Rate:
        log.info("upstream_call pair=%s-%s", origin, target)
        src, tgt = await asyncio.gather(self._brl_quote(origin), self._brl_quote(target))
        # cross rate through BRL:
        # buy  = what the market pays for 1 origin, in target (it buys origin, sells target)
        # sell = what the market charges for 1 origin, in target (it sells origin, buys target)
        return Rate(
            sell=round(src["sell"] / tgt["buy"], 6),
            buy=round(src["buy"] / tgt["sell"], 6),
            date=src["date"] or tgt["date"] or date.today().isoformat(),
        )

    async def _brl_quote(self, currency: str) -> dict:
        """Latest PTAX bulletin of a currency in BRL: {"buy", "sell", "date"}."""
        if currency == "BRL":
            return BRL
        # a 7-day window always holds a business day (weekends and holidays have no PTAX)
        end = date.today()
        start = end - timedelta(days=7)
        url = (
            f"{self._base_url}/CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,"
            "dataFinalCotacao=@dataFinalCotacao)"
            f"?@moeda='{currency}'&@dataInicial='{start:%m-%d-%Y}'&@dataFinalCotacao='{end:%m-%d-%Y}'"
            "&$format=json&$select=cotacaoCompra,cotacaoVenda,dataHoraCotacao"
        )
        try:
            response = await self._http.get(url)
        except httpx.HTTPError as e:
            log.error("PTAX call failed: currency=%s error=%r", currency, e)
            raise self._unavailable() from e

        if response.status_code != status.HTTP_200_OK:
            log.error("PTAX call failed: currency=%s status=%s", currency, response.status_code)
            raise self._unavailable()

        try:
            rows = response.json()["value"]
        except (ValueError, KeyError, TypeError) as e:
            log.error("Unexpected PTAX response: currency=%s error=%r", currency, e)
            raise self._unavailable() from e

        if not rows:  # PTAX answers an unknown currency with 200 and an empty list
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Currency not found: {currency}")

        last = rows[-1]  # rows come in time order: the latest bulletin is the last one
        return {
            "buy": last["cotacaoCompra"],
            "sell": last["cotacaoVenda"],
            "date": last["dataHoraCotacao"][:19],
        }

    async def close(self) -> None:
        await self._http.aclose()

    @staticmethod
    def _unavailable() -> HTTPException:
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Exchange API unavailable")
