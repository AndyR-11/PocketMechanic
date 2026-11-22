from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_INTERVAL_MILES = 100000
MAX_INTERVAL_MONTHS = 120


class ScheduleIntervals(BaseModel):
    interval_miles: int | None = Field(
        default=None, ge=1, le=MAX_INTERVAL_MILES
    )
    interval_months: int | None = Field(
        default=None, ge=1, le=MAX_INTERVAL_MONTHS
    )

    @model_validator(mode="after")
    def require_an_interval(self):
        # Contract 19 and 21: at least one interval must be set.
        if self.interval_miles is None and self.interval_months is None:
            raise ValueError(
                "Set a mileage interval, a time interval, or both"
            )
        return self


class ScheduleCreate(ScheduleIntervals):
    service_type: str = Field(min_length=1, max_length=100)

    @field_validator("service_type")
    @classmethod
    def clean_service_type(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Service type cannot be blank")
        return value


class ScheduleUpdate(ScheduleIntervals):
    # Contract 19: updateScheduleInfo(scheduleId, newIntervalMiles,
    # newIntervalMonths). Both values are replaced together.
    pass


class ScheduleResponse(BaseModel):
    id: int
    vehicle_id: int
    service_type: str
    interval_miles: int | None
    interval_months: int | None
    start_date: date
    start_mileage: int
    created_at: datetime

    # Calculated by DueStrategy (Contract 23), not stored.
    last_service_date: date
    last_service_mileage: int
    last_service_from_record: bool
    next_due_mileage: int | None
    next_due_date: date | None

    model_config = ConfigDict(from_attributes=True)


class ScheduleVehicle(BaseModel):
    id: int
    year: int
    make: str
    model: str
    mileage: int


class ScheduleWithVehicleResponse(ScheduleResponse):
    vehicle: ScheduleVehicle
