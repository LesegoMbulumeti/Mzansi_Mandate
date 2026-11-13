from datetime import datetime
from decimal import Decimal

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MandateIn(BaseModel):
    per_payment_cap: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    daily_cap: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    max_slippage_pct: Decimal = Field(default=Decimal("1.0"), ge=0, le=100)
    large_payment_threshold: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=6)
    currency: Literal["RLUSD", "XRP"] = "RLUSD"
    issuer: str | None = Field(default=None, max_length=64)
    expires_at: datetime


class MandateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    per_payment_cap: Decimal
    daily_cap: Decimal
    max_slippage_pct: Decimal
    large_payment_threshold: Decimal | None
    currency: str
    issuer: str | None
    version: int
    expires_at: datetime
    active: bool
    created_at: datetime
    updated_at: datetime | None
