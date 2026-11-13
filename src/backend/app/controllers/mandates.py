from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.security import require_operator
from app.db.session import get_session
from app.schemas.mandate import MandateIn, MandateOut
from app.services.mandate_service import MandateService

router = APIRouter(prefix="/api/v1/mandate", tags=["mandate"], dependencies=[Depends(require_operator)])


@router.get("", response_model=MandateOut | None)
def get_mandate(session: Session = Depends(get_session)) -> MandateOut | None:
    return MandateService(session).get()


@router.put("", response_model=MandateOut)
def update_mandate(body: MandateIn, session: Session = Depends(get_session)) -> MandateOut:
    return MandateService(session).update(**body.model_dump())


@router.post("/activate", response_model=MandateOut)
def activate_mandate(session: Session = Depends(get_session)) -> MandateOut:
    return MandateService(session).set_active(True)


@router.post("/suspend", response_model=MandateOut)
def suspend_mandate(session: Session = Depends(get_session)) -> MandateOut:
    return MandateService(session).set_active(False)
