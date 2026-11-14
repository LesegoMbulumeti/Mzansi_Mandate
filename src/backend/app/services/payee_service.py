from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.xrpl_address import is_valid_classic_address
from app.repositories.mandates import MandateRepository
from app.repositories.payees import PayeeRepository
from app.services.errors import ConflictError, NotFoundError, ValidationError

class PayeeService:
    def __init__(self, session: Session):
        self.session = session
        self.mandates = MandateRepository(session)
        self.repository = PayeeRepository(session)

    def list(self):
        return self.repository.list()

    def create(self, name: str, address: str):
        mandate = self.mandates.get()
        if mandate is None:
            raise ConflictError("Create a mandate before adding approved payees")
        if not is_valid_classic_address(address):
            raise ValidationError("Destination must be a valid XRPL classic address")
        existing = self.repository.by_address(address)
        if existing and existing.active:
            raise ConflictError("This XRPL address already exists; choose the existing supplier record")
        try:
            if existing:
                # Deactivated suppliers can be re-approved without creating a
                # duplicate address or leaving the dashboard stuck on an old row.
                payee = self.repository.reactivate(existing, mandate.id, name.strip())
            else:
                payee = self.repository.create(mandate.id, name.strip(), address)
            mandate.version += 1
            mandate.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(payee)
            return payee
        except Exception:
            self.session.rollback()
            raise

    def deactivate(self, payee_id: int):
        payee = self.repository.get(payee_id)
        if payee is None:
            raise NotFoundError("Payee not found")
        try:
            result = self.repository.deactivate(payee)
            mandate = self.mandates.get()
            if mandate:
                mandate.version += 1
                mandate.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(result)
            return result
        except Exception:
            self.session.rollback()
            raise

    def update(self, payee_id: int, name: str, address: str):
        payee = self.repository.get(payee_id)
        if payee is None:
            raise NotFoundError("Payee not found")
        name = name.strip()
        address = address.strip()
        if len(name) < 2 or len(name) > 120:
            raise ValidationError("Supplier name must contain 2 to 120 characters")
        if not is_valid_classic_address(address):
            raise ValidationError("Destination must be a valid XRPL classic address")
        existing = self.repository.by_address(address)
        if existing and existing.id != payee.id:
            raise ConflictError("This XRPL address is already assigned to another supplier")
        try:
            result = self.repository.update(payee, name, address)
            mandate = self.mandates.get()
            if mandate:
                mandate.version += 1
                mandate.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(result)
            return result
        except Exception:
            self.session.rollback()
            raise
