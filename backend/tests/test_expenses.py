import os
import unittest

os.environ.setdefault(
    "DATABASE_URL", "sqlite+pysqlite:///:memory:"
)

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.expense import Expense

from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.expense_service import (
    add_expense,
    get_expense,
    list_expenses,
    update_expense,
    delete_expense
)


class ExpenseServiceTests(unittest.TestCase):

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
                model="Corolla",
                year=2020,
                mileage=10000
            ),
            Vehicle(
                user_id=2,
                make="Honda",
                model="Civic",
                year=2021,
                mileage=20000
            )
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_expense_crud(self):
        expense = add_expense(
            self.db, 1, 1,
            ExpenseCreate(
                amount="52.45",
                category="Fuel",
                date="2026-11-09"
            )
        )

        self.assertEqual(str(expense.amount), "52.45")

        records = list_expenses(self.db, 1, 1)
        self.assertEqual(len(records), 1)

        found = get_expense(self.db, 1, expense.id)
        self.assertEqual(found.category, "Fuel")

        update_expense(
            self.db, 1, expense.id,
            ExpenseUpdate(amount="57.45")
        )

        updated = get_expense(self.db, 1, expense.id)
        self.assertEqual(str(updated.amount), "57.45")

        delete_expense(self.db, 1, expense.id)

        self.assertEqual(
            list_expenses(self.db, 1, 1), []
        )

    def test_vehicle_ownership(self):
        expense = add_expense(
            self.db, 1, 1,
            ExpenseCreate(
                amount="20.00",
                category="Parking",
                date="2026-11-09"
            )
        )

        with self.assertRaises(HTTPException) as result:
            get_expense(self.db, 2, expense.id)

        self.assertEqual(result.exception.status_code, 404)

        with self.assertRaises(HTTPException):
            delete_expense(self.db, 2, expense.id)

        with self.assertRaises(HTTPException):
            list_expenses(self.db, 2, 1)

        self.assertEqual(
            str(get_expense(self.db, 1, expense.id).amount),
            "20.00"
        )

    def test_invalid_expenses(self):
        with self.assertRaises(ValidationError):
            ExpenseCreate(
                amount="-10.00",
                category="Fuel",
                date="2026-11-09"
            )

        with self.assertRaises(ValidationError):
            ExpenseCreate(
                amount="10.00",
                category="   ",
                date="2026-11-09"
            )

        with self.assertRaises(ValidationError):
            ExpenseUpdate(amount=None)


if __name__ == "__main__":
    unittest.main()
