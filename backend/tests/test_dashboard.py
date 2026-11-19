import os
import unittest
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.schemas.maintenance import MaintenanceCreate
from app.schemas.schedule import ScheduleCreate
from app.services.expense_service import add_expense, update_expense
from app.services.maintenance_service import add_maintenance
from app.services.schedule_service import add_schedule
from app.services.dashboard_service import get_dashboard_summary


class DashboardTests(unittest.TestCase):
    """Contract 26: GetDashboardSummary (Facade)."""

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
            Vehicle(user_id=1, make="Toyota", model="Tacoma", year=2025, mileage=10000),
            Vehicle(user_id=1, make="Ford", model="F-150", year=2020, mileage=50000),
            Vehicle(user_id=2, make="Honda", model="Civic", year=2022, mileage=5000)
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_empty_user(self):
        self.db.add(User(name="New", email="new@example.com", password_hash="x"))
        self.db.commit()
        result = get_dashboard_summary(self.db, 3)
        self.assertEqual(result["vehicle_count"], 0)
        self.assertEqual(result["maintenance_count"], 0)
        self.assertEqual(result["recent_maintenance"], [])
        self.assertEqual(result["total_expenses"], Decimal("0.00"))
        self.assertEqual(result["reminders"], [])

    def test_summary_uses_only_the_users_data(self):
        for i in range(7):
            add_maintenance(self.db, 1, 1, MaintenanceCreate(
                service_type=f"Service {i}",
                service_date=date(2026, 1, i + 1),
                mileage=1000 * i,
                cost="10.00" if i < 2 else None
            ))
        add_maintenance(self.db, 2, 3, MaintenanceCreate(
            service_type="Other user", service_date=date(2026, 6, 1),
            mileage=1, cost="500.00"))
        add_expense(self.db, 1, 2, ExpenseCreate(
            amount="30.00", category="Fuel", date=date(2026, 3, 1)))
        add_schedule(self.db, 1, 1, ScheduleCreate(
            service_type="Oil Change", interval_miles=5000))

        result = get_dashboard_summary(self.db, 1)
        self.assertEqual(result["vehicle_count"], 2)
        self.assertEqual(len(result["vehicles"]), 2)
        self.assertEqual(result["maintenance_count"], 7)
        self.assertEqual(result["schedule_count"], 1)
        # Two $10 maintenance costs plus one $30 expense.
        self.assertEqual(result["total_expenses"], Decimal("50.00"))
        # At most five records, newest first.
        dates = [r["service_date"] for r in result["recent_maintenance"]]
        self.assertEqual(len(dates), 5)
        self.assertEqual(dates, sorted(dates, reverse=True))
        self.assertEqual(dates[0], date(2026, 1, 7))


class ExpenseDateTests(unittest.TestCase):
    """Contract 17: expense dates cannot be in the future."""

    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(User(name="Alex", email="alex@example.com", password_hash="x"))
        self.db.commit()
        self.db.add(Vehicle(user_id=1, make="Toyota", model="Tacoma", year=2025, mileage=1))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_future_date_rejected(self):
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(HTTPException) as error:
            add_expense(self.db, 1, 1, ExpenseCreate(
                amount="5.00", category="Fuel", date=tomorrow))
        self.assertEqual(error.exception.status_code, 422)

    def test_today_allowed_and_update_checked(self):
        expense = add_expense(self.db, 1, 1, ExpenseCreate(
            amount="5.00", category="Fuel", date=date.today()))
        with self.assertRaises(HTTPException):
            update_expense(self.db, 1, expense.id, ExpenseUpdate(
                date=date.today() + timedelta(days=1)))


if __name__ == "__main__":
    unittest.main()
