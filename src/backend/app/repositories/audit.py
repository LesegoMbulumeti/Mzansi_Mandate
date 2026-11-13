from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.orm import AuditRow


class AuditRepository:
    def __init__(self, session: Session):
        self.session = session

    def append(self, **values) -> AuditRow:
        entry = AuditRow(**values)
        self.session.add(entry)
        self.session.flush()
        return entry

    def list(self, limit: int, offset: int) -> tuple[list[AuditRow], int]:
        rows = list(self.session.scalars(
            select(AuditRow).order_by(AuditRow.created_at.desc(), AuditRow.id.desc())
            .limit(limit).offset(offset)
        ))
        total = self.session.scalar(select(func.count()).select_from(AuditRow)) or 0
        return rows, total
