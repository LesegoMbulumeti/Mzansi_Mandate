from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IntentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payee: str = Field(min_length=25, max_length=64)
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    currency: Literal["RLUSD", "XRP"] = "RLUSD"
    issuer: str | None = Field(default=None, max_length=64)
    network: Literal["testnet", "devnet"] = "testnet"
    reason: str = Field(min_length=3, max_length=1000)
    source: Literal["invoice", "payroll", "till", "api"] = "api"
    source_reference: str | None = Field(default=None, max_length=160)


class IntentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idempotency_key: str
    mandate_version: int | None
    payee: str
    amount: Decimal
    currency: str
    issuer: str | None
    network: str
    source: str
    source_reference: str | None
    reason: str
    verdict: str
    detail: str
    status: str
    tx_hash: str | None
    ledger_result: str | None
    created_at: datetime


class IntentPage(BaseModel):
    items: list[IntentOut]
    total: int
    limit: int
    offset: int
