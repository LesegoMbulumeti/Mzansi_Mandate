from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import PayeeRow


class PayeeRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self, active_only: bool = False) -> list[PayeeRow]:
        query = select(PayeeRow).order_by(PayeeRow.name)
        if active_only:
            query = query.where(PayeeRow.active.is_(True))
        return list(self.session.scalars(query))

    def get(self, payee_id: int) -> PayeeRow | None:
        return self.session.get(PayeeRow, payee_id)

    def by_address(self, address: str, active_only: bool = False) -> PayeeRow | None:
        query = select(PayeeRow).where(PayeeRow.xrpl_address == address)
        if active_only:
            query = query.where(PayeeRow.active.is_(True))
        return self.session.scalar(query)

    def create(self, mandate_id: int, name: str, address: str) -> PayeeRow:
        payee = PayeeRow(mandate_id=mandate_id, name=name, xrpl_address=address)
        self.session.add(payee)
        self.session.flush()
        return payee

    def deactivate(self, payee: PayeeRow) -> PayeeRow:
        payee.active = False
        self.session.flush()
        return payee

    def reactivate(self, payee: PayeeRow, mandate_id: int, name: str) -> PayeeRow:
        payee.mandate_id = mandate_id
        payee.name = name
        payee.active = True
        self.session.flush()
        return payee

    def update(self, payee: PayeeRow, name: str, address: str) -> PayeeRow:
        payee.name = name
        payee.xrpl_address = address
        self.session.flush()
        return payee
