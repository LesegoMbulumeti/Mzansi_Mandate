from sqlalchemy.orm import Session

from app.repositories.audit import AuditRepository


class AuditService:
    def __init__(self, session: Session):
        self.repository = AuditRepository(session)

    def append_intent_event(self, intent, detail: str | None = None) -> None:
        self.repository.append(
            payee=intent.payee,
            amount=intent.amount,
            currency=intent.currency,
            source=intent.source,
            reason=intent.reason,
            verdict=intent.verdict,
            detail=detail or intent.detail,
            tx_hash=intent.tx_hash,
            intent_id=intent.id,
            source_reference=intent.source_reference,
            mandate_version=intent.mandate_version,
        )

    def list(self, limit: int, offset: int):
        return self.repository.list(limit, offset)
