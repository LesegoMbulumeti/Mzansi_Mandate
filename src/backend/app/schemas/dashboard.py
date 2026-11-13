from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.intent import IntentOut
from app.schemas.mandate import MandateOut


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intent_id: int | None
    payee: str
    amount: Decimal
    currency: str
    source: str
    source_reference: str | None
    mandate_version: int | None
    reason: str
    verdict: str
    detail: str
    tx_hash: str | None
    created_at: datetime


class AuditPage(BaseModel):
    items: list[AuditOut]
    total: int
    limit: int
    offset: int


class TrendPoint(BaseModel):
    label: str
    allowed: int
    blocked: int
    volume: Decimal


class DashboardOut(BaseModel):
    mandate: MandateOut | None
    approved_payees: int
    intents_today: int
    allowed_today: int
    blocked_today: int
    pending_approval: int
    daily_spend: Decimal
    currency: str
    network: str
    execution_enabled: bool
    trend: list[TrendPoint]
    recent_intents: list[IntentOut]
