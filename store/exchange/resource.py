from typing import Annotated

from fastapi import APIRouter, Header, Request, Response

from store.exchange.models import ExchangeOut

router = APIRouter()


@router.get("/exchanges/{origin}/{target}", response_model=ExchangeOut)
async def exchange(
    origin: str,
    target: str,
    request: Request,
    response: Response,
    id_account: Annotated[str, Header(alias="id-account")],
) -> ExchangeOut:
    rate, hit = await request.app.state.exchange_service.exchange(origin, target)
    response.headers["X-Cache"] = "HIT" if hit else "MISS"
    return ExchangeOut(**rate.model_dump(), id_account=id_account)
