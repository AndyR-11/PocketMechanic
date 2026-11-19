from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import date

from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.vehicle import Vehicle
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.due_strategy import (
    calculate_next_due,
    normalize_service_type
)
from app.services.vehicle_service import get_vehicle


def to_response(
    db: Session,
    schedule: MaintenanceSchedule,
    vehicle: Vehicle | None = None
) -> dict:
    # Contract 20 (GetScheduleInfo) plus the due point from Contract 23.
    next_due = calculate_next_due(db, schedule)
    response = {
        "id": schedule.id,
        "vehicle_id": schedule.vehicle_id,
        "service_type": schedule.service_type,
        "interval_miles": schedule.interval_miles,
        "interval_months": schedule.interval_months,
        "start_date": schedule.start_date,
        "start_mileage": schedule.start_mileage,
        "created_at": schedule.created_at,
        "last_service_date": next_due.baseline.service_date,
        "last_service_mileage": next_due.baseline.mileage,
        "last_service_from_record": next_due.baseline.from_record,
        "next_due_mileage": next_due.due_mileage,
        "next_due_date": next_due.due_date
    }
    if vehicle is not None:
        response["vehicle"] = {
            "id": vehicle.id,
            "year": vehicle.year,
            "make": vehicle.make,
            "model": vehicle.model,
            "mileage": vehicle.mileage
        }
    return response


def check_duplicate(
    db: Session,
    vehicle_id: int,
    service_type: str,
    ignore_id: int | None = None
) -> None:
    # Private responsibility: one schedule per service type per vehicle.
    wanted = normalize_service_type(service_type)
    schedules = db.scalars(
        select(MaintenanceSchedule)
        .where(MaintenanceSchedule.vehicle_id == vehicle_id)
    ).all()
    for schedule in schedules:
        if schedule.id != ignore_id and \
                normalize_service_type(schedule.service_type) == wanted:
            raise HTTPException(
                status_code=409,
                detail="This vehicle already has a schedule for that service"
            )


def add_schedule(
    db: Session, user_id: int, vehicle_id: int, data: ScheduleCreate
):
    # Contract 21: AddSchedule
    # Precondition: the vehicle exists and belongs to the user.
    vehicle = get_vehicle(db, user_id, vehicle_id)
    check_duplicate(db, vehicle_id, data.service_type)

    schedule = MaintenanceSchedule(
        vehicle_id=vehicle_id,
        service_type=data.service_type,
        interval_miles=data.interval_miles,
        interval_months=data.interval_months,
        start_date=date.today(),
        start_mileage=vehicle.mileage
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def list_schedules(db: Session, user_id: int, vehicle_id: int):
    # Contract 22: ManageSchedule
    get_vehicle(db, user_id, vehicle_id)
    return db.scalars(
        select(MaintenanceSchedule)
        .where(MaintenanceSchedule.vehicle_id == vehicle_id)
        .order_by(MaintenanceSchedule.service_type)
    ).all()


def list_all_schedules(
    db: Session, user_id: int, vehicle_id: int | None = None
):
    # Contract 22: listAllSchedules, used by the Schedules page.
    if vehicle_id is not None:
        get_vehicle(db, user_id, vehicle_id)

    query = (
        select(MaintenanceSchedule, Vehicle)
        .join(Vehicle, MaintenanceSchedule.vehicle_id == Vehicle.id)
        .where(Vehicle.user_id == user_id)
    )
    if vehicle_id is not None:
        query = query.where(MaintenanceSchedule.vehicle_id == vehicle_id)

    return db.execute(
        query.order_by(
            Vehicle.year.desc(),
            Vehicle.id,
            MaintenanceSchedule.service_type
        )
    ).all()


def get_schedule(db: Session, user_id: int, schedule_id: int):
    # Contracts 20 and 22
    schedule = db.scalar(
        select(MaintenanceSchedule)
        .join(Vehicle, MaintenanceSchedule.vehicle_id == Vehicle.id)
        .where(
            MaintenanceSchedule.id == schedule_id,
            Vehicle.user_id == user_id
        )
    )
    if schedule is None:
        raise HTTPException(
            status_code=404,
            detail="Maintenance schedule not found"
        )
    return schedule


def update_schedule(
    db: Session, user_id: int, schedule_id: int, data: ScheduleUpdate
):
    # Contracts 19 (UpdateScheduleInfo) and 22 (ManageSchedule)
    schedule = get_schedule(db, user_id, schedule_id)
    schedule.interval_miles = data.interval_miles
    schedule.interval_months = data.interval_months
    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, user_id: int, schedule_id: int):
    # Contract 22: ManageSchedule
    schedule = get_schedule(db, user_id, schedule_id)
    db.delete(schedule)
    db.commit()
