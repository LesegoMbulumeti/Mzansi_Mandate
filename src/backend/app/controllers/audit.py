from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.controllers.security import require_operator
from app.db.session import get_session
from app.schemas.dashboard import AuditOut, AuditPage
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/audit-events", tags=["audit"], dependencies=[Depends(require_operator)])


@router.get("", response_model=AuditPage)
def list_audit_events(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> AuditPage:
    items, total = AuditService(session).list(limit, offset)
    return AuditPage(items=items, total=total, limit=limit, offset=offset)
