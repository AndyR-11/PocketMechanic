from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


def check_vehicle_year(year: int | None) -> None:
    # Precondition: Model year is at most one year past the current year.
    latest_year = date.today().year + 1
    if year is not None and year > latest_year:
        raise HTTPException(
            status_code=422,
            detail=f"Year cannot be later than {latest_year}"
        )


def add_vehicle(db: Session, user_id: int, data: VehicleCreate):
    # Contract 9 (AddVehicle)
    check_vehicle_year(data.year)
    vehicle = Vehicle(user_id=user_id, **data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def list_vehicles(db: Session, user_id: int):
    # Contract 10 (ManageVehicle)
    return db.scalars(
        select(Vehicle).where(Vehicle.user_id == user_id)
    ).all()


def get_vehicle(db: Session, user_id: int, vehicle_id: int):
    # Contracts 8 (GetVehicleInfo) and 10 (ManageVehicle)
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
    # Contracts 7 (UpdateVehicleInfo) and 10 (ManageVehicle)
    vehicle = get_vehicle(db, user_id, vehicle_id)
    changes = data.model_dump(exclude_unset=True)
    check_vehicle_year(changes.get("year"))

    # Precondition: Mileage cannot decrease.
    new_mileage = changes.get("mileage")
    if new_mileage is not None and new_mileage < vehicle.mileage:
        raise HTTPException(
            status_code=422,
            detail="Mileage cannot be lower than the current mileage"
        )

    for field, value in changes.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


def delete_vehicle(db: Session, user_id: int, vehicle_id: int):
    # Contract 10 (ManageVehicle)
    vehicle = get_vehicle(db, user_id, vehicle_id)
    db.delete(vehicle)
    db.commit()