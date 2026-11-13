from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.controllers.security import require_intent_client, require_operator
from app.db.session import get_session
from app.schemas.approval import ApprovalIn
from app.schemas.intent import IntentIn, IntentOut, IntentPage
from app.services.intent_service import IntentService

router = APIRouter(prefix="/api/v1/intents", tags=["intents"])


@router.post("", response_model=IntentOut, dependencies=[Depends(require_intent_client)])
async def submit_intent(
    body: IntentIn,
    idempotency_key: str = Header(min_length=8, max_length=160, alias="Idempotency-Key"),
    session: Session = Depends(get_session),
) -> IntentOut:
    return await IntentService(session).submit(body, idempotency_key)


@router.get("", response_model=IntentPage, dependencies=[Depends(require_operator)])
def list_intents(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> IntentPage:
    items, total = IntentService(session).list(limit, offset)
    return IntentPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{intent_id}", response_model=IntentOut, dependencies=[Depends(require_operator)])
def get_intent(intent_id: int, session: Session = Depends(get_session)) -> IntentOut:
    return IntentService(session).get(intent_id)


@router.post("/{intent_id}/approve", response_model=IntentOut, dependencies=[Depends(require_operator)])
async def approve_intent(
    intent_id: int,
    body: ApprovalIn,
    session: Session = Depends(get_session),
) -> IntentOut:
    return await IntentService(session).approve(intent_id, "dashboard-operator", body.comment)


@router.post("/{intent_id}/reject", response_model=IntentOut, dependencies=[Depends(require_operator)])
def reject_intent(
    intent_id: int,
    body: ApprovalIn,
    session: Session = Depends(get_session),
) -> IntentOut:
    return IntentService(session).reject(intent_id, "dashboard-operator", body.comment)
