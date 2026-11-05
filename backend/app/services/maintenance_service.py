from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.maintenance_record import MaintenanceRecord
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.services.vehicle_service import get_vehicle
from app.models.vehicle import Vehicle


def add_maintenance(
    db: Session, user_id: int, vehicle_id: int, data: MaintenanceCreate
):
    get_vehicle(db, user_id, vehicle_id)

    record = MaintenanceRecord(
        vehicle_id=vehicle_id,
        **data.model_dump()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_maintenance(db: Session, user_id: int, vehicle_id: int):
    get_vehicle(db, user_id, vehicle_id)

    return db.scalars(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.vehicle_id == vehicle_id)
        .order_by(MaintenanceRecord.service_date.desc())
    ).all()


def get_maintenance(db: Session, user_id: int, record_id: int):
    record = db.scalar(
        select(MaintenanceRecord)
        .join(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(
            MaintenanceRecord.id == record_id,
            Vehicle.user_id == user_id
        )
    )

    if record is None:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    return record


def update_maintenance(
    db: Session, user_id: int, record_id: int, data: MaintenanceUpdate
):
    record = get_maintenance(db, user_id, record_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


def delete_maintenance(db: Session, user_id: int, record_id: int):
    record = get_maintenance(db, user_id, record_id)
    db.delete(record)
    db.commit()