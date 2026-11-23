from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardReminder
from app.services.auth_service import get_current_user
from app.services.reminder_service import get_reminders

router = APIRouter(tags=["Reminders"])


@router.get("/reminders", response_model=list[DashboardReminder])
def read_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Same keys the dashboard already reads from get_reminders.
    return get_reminders(db, current_user.id)