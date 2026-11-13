from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.integrations.xrpl_client import XrplClient
from app.models.domain import Mandate, PaymentIntent, Verdict
from app.models.orm import PaymentIntentRow
from app.repositories.intents import IntentRepository
from app.repositories.mandates import MandateRepository
from app.repositories.payees import PayeeRepository
from app.services.audit_service import AuditService
from app.services.errors import ConflictError, IntegrationError, NotFoundError, ValidationError
from app.services.policy_service import PolicyService


class IntentService:
    SPEND_STATUSES = {"processing", "submitted", "settled", "submission_unknown"}

    def __init__(self, session: Session):
        self.session = session
        self.intents = IntentRepository(session)
        self.mandates = MandateRepository(session)
        self.payees = PayeeRepository(session)
        self.policy = PolicyService()
        self.audit = AuditService(session)

    async def submit(self, body, idempotency_key: str) -> PaymentIntentRow:
        existing = self.intents.by_idempotency_key(idempotency_key)
        if existing:
            if not self._matches_request(existing, body):
                raise ConflictError("Idempotency key was already used for a different payment intent")
            return existing

        if body.network != settings.xrpl_network:
            raise ValidationError("Intent network must match the configured XRPL network")

        # Serialize policy/budget evaluation for this mandate on Postgres.
        mandate_row = self.mandates.get_for_update()
        payee = self.payees.by_address(body.payee, active_only=True)
        resolved_issuer = body.issuer or (
            mandate_row.issuer if mandate_row and mandate_row.issuer else settings.rlusd_issuer or None
        )
        intent = PaymentIntent(
            payee=body.payee,
            amount=body.amount,
            currency=body.currency.upper(),
            reason=body.reason,
            source=body.source,
            issuer=resolved_issuer,
        )

        verdict: Verdict
        detail: str
        if mandate_row is None:
            verdict, detail = Verdict.BLOCKED, "no mandate configured"
        else:
            mandate = Mandate(
                per_payment_cap=mandate_row.per_payment_cap,
                daily_cap=mandate_row.daily_cap,
                approved_payees={p.xrpl_address for p in self.payees.list(active_only=True)},
                expires_at=mandate_row.expires_at,
                max_slippage_pct=mandate_row.max_slippage_pct,
                large_payment_threshold=mandate_row.large_payment_threshold,
                active=mandate_row.active,
                currency=mandate_row.currency,
                issuer=mandate_row.issuer,
                version=mandate_row.version,
            )
            configured_issuer = mandate_row.issuer or settings.rlusd_issuer or None
            if body.currency.upper() != "XRP" and settings.xrpl_payments_enabled and not configured_issuer:
                verdict, detail = Verdict.BLOCKED, "issued asset issuer is not configured"
            elif body.currency.upper() != "XRP" and configured_issuer and resolved_issuer != configured_issuer:
                verdict, detail = Verdict.BLOCKED, "asset issuer does not match configured mandate issuer"
            elif payee is None:
                verdict, detail = Verdict.BLOCKED, "payee not on approved list"
            else:
                start, end = self._utc_day_bounds()
                spent_today = self.intents.daily_spend(start, end, body.currency.upper())
                verdict, detail = self.policy.evaluate(mandate, intent, spent_today)

        if verdict == Verdict.ALLOWED:
            if settings.xrpl_payments_enabled:
                detail = "within mandate; submitting to configured XRPL test network"
                status = "processing"
            else:
                detail = "within mandate; XRPL execution is disabled, no funds were moved"
                status = "authorized"
        elif verdict == Verdict.NEEDS_APPROVAL:
            status = "needs_approval"
        else:
            status = "blocked"

        row = self.intents.create(
            idempotency_key=idempotency_key,
            mandate_version=mandate_row.version if mandate_row else None,
            payee=body.payee,
            amount=body.amount,
            currency=body.currency.upper(),
            issuer=resolved_issuer,
            network=body.network,
            source=body.source,
            source_reference=body.source_reference,
            reason=body.reason,
            verdict=verdict.value,
            detail=detail,
            status=status,
        )
        self.audit.append_intent_event(row)
        try:
            # Persist the idempotency key and decision before any external call.
            self.session.commit()
            self.session.refresh(row)
        except IntegrityError:
            self.session.rollback()
            duplicate = self.intents.by_idempotency_key(idempotency_key)
            if duplicate:
                if not self._matches_request(duplicate, body):
                    raise ConflictError("Idempotency key was already used for a different payment intent")
                return duplicate
            raise ConflictError("Could not safely record this intent; retry with the same idempotency key")

        if verdict == Verdict.ALLOWED and settings.xrpl_payments_enabled:
            return await self._submit_to_ledger(row)
        return row

    async def _submit_to_ledger(self, row: PaymentIntentRow) -> PaymentIntentRow:
        try:
            result = await XrplClient().pay(
                payee=row.payee,
                amount=row.amount,
                currency=row.currency,
                issuer=row.issuer,
                network=row.network,
            )
            row.tx_hash = result.get("hash")
            row.ledger_result = result.get("ledger_result")
            if result.get("validated") and row.ledger_result == "tesSUCCESS":
                row.status = "settled"
                row.detail = "validated by XRPL with tesSUCCESS"
            elif result.get("validated"):
                row.status = "failed"
                row.detail = f"validated ledger result: {row.ledger_result or 'unknown'}"
            else:
                row.status = "submission_unknown"
                row.detail = "transaction returned without validated-ledger confirmation; reconcile before retrying"
        except IntegrationError as exc:
            row.status = "submission_unknown" if exc.outcome_unknown else "failed"
            row.detail = str(exc)
        except Exception:
            row.status = "submission_unknown"
            row.detail = "XRPL outcome is unknown; reconcile the account before retrying"

        self.audit.append_intent_event(row)
        try:
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    async def approve(self, intent_id: int, actor: str, comment: str | None):
        row = self.intents.get(intent_id)
        if row is None:
            raise NotFoundError("Payment intent not found")
        if row.status != "needs_approval":
            raise ConflictError("Only an intent awaiting approval can be approved")
        mandate_row = self.mandates.get_for_update()
        payee = self.payees.by_address(row.payee)
        if mandate_row is None:
            verdict, detail = Verdict.BLOCKED, "no mandate configured at approval time"
        elif payee is None:
            verdict, detail = Verdict.BLOCKED, "payee is no longer approved"
        elif settings.xrpl_payments_enabled and row.network != settings.xrpl_network:
            verdict, detail = Verdict.BLOCKED, "intent network no longer matches the configured XRPL network"
        elif (
            settings.xrpl_payments_enabled
            and row.currency != "XRP"
            and (not (mandate_row.issuer or settings.rlusd_issuer)
                 or row.issuer != (mandate_row.issuer or settings.rlusd_issuer))
        ):
            verdict, detail = Verdict.BLOCKED, "issued asset issuer no longer matches the active configuration"
        else:
            mandate = Mandate(
                per_payment_cap=mandate_row.per_payment_cap,
                daily_cap=mandate_row.daily_cap,
                approved_payees={p.xrpl_address for p in self.payees.list(active_only=True)},
                expires_at=mandate_row.expires_at,
                max_slippage_pct=mandate_row.max_slippage_pct,
                large_payment_threshold=mandate_row.large_payment_threshold,
                active=mandate_row.active,
                currency=mandate_row.currency,
                issuer=mandate_row.issuer,
                version=mandate_row.version,
            )
            start, end = self._utc_day_bounds()
            spent_today = self.intents.daily_spend(start, end, row.currency)
            verdict, detail = self.policy.evaluate(
                mandate,
                PaymentIntent(row.payee, row.amount, row.currency, row.reason, row.source, row.issuer),
                spent_today,
                approval_confirmed=True,
            )
        if verdict != Verdict.ALLOWED:
            row.mandate_version = mandate_row.version if mandate_row else None
            self.intents.add_approval(intent_id, actor, "approved_but_blocked", comment)
            row.verdict = Verdict.BLOCKED.value
            row.status = "blocked"
            row.detail = f"human approval could not override current policy: {detail}"
            self.audit.append_intent_event(row)
            self.session.commit()
            self.session.refresh(row)
            return row

        self.intents.add_approval(intent_id, actor, "approved", comment)
        row.mandate_version = mandate_row.version if mandate_row else None
        row.status = "processing" if settings.xrpl_payments_enabled else "authorized"
        row.detail = "approved by a human operator"
        self.audit.append_intent_event(row)
        self.session.commit()
        self.session.refresh(row)
        if settings.xrpl_payments_enabled:
            return await self._submit_to_ledger(row)
        return row

    def reject(self, intent_id: int, actor: str, comment: str | None):
        row = self.intents.get(intent_id)
        if row is None:
            raise NotFoundError("Payment intent not found")
        if row.status != "needs_approval":
            raise ConflictError("Only an intent awaiting approval can be rejected")
        self.intents.add_approval(intent_id, actor, "rejected", comment)
        row.status = "cancelled"
        row.detail = "rejected by a human operator"
        self.audit.append_intent_event(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list(self, limit: int, offset: int):
        return self.intents.list(limit, offset)

    def get(self, intent_id: int):
        row = self.intents.get(intent_id)
        if row is None:
            raise NotFoundError("Payment intent not found")
        return row

    @staticmethod
    def _utc_day_bounds() -> tuple[datetime, datetime]:
        business_tz = ZoneInfo(settings.business_timezone)
        local_today = datetime.now(business_tz).date()
        local_start = datetime.combine(local_today, time.min, tzinfo=business_tz)
        local_end = local_start + timedelta(days=1)
        return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)

    @staticmethod
    def _matches_request(row: PaymentIntentRow, body) -> bool:
        return (
            row.payee == body.payee
            and row.amount == body.amount
            and row.currency == body.currency.upper()
            and (body.issuer is None or row.issuer == body.issuer)
            and row.network == body.network
            and row.source == body.source
            and row.source_reference == body.source_reference
            and row.reason == body.reason
        )
