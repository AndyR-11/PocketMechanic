"""
Contract 23: CalculateNextDue (Strategy design pattern).

Bridging technique: PPP. Each comment below is a line of the
pseudocode in the SDD that was written before the code.
"""

import calendar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_schedule import MaintenanceSchedule


@dataclass
class Baseline:
    service_date: date
    mileage: int
    from_record: bool


@dataclass
class NextDue:
    baseline: Baseline
    due_mileage: int | None
    due_date: date | None


def normalize_service_type(value: str) -> str:
    return " ".join(value.split()).lower()


def find_baseline(db: Session, schedule: MaintenanceSchedule) -> Baseline:
    # find the newest maintenance record on the schedule's vehicle
    #     whose service type matches the schedule's (ignoring case and spaces)
    records = db.scalars(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.vehicle_id == schedule.vehicle_id)
        .order_by(
            MaintenanceRecord.service_date.desc(),
            MaintenanceRecord.mileage.desc(),
            MaintenanceRecord.id.desc()
        )
    ).all()
    wanted = normalize_service_type(schedule.service_type)
    newest = next(
        (r for r in records
         if normalize_service_type(r.service_type) == wanted),
        None
    )

    # if a record is found
    #     return its service date and mileage
    if newest is not None:
        return Baseline(newest.service_date, newest.mileage, True)

    # otherwise
    #     return the schedule's start date and start mileage
    return Baseline(schedule.start_date, schedule.start_mileage, False)


def add_months(start: date, months: int) -> date:
    # add the interval in months to the baseline date
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1

    # if that day does not exist in the new month (for example Jan 31 + 1 month)
    #     use the last day of that month
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(start.day, last_day))


class DueStrategy(ABC):
    """Calculates one kind of due point for a schedule."""

    @abstractmethod
    def calculate(self, schedule: MaintenanceSchedule, baseline: Baseline):
        ...


class MileageDueStrategy(DueStrategy):
    def calculate(self, schedule, baseline) -> int | None:
        # if the schedule has no mileage interval
        #     return nothing
        if schedule.interval_miles is None:
            return None
        # return baseline mileage + mileage interval
        return baseline.mileage + schedule.interval_miles


class TimeDueStrategy(DueStrategy):
    def calculate(self, schedule, baseline) -> date | None:
        # if the schedule has no time interval
        #     return nothing
        if schedule.interval_months is None:
            return None
        # return the new date
        return add_months(baseline.service_date, schedule.interval_months)


MILEAGE_STRATEGY = MileageDueStrategy()
TIME_STRATEGY = TimeDueStrategy()


def calculate_next_due(
    db: Session, schedule: MaintenanceSchedule
) -> NextDue:
    baseline = find_baseline(db, schedule)
    return NextDue(
        baseline=baseline,
        due_mileage=MILEAGE_STRATEGY.calculate(schedule, baseline),
        due_date=TIME_STRATEGY.calculate(schedule, baseline)
    )
