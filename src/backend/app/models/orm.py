"""SQLAlchemy tables. Domain dataclasses live in domain.py; repositories map between the two."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MandateRow(Base):
    __tablename__ = "mandates"

    id: Mapped[int] = mapped_column(primary_key=True)
    per_payment_cap: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    daily_cap: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    max_slippage_pct: Mapped[Decimal] = mapped_column(Numeric(6, 3), default=Decimal("1.0"))
    large_payment_threshold: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True)  # kill switch mirror
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    payees: Mapped[list["PayeeRow"]] = relationship(back_populates="mandate", cascade="all, delete-orphan")


class PayeeRow(Base):
    __tablename__ = "approved_payees"

    id: Mapped[int] = mapped_column(primary_key=True)
    mandate_id: Mapped[int] = mapped_column(ForeignKey("mandates.id"))
    name: Mapped[str] = mapped_column(String(120))
    xrpl_address: Mapped[str] = mapped_column(String(64), index=True)

    mandate: Mapped[MandateRow] = relationship(back_populates="payees")


class AuditRow(Base):
    """Append-only. Never update or delete rows."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    payee: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    currency: Mapped[str] = mapped_column(String(16))
    source: Mapped[str] = mapped_column(String(32))  # invoice | payroll | till | api
    reason: Mapped[str] = mapped_column(Text)  # the agent's stated reasoning
    verdict: Mapped[str] = mapped_column(String(24), index=True)
    detail: Mapped[str] = mapped_column(Text)
    tx_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
