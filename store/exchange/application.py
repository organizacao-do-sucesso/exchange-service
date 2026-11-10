import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from store.exchange.cache import RateCache
from store.exchange.client import ExchangeRateClient
from store.exchange.resource import router
from store.exchange.service import ExchangeService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = ExchangeRateClient(os.environ["EXCHANGE_API_URL"])
    cache = RateCache(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        ttl_seconds=int(os.environ["EXCHANGE_CACHE_TTL_SECONDS"]),
    )
    app.state.exchange_service = ExchangeService(client, cache)
    yield
    await cache.close()
    await client.close()


app = FastAPI(title="exchange", lifespan=lifespan)
app.include_router(router)
