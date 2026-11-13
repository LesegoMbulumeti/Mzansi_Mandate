from datetime import datetime, timezone
from decimal import Decimal

from app.models.domain import Mandate, PaymentIntent, Verdict


class PolicyService:
    """Pure decision logic. No I/O, so every block reason is unit-testable."""

    def evaluate(
        self, mandate: Mandate, intent: PaymentIntent, spent_today: Decimal,
        now: datetime | None = None, approval_confirmed: bool = False,
    ) -> tuple[Verdict, str]:
        if not mandate.active:
            return Verdict.BLOCKED, "kill switch engaged"
        current_time = now or datetime.now(timezone.utc)
        expires_at = mandate.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if current_time >= expires_at:
            return Verdict.BLOCKED, "mandate expired"
        if intent.payee not in mandate.approved_payees:
            return Verdict.BLOCKED, "payee not on approved list"
        if intent.currency.upper() != mandate.currency.upper():
            return Verdict.BLOCKED, "asset not permitted by mandate"
        if mandate.issuer and intent.issuer != mandate.issuer:
            return Verdict.BLOCKED, "asset issuer does not match mandate"
        if intent.amount > mandate.per_payment_cap:
            return Verdict.BLOCKED, "exceeds per-payment cap"
        if spent_today + intent.amount > mandate.daily_cap:
            return Verdict.BLOCKED, "exceeds daily budget"
        threshold = mandate.large_payment_threshold
        if threshold is not None and intent.amount >= threshold and not approval_confirmed:
            return Verdict.NEEDS_APPROVAL, "large payment needs human co-sign"
        return Verdict.ALLOWED, "within mandate"
