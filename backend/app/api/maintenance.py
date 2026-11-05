from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse
)
from app.services.auth_service import get_current_user
from app.services import maintenance_service

router = APIRouter(tags=["Maintenance"])


@router.post(
    "/vehicles/{vehicle_id}/maintenance",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED
)
def create_maintenance(
    vehicle_id: int,
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return maintenance_service.add_maintenance(
        db, current_user.id, vehicle_id, data
    )


@router.get(
    "/vehicles/{vehicle_id}/maintenance",
    response_model=list[MaintenanceResponse]
)
def list_vehicle_maintenance(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return maintenance_service.list_maintenance(
        db, current_user.id, vehicle_id
    )


@router.get(
    "/maintenance/{record_id}",
    response_model=MaintenanceResponse
)
def read_maintenance(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return maintenance_service.get_maintenance(
        db, current_user.id, record_id
    )


@router.put(
    "/maintenance/{record_id}",
    response_model=MaintenanceResponse
)
def edit_maintenance(
    record_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return maintenance_service.update_maintenance(
        db, current_user.id, record_id, data
    )


@router.delete(
    "/maintenance/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_maintenance(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    maintenance_service.delete_maintenance(
        db, current_user.id, record_id
    )