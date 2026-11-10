from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse
)
from app.services.auth_service import get_current_user
from app.services import expense_service


router = APIRouter(tags=["Expenses"])


@router.post(
    "/vehicles/{vehicle_id}/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED
)
def create_expense(
    vehicle_id: int,
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expense_service.add_expense(
        db, current_user.id, vehicle_id, data
    )


@router.get(
    "/vehicles/{vehicle_id}/expenses",
    response_model=list[ExpenseResponse]
)
def list_vehicle_expenses(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expense_service.list_expenses(
        db, current_user.id, vehicle_id
    )


@router.get(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse
)
def read_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expense_service.get_expense(
        db, current_user.id, expense_id
    )


@router.put(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse
)
def edit_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expense_service.update_expense(
        db, current_user.id, expense_id, data
    )


@router.delete(
    "/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense_service.delete_expense(
        db, current_user.id, expense_id
    )
