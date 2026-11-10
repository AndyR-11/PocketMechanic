from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.vehicle import Vehicle
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.vehicle_service import get_vehicle


def add_expense(
    db: Session, user_id: int, vehicle_id: int, data: ExpenseCreate
):
    # Contract 17: AddExpense
    # Check that the vehicle belongs to the current user.
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


def update_expense(
    db: Session,
    user_id: int,
    expense_id: int,
    data: ExpenseUpdate
):
    # Contract 15: UpdateExpenseInfo
    expense = get_expense(db, user_id, expense_id)

    changes = data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)

    return expense


def delete_expense(db: Session, user_id: int, expense_id: int):
    # Contract 18: ManageExpense
    expense = get_expense(db, user_id, expense_id)

    db.delete(expense)
    db.commit()
