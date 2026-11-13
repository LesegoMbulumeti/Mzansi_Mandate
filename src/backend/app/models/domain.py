from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class Verdict(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    NEEDS_APPROVAL = "needs_approval"


@dataclass
class Mandate:
    per_payment_cap: Decimal
    daily_cap: Decimal
    approved_payees: set[str]
    expires_at: datetime
    max_slippage_pct: Decimal = Decimal("1.0")
    large_payment_threshold: Decimal | None = None
    active: bool = True  # kill switch


@dataclass
class PaymentIntent:
    payee: str
    amount: Decimal
    currency: str
    reason: str
    source: str = "api"  # invoice | payroll | till | api


@dataclass
class AuditEntry:
    intent: PaymentIntent
    verdict: Verdict
    detail: str
    tx_hash: str | None = None
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
