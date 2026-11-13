from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.dashboard import DashboardRepository


class DashboardService:
    SPEND_STATUSES = {"processing", "submitted", "settled", "submission_unknown"}
    SETTLED_STATUSES = {"submitted", "settled"}

    def __init__(self, session: Session):
        self.repository = DashboardRepository(session)

    def get_summary(self) -> dict:
        now = datetime.now(timezone.utc)
        business_tz = ZoneInfo(settings.business_timezone)
        local_today = now.astimezone(business_tz).date()
        local_start = datetime.combine(local_today, time.min, tzinfo=business_tz)
        local_end = local_start + timedelta(days=1)
        today_start = local_start.astimezone(timezone.utc)
        next_day = local_end.astimezone(timezone.utc)
        first_local_day = local_start - timedelta(days=6)
        week_start = first_local_day.astimezone(timezone.utc)
        mandate, payee_count, today, recent = self.repository.snapshot(
            today_start, next_day, week_start
        )

        currency = mandate.currency if mandate else "RLUSD"
        day_spend = sum(
            (row.amount for row in today
             if row.currency == currency and row.status in self.SPEND_STATUSES),
            Decimal("0"),
        )
        allowed = sum(1 for row in today if row.verdict == "allowed")
        blocked = sum(1 for row in today if row.verdict == "blocked")
        pending = sum(1 for row in today if row.status == "needs_approval")

        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {"allowed": 0, "blocked": 0, "volume": Decimal("0")}
        )
        for row in recent:
            stamp = row.created_at
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            key = stamp.astimezone(business_tz).date().isoformat()
            point = aggregate[key]
            if row.verdict == "allowed":
                point["allowed"] = int(point["allowed"]) + 1
                if row.status in self.SETTLED_STATUSES and row.currency == currency:
                    point["volume"] = Decimal(point["volume"]) + row.amount
            elif row.verdict == "blocked":
                point["blocked"] = int(point["blocked"]) + 1

        trend = []
        for offset in range(7):
            date = (first_local_day + timedelta(days=offset)).date()
            point = aggregate[date.isoformat()]
            trend.append({
                "label": date.strftime("%a"),
                "allowed": int(point["allowed"]),
                "blocked": int(point["blocked"]),
                "volume": Decimal(point["volume"]),
            })

        return {
            "mandate": mandate,
            "approved_payees": payee_count,
            "intents_today": len(today),
            "allowed_today": allowed,
            "blocked_today": blocked,
            "pending_approval": pending,
            "daily_spend": day_spend,
            "currency": currency,
            "network": settings.xrpl_network,
            "execution_enabled": settings.xrpl_payments_enabled,
            "trend": trend,
            "recent_intents": sorted(
                recent, key=lambda row: (row.created_at, row.id), reverse=True
            )[:8],
        }
