import os
import unittest
from datetime import date, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_schedule import MaintenanceSchedule
from app.schemas.dashboard import DashboardReminder
from app.services.due_strategy import add_months, calculate_next_due
from app.services.dashboard_service import get_dashboard_summary
from app.services.reminder_service import get_reminders


def start_for_due(target: date) -> tuple[date, int]:
    """A start date and month interval whose next due date is target."""
    for months in (1, 2, 3, 4):
        for delta in range(1, months * 32):
            candidate = target - timedelta(days=delta)
            if add_months(candidate, months) == target:
                return candidate, months
    raise AssertionError(f"no baseline produces due date {target}")


class ReminderServiceTests(unittest.TestCase):
    """Contract 24: GetReminders, using Contract 23 for the due point.

    Case ids match docs/test-plan.md (REM-01 through REM-10).
    """

    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([
            User(name="Alex", email="alex@example.com", password_hash="x"),
            User(name="Sam", email="sam@example.com", password_hash="x")
        ])
        self.db.commit()
        self.db.add_all([
            Vehicle(
                user_id=1, make="Toyota", model="Corolla",
                year=2020, mileage=10000
            ),
            Vehicle(
                user_id=2, make="Honda", model="Civic",
                year=2021, mileage=10000
            )
        ])
        self.db.commit()
        self.today = date.today()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def set_mileage(self, mileage: int, vehicle_id: int = 1):
        vehicle = self.db.get(Vehicle, vehicle_id)
        vehicle.mileage = mileage
        self.db.commit()

    def add_schedule(
        self,
        service_type: str,
        start_mileage: int,
        interval_miles: int | None = None,
        interval_months: int | None = None,
        start_date: date | None = None,
        vehicle_id: int = 1
    ) -> MaintenanceSchedule:
        schedule = MaintenanceSchedule(
            vehicle_id=vehicle_id,
            service_type=service_type,
            interval_miles=interval_miles,
            interval_months=interval_months,
            start_date=start_date or self.today,
            start_mileage=start_mileage
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def by_type(self, service_type: str) -> dict | None:
        for reminder in get_reminders(self.db, 1):
            if reminder["service_type"] == service_type:
                return reminder
        return None

    def test_mileage_at_or_past_due_is_overdue(self):
        # REM-01. Due mileage is the baseline plus the interval.
        self.add_schedule("Oil Change", start_mileage=10000, interval_miles=5000)
        self.set_mileage(15000)
        reminder = self.by_type("Oil Change")
        self.assertIsNotNone(reminder)
        self.assertEqual(reminder["status"], "OVERDUE")
        self.assertEqual(reminder["due_mileage"], 15000)
        self.assertIsNone(reminder["due_date"])

        self.set_mileage(15001)
        self.assertEqual(self.by_type("Oil Change")["status"], "OVERDUE")

    def test_mileage_window_is_500(self):
        # REM-02. 500 miles out is UPCOMING. 501 is not a reminder.
        due_soon = self.add_schedule(
            "Tire Rotation", start_mileage=10000, interval_miles=500
        )
        self.add_schedule(
            "Brake Inspection", start_mileage=10000, interval_miles=501
        )
        soon = self.by_type("Tire Rotation")
        self.assertEqual(soon["status"], "UPCOMING")
        self.assertEqual(soon["due_mileage"], 10500)
        self.assertEqual(
            soon["due_mileage"],
            calculate_next_due(self.db, due_soon).due_mileage
        )
        self.assertIsNone(self.by_type("Brake Inspection"))

    def test_date_at_or_past_due_is_overdue(self):
        # REM-03.
        for name, target in (
            ("Inspection", self.today),
            ("Coolant", self.today - timedelta(days=1))
        ):
            start, months = start_for_due(target)
            self.add_schedule(
                name,
                start_mileage=0,
                interval_months=months,
                start_date=start
            )
            reminder = self.by_type(name)
            self.assertEqual(reminder["status"], "OVERDUE")
            self.assertEqual(reminder["due_date"], target)
            self.assertIsNone(reminder["due_mileage"])

    def test_matching_record_moves_the_due_point(self):
        # REM-06. The newest matching service is the baseline.
        schedule = self.add_schedule(
            "Oil Change", start_mileage=0, interval_miles=500
        )
        self.db.add(MaintenanceRecord(
            vehicle_id=1,
            service_type="oil   change",
            service_date=self.today,
            mileage=19800
        ))
        self.db.commit()
        self.set_mileage(20000)

        reminder = self.by_type("Oil Change")
        due = calculate_next_due(self.db, schedule)
        self.assertTrue(due.baseline.from_record)
        self.assertEqual(due.due_mileage, 20300)
        self.assertEqual(reminder["due_mileage"], 20300)
        self.assertEqual(reminder["status"], "UPCOMING")

    def test_get_reminders_route(self):
        # REM-09.
        from app.api.reminders import router
        from app.main import app

        route_methods = [
            route.methods
            for route in router.routes
            if getattr(route, "path", None) == "/reminders"
        ]
        self.assertTrue(any("GET" in methods for methods in route_methods))

        reminders_path = app.openapi()["paths"]["/reminders"]
        self.assertIn("get", reminders_path)


if __name__ == "__main__":
    unittest.main()