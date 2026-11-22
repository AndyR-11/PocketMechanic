
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.vehicle import Vehicle
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.expense_item_factory import ExpenseItemFactory
from app.services.vehicle_service import get_vehicle


def check_expense_date(expense_date: date | None) -> None:
    # Contract 17: an expense cannot be dated in the future.
    if expense_date is not None and expense_date > date.today():
        raise HTTPException(
            status_code=422,
            detail="Expense date cannot be in the future"
        )


def add_expense(
    db: Session, user_id: int, vehicle_id: int, data: ExpenseCreate
):
    # Contract 17: AddExpense
    check_expense_date(data.date)
    get_vehicle(db, user_id, vehicle_id)

    expense = Expense(
        vehicle_id=vehicle_id,
        **data.model_dump()
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(db: Session, user_id: int, vehicle_id: int):
    # Contract 18: ManageExpense
    get_vehicle(db, user_id, vehicle_id)

    return db.scalars(
        select(Expense)
        .where(Expense.vehicle_id == vehicle_id)
        .order_by(Expense.date.desc(), Expense.id.desc())
    ).all()


def get_expense(db: Session, user_id: int, expense_id: int):
    # Contract 16: GetExpenseInfo
    expense = db.scalar(
        select(Expense)
        .join(Vehicle, Expense.vehicle_id == Vehicle.id)
        .where(
            Expense.id == expense_id,
            Vehicle.user_id == user_id
        )
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    return expense


def check_manual_expense(expense: Expense):
    # Linked maintenance expenses must be managed through Maintenance.
    if expense.source_maintenance_id is not None:
        raise HTTPException(
            status_code=409,
            detail="This expense belongs to a maintenance record. "
                   "Edit or delete it from the Maintenance tab."
        )


def update_expense(
    db: Session,
    user_id: int,
    expense_id: int,
    data: ExpenseUpdate
):
    # Contract 15: UpdateExpenseInfo
    expense = get_expense(db, user_id, expense_id)
    check_manual_expense(expense)
    check_expense_date(data.date)

    changes = data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, user_id: int, expense_id: int):
    # Contract 18: ManageExpense
    expense = get_expense(db, user_id, expense_id)
    check_manual_expense(expense)

    db.delete(expense)
    db.commit()


def get_expense_overview(
    db: Session,
    user_id: int,
    vehicle_id: int | None = None
):
    """
    Return all expenses for the signed-in user.

    Maintenance costs are already synchronized into the
    expenses table by maintenance_service.py.

    Read them only once from the expenses table.
    """

    vehicles = db.scalars(
        select(Vehicle)
        .where(Vehicle.user_id == user_id)
        .order_by(Vehicle.year.desc(), Vehicle.id.desc())
    ).all()

    if vehicle_id is not None:
        if not any(v.id == vehicle_id for v in vehicles):
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

    query = (
        select(Expense, Vehicle)
        .join(Vehicle, Expense.vehicle_id == Vehicle.id)
        .where(Vehicle.user_id == user_id)
    )

    if vehicle_id is not None:
        query = query.where(
            Expense.vehicle_id == vehicle_id
        )

    query = query.order_by(
        Expense.date.desc(),
        Expense.id.desc()
    )

    items = [
        ExpenseItemFactory.create_overview_item(expense, vehicle)
        for expense, vehicle in db.execute(query)
    ]

    total = sum(
        (Decimal(str(item["amount"])) for item in items),
        Decimal("0.00")
    )

    return {
        "vehicles": [
            ExpenseItemFactory.create_vehicle_summary(vehicle)
            for vehicle in vehicles
        ],
        "items": items,
        "total": total,
        "count": len(items)
    }