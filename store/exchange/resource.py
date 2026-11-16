from typing import Annotated

from fastapi import APIRouter, Header, Request, Response

from store.exchange.models import ExchangeOut

router = APIRouter()


# /exchanges is the platform contract (gateway route and the Feign client in `exchange`);
# /exchange is the path used by the course's BACEN page, served for compatibility
@router.get("/exchanges/{origin}/{target}", response_model=ExchangeOut)
@router.get("/exchange/{origin}/{target}", response_model=ExchangeOut, include_in_schema=False)
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


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
