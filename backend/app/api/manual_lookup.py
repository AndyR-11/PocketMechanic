"""Authenticated, search-only maintenance manual finder (no Groq required)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.manual_finder import find_maintenance_manuals
from app.services.vehicle_service import get_vehicle

router = APIRouter(prefix="/ai", tags=["Maintenance Manual Finder"])


@router.get("/manuals")
def find_manuals(
    vehicle_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vehicle = get_vehicle(db, current_user.id, vehicle_id)
    return find_maintenance_manuals(vehicle.year, vehicle.make, vehicle.model)
