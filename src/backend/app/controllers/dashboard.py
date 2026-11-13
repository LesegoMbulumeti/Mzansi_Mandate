from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.security import require_operator
from app.db.session import get_session
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"], dependencies=[Depends(require_operator)])


@router.get("", response_model=DashboardOut)
def get_dashboard(session: Session = Depends(get_session)) -> DashboardOut:
    return DashboardService(session).get_summary()
