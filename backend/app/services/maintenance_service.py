
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.maintenance_record import MaintenanceRecord
from app.models.expense import Expense
from app.models.vehicle import Vehicle
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate
)
from app.services.vehicle_service import get_vehicle


def check_service_date(service_date: date | None) -> None:
    # A completed maintenance service cannot be dated in the future.
    if service_date is not None and service_date > date.today():
        raise HTTPException(
            status_code=422,
            detail="Service date cannot be in the future"
        )


def sync_maintenance_expense(
    db: Session,
    record: MaintenanceRecord
):
    # Find an expense already linked to this maintenance record.
    expense = db.scalar(
        select(Expense).where(
            Expense.source_maintenance_id == record.id
        )
    )

    # No positive cost means no expense should be recorded.
    if record.cost is None or record.cost <= Decimal("0"):
        if expense is not None:
            db.delete(expense)
        return

    if expense is None:
        # Create one linked expense.
        expense = Expense(
            vehicle_id=record.vehicle_id,
            source_maintenance_id=record.id,
            amount=record.cost,
            category=f"Maintenance: {record.service_type}",
            date=record.service_date,
            notes=record.notes
        )
        db.add(expense)
    else:
        # Update the same expense instead of creating another.
        expense.amount = record.cost
        expense.category = f"Maintenance: {record.service_type}"
        expense.date = record.service_date
        expense.notes = record.notes


def add_maintenance(
    db: Session,
    user_id: int,
    vehicle_id: int,
    data: MaintenanceCreate
):
    # Contract 13: AddMaintenanceRecord
    check_service_date(data.service_date)
    get_vehicle(db, user_id, vehicle_id)

    record = MaintenanceRecord(
        vehicle_id=vehicle_id,
        **data.model_dump()
    )

    try:
        db.add(record)
        db.flush()

        sync_maintenance_expense(db, record)

        # Both records are committed together.
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise

    return record


def list_maintenance(db: Session, user_id: int, vehicle_id: int):
    # Contract 14: ManageMaintenanceRecord
    get_vehicle(db, user_id, vehicle_id)

    return db.scalars(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.vehicle_id == vehicle_id)
        .order_by(MaintenanceRecord.service_date.desc())
    ).all()


def get_maintenance(db: Session, user_id: int, record_id: int):
    # Contracts 12 and 14
    record = db.scalar(
        select(MaintenanceRecord)
        .join(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(
            MaintenanceRecord.id == record_id,
            Vehicle.user_id == user_id
        )
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found"
        )

    return record


def update_maintenance(
    db: Session,
    user_id: int,
    record_id: int,
    data: MaintenanceUpdate
):
    # Contracts 11 and 14
    check_service_date(data.service_date)
    record = get_maintenance(db, user_id, record_id)

    changes = data.model_dump(exclude_unset=True)

    try:
        for field, value in changes.items():
            setattr(record, field, value)

        db.flush()
        sync_maintenance_expense(db, record)

        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise

    return record


def delete_maintenance(
    db: Session,
    user_id: int,
    record_id: int
):
    # Contract 14: ManageMaintenanceRecord
    record = get_maintenance(db, user_id, record_id)

    try:
        # Remove the linked expense before its maintenance record.
        expense = db.scalar(
            select(Expense).where(
                Expense.source_maintenance_id == record.id
            )
        )

        if expense is not None:
            db.delete(expense)
            db.flush()

        db.delete(record)
        db.commit()
    except Exception:
        db.rollback()
        raise
