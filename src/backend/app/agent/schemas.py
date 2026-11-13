"""Public invoice event contract for the autonomous invoice agent."""
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_id: str = Field(min_length=1, max_length=140)
    payee: str = Field(min_length=25, max_length=64)
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    currency: Literal["RLUSD", "XRP"]
    issuer: str | None = Field(default=None, max_length=64)
    network: Literal["testnet", "devnet"] = "testnet"
    reason: str = Field(min_length=3, max_length=800)


class AgentHealth(BaseModel):
    status: str
    component: str
