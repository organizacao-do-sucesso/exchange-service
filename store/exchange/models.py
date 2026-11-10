from pydantic import BaseModel, ConfigDict, Field


class Rate(BaseModel):
    sell: float
    buy: float
    date: str


class ExchangeOut(Rate):
    model_config = ConfigDict(populate_by_name=True)

    id_account: str = Field(alias="id-account")
