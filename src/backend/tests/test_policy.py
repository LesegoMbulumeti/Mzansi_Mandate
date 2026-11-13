from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.domain import Mandate, PaymentIntent, Verdict
from app.services.policy_service import PolicyService


def mandate(**kw) -> Mandate:
    base = dict(
        per_payment_cap=Decimal("5000"),
        daily_cap=Decimal("12000"),
        approved_payees={"rSupplierA"},
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    base.update(kw)
    return Mandate(**base)


def intent(amount="1000", payee="rSupplierA") -> PaymentIntent:
    return PaymentIntent(payee=payee, amount=Decimal(amount), currency="RLUSD", reason="test")


def test_allows_within_mandate():
    assert PolicyService().evaluate(mandate(), intent(), Decimal(0))[0] == Verdict.ALLOWED


def test_blocks_unknown_payee():
    assert PolicyService().evaluate(mandate(), intent(payee="rEvil"), Decimal(0))[0] == Verdict.BLOCKED


def test_blocks_over_cap():
    assert PolicyService().evaluate(mandate(), intent("9000"), Decimal(0))[0] == Verdict.BLOCKED


def test_blocks_daily_budget():
    assert PolicyService().evaluate(mandate(), intent("4000"), Decimal("9000"))[0] == Verdict.BLOCKED


def test_blocks_kill_switch():
    assert PolicyService().evaluate(mandate(active=False), intent(), Decimal(0))[0] == Verdict.BLOCKED
