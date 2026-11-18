
import os
import unittest
from datetime import date
from decimal import Decimal

os.environ.setdefault(
    "DATABASE_URL", "sqlite+pysqlite:///:memory:"
)

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.expense import Expense
from app.models.maintenance_record import MaintenanceRecord

from app.schemas.expense import ExpenseCreate
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.services.expense_service import (
    add_expense,
    get_expense_overview
)
from app.services.maintenance_service import (
    add_maintenance,
    update_maintenance,
    delete_maintenance
)


class ExpenseOverviewTests(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:"
        )
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

        self.db.add_all([
            User(
                name="Alex",
                email="alex@example.com",
                password_hash="test"
            ),
            User(
                name="Sam",
                email="sam@example.com",
                password_hash="test"
            )
        ])
        self.db.commit()

        self.db.add_all([
            Vehicle(
                user_id=1,
                make="Toyota",
                model="Tacoma",
                year=2025,
                mileage=10000
            ),
            Vehicle(
                user_id=2,
                make="Honda",
                model="Civic",
                year=2022,
                mileage=20000
            )
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_manual_and_maintenance_expenses(self):
        add_expense(
            self.db,
            1,
            1,
            ExpenseCreate(
                amount="30.00",
                category="Fuel",
                date=date.today()
            )
        )

        maintenance = add_maintenance(
            self.db,
            1,
            1,
            MaintenanceCreate(
                service_type="Oil Change",
                service_date=date.today(),
                mileage=10000,
                cost="75.00"
            )
        )

        result = get_expense_overview(self.db, 1)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["total"], Decimal("105.00"))

        sources = {item["source"] for item in result["items"]}
        self.assertEqual(sources, {"manual", "maintenance"})

        update_maintenance(
            self.db,
            1,
            maintenance.id,
            MaintenanceUpdate(cost="90.00")
        )

        result = get_expense_overview(self.db, 1)
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["total"], Decimal("120.00"))

        delete_maintenance(self.db, 1, maintenance.id)

        result = get_expense_overview(self.db, 1)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["total"], Decimal("30.00"))

    def test_vehicle_filter_and_user_ownership(self):
        add_expense(
            self.db,
            1,
            1,
            ExpenseCreate(
                amount="20.00",
                category="Parking",
                date=date.today()
            )
        )

        result = get_expense_overview(
            self.db, user_id=1, vehicle_id=1
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["total"], Decimal("20.00"))

        other_user = get_expense_overview(self.db, user_id=2)
        self.assertEqual(other_user["count"], 0)
        self.assertEqual(other_user["total"], Decimal("0.00"))

        with self.assertRaises(HTTPException) as error:
            get_expense_overview(
                self.db, user_id=2, vehicle_id=1
            )

        self.assertEqual(error.exception.status_code, 404)

    def test_maintenance_without_cost(self):
        add_maintenance(
            self.db,
            1,
            1,
            MaintenanceCreate(
                service_type="Inspection",
                service_date=date.today(),
                mileage=10000,
                cost=None
            )
        )

        result = get_expense_overview(self.db, 1)

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["total"], Decimal("0.00"))


if __name__ == "__main__":
    unittest.main()

