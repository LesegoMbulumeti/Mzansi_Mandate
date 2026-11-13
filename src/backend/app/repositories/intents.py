from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.orm import PaymentIntentRow
from app.models.orm import ApprovalRow


class IntentRepository:
    def __init__(self, session: Session):
        self.session = session

    def by_idempotency_key(self, key: str) -> PaymentIntentRow | None:
        return self.session.scalar(
            select(PaymentIntentRow).where(PaymentIntentRow.idempotency_key == key)
        )

    def get(self, intent_id: int) -> PaymentIntentRow | None:
        return self.session.get(PaymentIntentRow, intent_id)

    def list(self, limit: int, offset: int) -> tuple[list[PaymentIntentRow], int]:
        rows = list(self.session.scalars(
            select(PaymentIntentRow)
            .order_by(PaymentIntentRow.created_at.desc(), PaymentIntentRow.id.desc())
            .limit(limit).offset(offset)
        ))
        total = self.session.scalar(select(func.count()).select_from(PaymentIntentRow)) or 0
        return rows, total

    def daily_spend(self, start: datetime, end: datetime, currency: str) -> Decimal:
        amount = self.session.scalar(
            select(func.coalesce(func.sum(PaymentIntentRow.amount), 0)).where(
                PaymentIntentRow.created_at >= start,
                PaymentIntentRow.created_at < end,
                PaymentIntentRow.currency == currency,
                PaymentIntentRow.status.in_(["processing", "submitted", "settled", "submission_unknown"]),
            )
        )
        return Decimal(amount or 0)

    def create(self, **values) -> PaymentIntentRow:
        intent = PaymentIntentRow(**values)
        self.session.add(intent)
        self.session.flush()
        return intent

    def add_approval(self, intent_id: int, actor: str, decision: str, comment: str | None) -> ApprovalRow:
        approval = ApprovalRow(
            intent_id=intent_id, actor=actor, decision=decision, comment=comment
        )
        self.session.add(approval)
        self.session.flush()
        return approval
