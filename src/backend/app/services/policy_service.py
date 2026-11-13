from datetime import datetime, timezone
from decimal import Decimal

from app.models.domain import Mandate, PaymentIntent, Verdict


class PolicyService:
    """Pure decision logic. No I/O, so every block reason is unit-testable."""

    def evaluate(
        self, mandate: Mandate, intent: PaymentIntent, spent_today: Decimal
    ) -> tuple[Verdict, str]:
        if not mandate.active:
            return Verdict.BLOCKED, "kill switch engaged"
        if datetime.now(timezone.utc) >= mandate.expires_at:
            return Verdict.BLOCKED, "mandate expired"
        if intent.payee not in mandate.approved_payees:
            return Verdict.BLOCKED, "payee not on approved list"
        if intent.amount > mandate.per_payment_cap:
            return Verdict.BLOCKED, "exceeds per-payment cap"
        if spent_today + intent.amount > mandate.daily_cap:
            return Verdict.BLOCKED, "exceeds daily budget"
        threshold = mandate.large_payment_threshold
        if threshold is not None and intent.amount >= threshold:
            return Verdict.NEEDS_APPROVAL, "large payment needs human co-sign"
        return Verdict.ALLOWED, "within mandate"
