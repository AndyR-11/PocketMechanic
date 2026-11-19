from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class DashboardVehicle(BaseModel):
    id: int
    year: int
    make: str
    model: str
    mileage: int


class DashboardMaintenance(BaseModel):
    id: int
    vehicle_id: int
    vehicle_make: str
    vehicle_model: str
    service_type: str
    service_date: date


class DashboardReminder(BaseModel):
    # Shape expected from ReminderService.get_reminders (Contract 24).
    schedule_id: int
    vehicle_id: int
    vehicle_name: str
    service_type: str
    status: Literal["OVERDUE", "UPCOMING"]
    due_mileage: int | None = None
    due_date: date | None = None


class DashboardSummaryResponse(BaseModel):
    vehicles: list[DashboardVehicle]
    vehicle_count: int
    maintenance_count: int
    recent_maintenance: list[DashboardMaintenance]
    total_expenses: Decimal
    schedule_count: int
    reminders_available: bool
    reminders: list[DashboardReminder]
