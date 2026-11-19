from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleWithVehicleResponse
)
from app.services.auth_service import get_current_user
from app.services import schedule_service

router = APIRouter(tags=["Maintenance Schedules"])


@router.post(
    "/vehicles/{vehicle_id}/schedules",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_schedule(
    vehicle_id: int,
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedule = schedule_service.add_schedule(
        db, current_user.id, vehicle_id, data
    )
    return schedule_service.to_response(db, schedule)


@router.get(
    "/vehicles/{vehicle_id}/schedules",
    response_model=list[ScheduleResponse]
)
def list_vehicle_schedules(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedules = schedule_service.list_schedules(
        db, current_user.id, vehicle_id
    )
    return [schedule_service.to_response(db, s) for s in schedules]


@router.get(
    "/schedules",
    response_model=list[ScheduleWithVehicleResponse]
)
def list_all_schedules(
    vehicle_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rows = schedule_service.list_all_schedules(
        db, current_user.id, vehicle_id
    )
    return [
        schedule_service.to_response(db, schedule, vehicle)
        for schedule, vehicle in rows
    ]


@router.get(
    "/schedules/{schedule_id}",
    response_model=ScheduleResponse
)
def read_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedule = schedule_service.get_schedule(
        db, current_user.id, schedule_id
    )
    return schedule_service.to_response(db, schedule)


@router.put(
    "/schedules/{schedule_id}",
    response_model=ScheduleResponse
)
def edit_schedule(
    schedule_id: int,
    data: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedule = schedule_service.update_schedule(
        db, current_user.id, schedule_id, data
    )
    return schedule_service.to_response(db, schedule)


@router.delete(
    "/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedule_service.delete_schedule(db, current_user.id, schedule_id)
