from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.orm import MandateRow, PayeeRow, PaymentIntentRow


class DashboardRepository:
    def __init__(self, session: Session):
        self.session = session

    def snapshot(self, day_start: datetime, next_day: datetime, week_start: datetime):
        mandate = self.session.get(MandateRow, 1)
        payee_count = self.session.scalar(
            select(func.count()).select_from(PayeeRow).where(PayeeRow.active.is_(True))
        ) or 0
        today = list(self.session.scalars(
            select(PaymentIntentRow).where(
                PaymentIntentRow.created_at >= day_start,
                PaymentIntentRow.created_at < next_day,
            )
        ))
        recent = list(self.session.scalars(
            select(PaymentIntentRow).where(PaymentIntentRow.created_at >= week_start)
            .order_by(PaymentIntentRow.created_at, PaymentIntentRow.id)
        ))
        return mandate, payee_count, today, recent
