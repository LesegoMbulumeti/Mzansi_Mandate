from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.integrations.xrpl_address import is_valid_classic_address
from app.repositories.mandates import MandateRepository
from app.services.errors import NotFoundError, ValidationError


class MandateService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = MandateRepository(session)

    def get(self):
        return self.repository.get()

    def update(self, *, per_payment_cap: Decimal, daily_cap: Decimal,
               max_slippage_pct: Decimal, large_payment_threshold: Decimal | None,
               currency: str, issuer: str | None, expires_at: datetime):
        if daily_cap < per_payment_cap:
            raise ValidationError("daily cap must be greater than or equal to the per-payment cap")
        if expires_at.tzinfo is None:
            raise ValidationError("expires_at must include a timezone")
        if expires_at <= datetime.now(timezone.utc):
            raise ValidationError("expires_at must be in the future")
        if currency.upper() == "RLUSD" and issuer is None:
            issuer = settings.rlusd_issuer or None
        if issuer is not None and not is_valid_classic_address(issuer):
            raise ValidationError("Issued asset issuer must be a valid XRPL classic address")
        current = self.repository.get()
        values = {
            "per_payment_cap": per_payment_cap,
            "daily_cap": daily_cap,
            "max_slippage_pct": max_slippage_pct,
            "large_payment_threshold": large_payment_threshold,
            "currency": currency.upper(),
            "issuer": issuer,
            "expires_at": expires_at,
            # Any material change suspends execution until a human reactivates it.
            "active": False,
            "version": current.version + 1 if current else 1,
        }
        try:
            mandate = self.repository.save(values)
            self.session.commit()
            self.session.refresh(mandate)
            return mandate
        except Exception:
            self.session.rollback()
            raise

    def set_active(self, active: bool):
        mandate = self.repository.get()
        if mandate is None:
            raise NotFoundError("Create a mandate before activating it")
        if active:
            expires_at = mandate.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise ValidationError("An expired mandate cannot be activated")
        mandate = self.repository.set_active(active)
        try:
            self.session.commit()
            self.session.refresh(mandate)
            return mandate
        except Exception:
            self.session.rollback()
            raise
