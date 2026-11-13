"""SQLAlchemy tables. Domain dataclasses live in domain.py; repositories map between the two."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
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
    currency: Mapped[str] = mapped_column(String(16), default="RLUSD")
    issuer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(default=1)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True)  # kill switch mirror
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    payees: Mapped[list["PayeeRow"]] = relationship(back_populates="mandate", cascade="all, delete-orphan")


class PayeeRow(Base):
    __tablename__ = "approved_payees"

    id: Mapped[int] = mapped_column(primary_key=True)
    mandate_id: Mapped[int] = mapped_column(ForeignKey("mandates.id"))
    name: Mapped[str] = mapped_column(String(120))
    xrpl_address: Mapped[str] = mapped_column(String(64), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

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
    intent_id: Mapped[int | None] = mapped_column(ForeignKey("payment_intents.id"), nullable=True, index=True)
    source_reference: Mapped[str | None] = mapped_column(String(160), nullable=True)
    mandate_version: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class PaymentIntentRow(Base):
    __tablename__ = "payment_intents"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_payment_intents_idempotency_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    mandate_version: Mapped[int | None] = mapped_column(nullable=True)
    payee: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    currency: Mapped[str] = mapped_column(String(16))
    issuer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    network: Mapped[str] = mapped_column(String(16), default="testnet")
    source: Mapped[str] = mapped_column(String(32), default="api")
    source_reference: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(String(24), index=True)
    detail: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), index=True)
    tx_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ledger_result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class ApprovalRow(Base):
    """Append-only record of human approval decisions."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    intent_id: Mapped[int] = mapped_column(ForeignKey("payment_intents.id"), index=True)
    actor: Mapped[str] = mapped_column(String(120))
    decision: Mapped[str] = mapped_column(String(24))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
