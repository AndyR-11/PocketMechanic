"""
Contract 26: GetDashboardSummary (Facade design pattern).

The dashboard page makes one request and this service collects the data
from Vehicle, Maintenance, Expense, and Reminder management for it.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.vehicle import Vehicle
from app.services.cost_analysis_service import get_cost_summary

try:
    from app.services.reminder_service import get_reminders
except ImportError:
    get_reminders = None

RECENT_MAINTENANCE_LIMIT = 5


def get_dashboard_summary(db: Session, user_id: int) -> dict:
    # Collaborates with VehicleService (10)
    vehicles = db.scalars(
        select(Vehicle)
        .where(Vehicle.user_id == user_id)
        .order_by(Vehicle.year.desc(), Vehicle.id.desc())
    ).all()

    # Collaborates with MaintenanceService (14)
    maintenance_count = db.scalar(
        select(func.count(MaintenanceRecord.id))
        .join(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(Vehicle.user_id == user_id)
    ) or 0

    recent = db.execute(
        select(MaintenanceRecord, Vehicle)
        .join(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(Vehicle.user_id == user_id)
        .order_by(
            MaintenanceRecord.service_date.desc(),
            MaintenanceRecord.id.desc()
        )
        .limit(RECENT_MAINTENANCE_LIMIT)
    ).all()

    schedule_count = db.scalar(
        select(func.count(MaintenanceSchedule.id))
        .join(Vehicle, MaintenanceSchedule.vehicle_id == Vehicle.id)
        .where(Vehicle.user_id == user_id)
    ) or 0

    # Collaborates with CostAnalysisService (25)
    total_expenses = get_cost_summary(db, user_id)["total"]

    # Collaborates with ReminderService (24)
    reminders = get_reminders(db, user_id) if get_reminders else []

    return {
        "vehicles": [
            {
                "id": v.id,
                "year": v.year,
                "make": v.make,
                "model": v.model,
                "mileage": v.mileage
            }
            for v in vehicles
        ],
        "vehicle_count": len(vehicles),
        "maintenance_count": maintenance_count,
        "recent_maintenance": [
            {
                "id": record.id,
                "vehicle_id": record.vehicle_id,
                "vehicle_make": vehicle.make,
                "vehicle_model": vehicle.model,
                "service_type": record.service_type,
                "service_date": record.service_date
            }
            for record, vehicle in recent
        ],
        "total_expenses": total_expenses,
        "schedule_count": schedule_count,
        "reminders_available": get_reminders is not None,
        "reminders": reminders
    }
