from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse
)
from app.services.auth_service import get_current_user
from app.services import vehicle_service

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return vehicle_service.add_vehicle(db, current_user.id, data)


@router.get("", response_model=list[VehicleResponse])
def list_user_vehicles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return vehicle_service.list_vehicles(db, current_user.id)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def read_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return vehicle_service.get_vehicle(
        db, current_user.id, vehicle_id
    )


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def edit_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return vehicle_service.update_vehicle(
        db, current_user.id, vehicle_id, data
    )


@router.delete("/{vehicle_id}", status_code=204)
def remove_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle_service.delete_vehicle(
        db, current_user.id, vehicle_id
    )