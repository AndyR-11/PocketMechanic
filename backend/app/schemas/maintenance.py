from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceCreate(BaseModel):
    service_type: str = Field(min_length=1, max_length=100)
    service_date: date
    mileage: int = Field(ge=0)
    notes: str | None = None


class MaintenanceUpdate(BaseModel):
    service_type: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    service_date: date | None = None
    mileage: int | None = Field(default=None, ge=0)
    notes: str | None = None


class MaintenanceResponse(MaintenanceCreate):
    id: int
    vehicle_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)