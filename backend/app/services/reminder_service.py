"""
Contract 24: GetReminders.

Each due mileage and due date comes from calculate_next_due
(Contract 23, DueStrategy). This service does not store reminders.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.vehicle import Vehicle
from app.services.due_strategy import calculate_next_due

# A service inside either window is UPCOMING, unless it is already due.
UPCOMING_MILES = 500
UPCOMING_DAYS = 30


def _status(
    mileage: int,
    due_mileage: int | None,
    due_date: date | None,
    today: date
) -> str | None:
    # OVERDUE if mileage or date is at or past due.
    # UPCOMING if within 500 miles or 30 days, and not overdue.
    overdue = False
    upcoming = False

    if due_mileage is not None:
        miles_left = due_mileage - mileage
        if miles_left <= 0:
            overdue = True
        elif miles_left <= UPCOMING_MILES:
            upcoming = True

    if due_date is not None:
        days_left = (due_date - today).days
        if days_left <= 0:
            overdue = True
        elif days_left <= UPCOMING_DAYS:
            upcoming = True

    if overdue:
        return "OVERDUE"
    if upcoming:
        return "UPCOMING"
    return None


def _sort_key(reminder: dict):
    due_mileage = reminder["due_mileage"]
    return (
        0 if reminder["status"] == "OVERDUE" else 1,
        reminder["due_date"] or date.max,
        due_mileage if due_mileage is not None else 10**9,
        reminder["schedule_id"]
    )


def get_reminders(db: Session, user_id: int) -> list[dict]:
    # Contract 24. Only the signed-in user's schedules are considered.
    rows = db.execute(
        select(MaintenanceSchedule, Vehicle)
        .join(Vehicle, MaintenanceSchedule.vehicle_id == Vehicle.id)
        .where(Vehicle.user_id == user_id)
    ).all()

    today = date.today()
    reminders = []
    for schedule, vehicle in rows:
        due = calculate_next_due(db, schedule)
        status = _status(
            vehicle.mileage,
            due.due_mileage,
            due.due_date,
            today
        )
        if status is None:
            continue
        reminders.append({
            "schedule_id": schedule.id,
            "vehicle_id": vehicle.id,
            "vehicle_name": (
                f"{vehicle.year} {vehicle.make} {vehicle.model}"
            ),
            "service_type": schedule.service_type,
            "status": status,
            "due_mileage": due.due_mileage,
            "due_date": due.due_date
        })

    reminders.sort(key=_sort_key)
    return reminders