from decimal import Decimal

from pydantic import BaseModel, Field


class IntentIn(BaseModel):
    payee: str
    amount: Decimal = Field(gt=0)
    currency: str = "RLUSD"
    reason: str
    source: str = "api"


class IntentOut(BaseModel):
    verdict: str
    detail: str
    tx_hash: str | None = None
