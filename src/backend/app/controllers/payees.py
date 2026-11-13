from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers.security import require_operator
from app.db.session import get_session
from app.schemas.payee import PayeeIn, PayeeOut
from app.services.payee_service import PayeeService

router = APIRouter(prefix="/api/v1/payees", tags=["payees"], dependencies=[Depends(require_operator)])


@router.get("", response_model=list[PayeeOut])
def list_payees(session: Session = Depends(get_session)) -> list[PayeeOut]:
    return PayeeService(session).list()


@router.post("", response_model=PayeeOut, status_code=status.HTTP_201_CREATED)
def create_payee(body: PayeeIn, session: Session = Depends(get_session)) -> PayeeOut:
    return PayeeService(session).create(body.name, body.xrpl_address)


@router.delete("/{payee_id}", response_model=PayeeOut)
def deactivate_payee(payee_id: int, session: Session = Depends(get_session)) -> PayeeOut:
    return PayeeService(session).deactivate(payee_id)
