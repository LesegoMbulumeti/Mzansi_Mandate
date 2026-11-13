from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import MandateRow


class MandateRepository:
    DEMO_MANDATE_ID = 1

    def __init__(self, session: Session):
        self.session = session

    def get(self) -> MandateRow | None:
        return self.session.get(MandateRow, self.DEMO_MANDATE_ID)

    def get_for_update(self) -> MandateRow | None:
        return self.session.scalar(
            select(MandateRow)
            .where(MandateRow.id == self.DEMO_MANDATE_ID)
            .with_for_update()
        )

    def save(self, values: dict) -> MandateRow:
        mandate = self.get()
        if mandate is None:
            mandate = MandateRow(id=self.DEMO_MANDATE_ID, **values)
            self.session.add(mandate)
        else:
            for key, value in values.items():
                setattr(mandate, key, value)
        self.session.flush()
        return mandate

    def set_active(self, active: bool) -> MandateRow | None:
        mandate = self.get()
        if mandate is not None and mandate.active != active:
            mandate.active = active
            mandate.version += 1
            mandate.updated_at = datetime.now(timezone.utc)
            self.session.flush()
        return mandate
