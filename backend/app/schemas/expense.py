from datetime import date as Date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(
        ge=0, max_digits=10, decimal_places=2
    )
    category: str = Field(min_length=1, max_length=100)
    date: Date
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category cannot be blank")
        return value


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2
    )
    category: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    date: Date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("amount", "category", "date", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("Field cannot be null")
        return value

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Category cannot be blank")
        return value


class ExpenseResponse(ExpenseCreate):
    id: int
    vehicle_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
