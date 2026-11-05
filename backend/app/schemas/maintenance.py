from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MaintenanceCreate(BaseModel):
    service_type: str = Field(min_length=1, max_length=100)
    service_date: date
    mileage: int = Field(ge=0)
    cost: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2
    )
    notes: str | None = None


class MaintenanceUpdate(BaseModel):
    service_type: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    service_date: date | None = None
    mileage: int | None = Field(default=None, ge=0)
    cost: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2
    )
    notes: str | None = None

    @field_validator("service_type", "service_date", "mileage", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class MaintenanceResponse(MaintenanceCreate):
    id: int
    vehicle_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)