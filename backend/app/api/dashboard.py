from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.auth_service import get_current_user
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardSummaryResponse)
def read_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_dashboard_summary(db, current_user.id)
