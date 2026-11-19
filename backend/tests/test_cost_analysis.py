import os
import unittest
from datetime import date
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
from app.schemas.expense import ExpenseCreate
from app.schemas.maintenance import MaintenanceCreate
from app.services.expense_service import add_expense
from app.services.maintenance_service import add_maintenance
from app.services.cost_analysis_service import get_cost_summary


class CostAnalysisTests(unittest.TestCase):
    """Contract 25: GetCostSummary (Design by Contract)."""

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
            Vehicle(user_id=1, make="Toyota", model="Tacoma",
                    year=2025, mileage=10000),
            Vehicle(user_id=1, make="Ford", model="F-150",
                    year=2020, mileage=50000),
            Vehicle(user_id=2, make="Honda", model="Civic",
                    year=2022, mileage=5000)
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def expense(self, user, vehicle, amount, category, day):
        add_expense(self.db, user, vehicle, ExpenseCreate(
            amount=amount, category=category, date=day))

    def test_empty_summary(self):
        result = get_cost_summary(self.db, 1)
        self.assertEqual(result["total"], Decimal("0.00"))
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["by_category"], [])
        self.assertEqual(result["by_month"], [])

    def test_totals_by_category_and_month(self):
        self.expense(1, 1, "30.00", "Fuel", date(2026, 9, 5))
        self.expense(1, 1, "20.50", "Fuel", date(2026, 10, 5))
        self.expense(1, 2, "100.00", "Tires", date(2026, 10, 20))
        self.expense(2, 3, "999.00", "Fuel", date(2026, 10, 1))

        result = get_cost_summary(self.db, 1)
        self.assertEqual(result["total"], Decimal("150.50"))
        self.assertEqual(result["count"], 3)
        self.assertEqual(
            [(g["category"], g["total"], g["count"]) for g in result["by_category"]],
            [("Tires", Decimal("100.00"), 1), ("Fuel", Decimal("50.50"), 2)]
        )
        self.assertEqual(
            [(g["month"], g["total"]) for g in result["by_month"]],
            [("2026-09", Decimal("30.00")), ("2026-10", Decimal("120.50"))]
        )
        # Postcondition: every grouping adds up to the total.
        for key in ("by_category", "by_month"):
            self.assertEqual(
                sum(g["total"] for g in result[key]), result["total"])

    def test_maintenance_costs_grouped_once(self):
        add_maintenance(self.db, 1, 1, MaintenanceCreate(
            service_type="Oil Change", service_date=date(2026, 10, 1),
            mileage=10000, cost="75.00"))
        add_maintenance(self.db, 1, 1, MaintenanceCreate(
            service_type="Brakes", service_date=date(2026, 10, 2),
            mileage=10100, cost="225.00"))
        self.expense(1, 1, "40.00", "Fuel", date(2026, 10, 3))

        result = get_cost_summary(self.db, 1)
        self.assertEqual(result["total"], Decimal("340.00"))
        categories = {g["category"]: g["total"] for g in result["by_category"]}
        self.assertEqual(categories, {
            "Maintenance": Decimal("300.00"), "Fuel": Decimal("40.00")})

    def test_filter_by_vehicle(self):
        self.expense(1, 1, "30.00", "Fuel", date(2026, 9, 5))
        self.expense(1, 2, "100.00", "Tires", date(2026, 10, 20))
        result = get_cost_summary(self.db, 1, 2)
        self.assertEqual(result["total"], Decimal("100.00"))
        self.assertEqual(result["count"], 1)

    def test_other_users_vehicle_rejected(self):
        with self.assertRaises(HTTPException) as error:
            get_cost_summary(self.db, 1, 3)
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
