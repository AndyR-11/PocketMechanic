from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


def add_vehicle(db: Session, user_id: int, data: VehicleCreate):
    vehicle = Vehicle(user_id=user_id, **data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def list_vehicles(db: Session, user_id: int):
    return db.scalars(
        select(Vehicle).where(Vehicle.user_id == user_id)
    ).all()


def get_vehicle(db: Session, user_id: int, vehicle_id: int):
    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.user_id == user_id
        )
    )

    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return vehicle


def update_vehicle(
    db: Session,
    user_id: int,
    vehicle_id: int,
    data: VehicleUpdate
):
    vehicle = get_vehicle(db, user_id, vehicle_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


def delete_vehicle(db: Session, user_id: int, vehicle_id: int):
    vehicle = get_vehicle(db, user_id, vehicle_id)
    db.delete(vehicle)
    db.commit()