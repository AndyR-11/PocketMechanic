import os
import unittest
from datetime import date, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.expense import Expense
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.due_strategy import (
    Baseline,
    MileageDueStrategy,
    TimeDueStrategy,
    add_months,
    calculate_next_due
)
from app.services.schedule_service import (
    add_schedule,
    delete_schedule,
    list_all_schedules,
    get_schedule,
    list_schedules,
    update_schedule
)


class DueStrategyTests(unittest.TestCase):
    """Contract 23: CalculateNextDue (PPP example)."""

    def schedule(self, miles=None, months=None):
        return MaintenanceSchedule(
            vehicle_id=1, service_type="Oil Change",
            interval_miles=miles, interval_months=months,
            start_date=date(2026, 1, 1), start_mileage=0
        )

    def test_mileage_strategy_adds_interval(self):
        baseline = Baseline(date(2026, 5, 1), 10000, True)
        self.assertEqual(
            MileageDueStrategy().calculate(self.schedule(miles=5000), baseline),
            15000
        )

    def test_mileage_strategy_without_interval(self):
        baseline = Baseline(date(2026, 5, 1), 10000, True)
        self.assertIsNone(
            MileageDueStrategy().calculate(self.schedule(months=6), baseline)
        )

    def test_time_strategy_adds_months(self):
        baseline = Baseline(date(2026, 5, 1), 10000, True)
        self.assertEqual(
            TimeDueStrategy().calculate(self.schedule(months=6), baseline),
            date(2026, 11, 1)
        )

    def test_short_month_uses_last_day(self):
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(add_months(date(2027, 12, 31), 2), date(2028, 2, 29))

    def test_months_roll_into_next_year(self):
        self.assertEqual(add_months(date(2026, 11, 15), 3), date(2027, 2, 15))


class ScheduleServiceTests(unittest.TestCase):
    """Contracts 19-22 (Design by Contract)."""

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
                    year=2025, mileage=20000),
            Vehicle(user_id=2, make="Honda", model="Civic",
                    year=2022, mileage=5000)
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def add_record(self, service_type, service_date, mileage):
        self.db.add(MaintenanceRecord(
            vehicle_id=1, service_type=service_type,
            service_date=service_date, mileage=mileage
        ))
        self.db.commit()

    def test_add_schedule_uses_vehicle_mileage_and_today(self):
        schedule = add_schedule(self.db, 1, 1, ScheduleCreate(
            service_type="  Oil   Change ", interval_miles=5000
        ))
        self.assertEqual(schedule.service_type, "Oil Change")
        self.assertEqual(schedule.start_mileage, 20000)
        self.assertEqual(schedule.start_date, date.today())
        due = calculate_next_due(self.db, schedule)
        self.assertFalse(due.baseline.from_record)
        self.assertEqual(due.due_mileage, 25000)

    def test_needs_at_least_one_interval(self):
        with self.assertRaises(ValidationError):
            ScheduleCreate(service_type="Oil Change")
        with self.assertRaises(ValidationError):
            ScheduleUpdate(interval_miles=None, interval_months=None)

    def test_interval_limits(self):
        for bad in ({"interval_miles": 0}, {"interval_miles": 100001},
                    {"interval_months": 0}, {"interval_months": 121}):
            with self.assertRaises(ValidationError):
                ScheduleCreate(service_type="Oil Change", **bad)
        ScheduleCreate(service_type="Oil Change",
                       interval_miles=100000, interval_months=120)

    def test_blank_service_type_rejected(self):
        with self.assertRaises(ValidationError):
            ScheduleCreate(service_type="   ", interval_miles=5000)

    def test_duplicate_service_type_rejected(self):
        add_schedule(self.db, 1, 1, ScheduleCreate(
            service_type="Oil Change", interval_miles=5000))
        with self.assertRaises(HTTPException) as error:
            add_schedule(self.db, 1, 1, ScheduleCreate(
                service_type="oil change", interval_months=6))
        self.assertEqual(error.exception.status_code, 409)

    def test_newest_matching_record_is_baseline(self):
        self.add_record("Oil Change", date(2026, 1, 10), 10000)
        self.add_record("oil  change", date(2026, 6, 10), 14000)
        self.add_record("Tire Rotation", date(2026, 8, 1), 16000)
        schedule = add_schedule(self.db, 1, 1, ScheduleCreate(
            service_type="Oil Change", interval_miles=5000, interval_months=6))
        due = calculate_next_due(self.db, schedule)
        self.assertTrue(due.baseline.from_record)
        self.assertEqual(due.due_mileage, 19000)
        self.assertEqual(due.due_date, date(2026, 12, 10))

    def test_update_replaces_both_intervals(self):
        schedule = add_schedule(self.db, 1, 1, ScheduleCreate(
            service_type="Oil Change", interval_miles=5000, interval_months=6))
        update_schedule(self.db, 1, schedule.id,
                        ScheduleUpdate(interval_miles=None, interval_months=12))
        schedule = get_schedule(self.db, 1, schedule.id)
        self.assertIsNone(schedule.interval_miles)
        self.assertEqual(schedule.interval_months, 12)

    def test_other_user_cannot_access(self):
        schedule = add_schedule(self.db, 1, 1, ScheduleCreate(
            service_type="Oil Change", interval_miles=5000))
        for call in (
            lambda: get_schedule(self.db, 2, schedule.id),
            lambda: update_schedule(self.db, 2, schedule.id,
                                    ScheduleUpdate(interval_miles=1)),
            lambda: delete_schedule(self.db, 2, schedule.id),
            lambda: list_schedules(self.db, 2, 1),
            lambda: add_schedule(self.db, 2, 1, ScheduleCreate(
                service_type="Brakes", interval_miles=1))
        ):
            with self.assertRaises(HTTPException) as error:
                call()
            self.assertEqual(error.exception.status_code, 404)

    def test_list_all_schedules_for_user(self):
        self.db.add(Vehicle(user_id=1, make="Ford", model="F-150",
                            year=2020, mileage=1000))
        self.db.commit()
        add_schedule(self.db, 1, 1, ScheduleCreate(
            service_type="Oil Change", interval_miles=5000))
        add_schedule(self.db, 1, 3, ScheduleCreate(
            service_type="Tire Rotation", interval_months=6))
        add_schedule(self.db, 2, 2, ScheduleCreate(
            service_type="Other User", interval_miles=1))

        rows = list_all_schedules(self.db, 1)
        self.assertEqual(
            sorted(s.service_type for s, v in rows),
            ["Oil Change", "Tire Rotation"]
        )
        self.assertTrue(all(v.user_id == 1 for s, v in rows))

        rows = list_all_schedules(self.db, 1, 3)
        self.assertEqual([s.service_type for s, v in rows], ["Tire Rotation"])

        with self.assertRaises(HTTPException) as error:
            list_all_schedules(self.db, 1, 2)
        self.assertEqual(error.exception.status_code, 404)

    def test_delete_schedule(self):
        schedule = add_schedule(self.db, 1, 1, ScheduleCreate(
            service_type="Oil Change", interval_miles=5000))
        delete_schedule(self.db, 1, schedule.id)
        self.assertEqual(list_schedules(self.db, 1, 1), [])


if __name__ == "__main__":
    unittest.main()
