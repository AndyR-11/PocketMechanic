from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.vehicle import Vehicle
from app.services.vehicle_service import get_vehicle

MAINTENANCE_CATEGORY = "Maintenance"


def get_cost_summary(
    db: Session, user_id: int, vehicle_id: int | None = None
) -> dict:
    # Contract 25: GetCostSummary
    # Precondition: if a vehicle is given, it belongs to the user.
    if vehicle_id is not None:
        get_vehicle(db, user_id, vehicle_id)

    query = (
        select(Expense)
        .join(Vehicle, Expense.vehicle_id == Vehicle.id)
        .where(Vehicle.user_id == user_id)
    )
    if vehicle_id is not None:
        query = query.where(Expense.vehicle_id == vehicle_id)

    expenses = db.scalars(query).all()

    total = Decimal("0.00")
    by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    by_month: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    counts: dict[str, int] = defaultdict(int)

    for expense in expenses:
        amount = Decimal(expense.amount)
        total += amount

        # Linked maintenance expenses are grouped under one category.
        category = (
            MAINTENANCE_CATEGORY
            if expense.source_maintenance_id is not None
            else expense.category
        )
        by_category[category] += amount
        counts[category] += 1
        by_month[expense.date.strftime("%Y-%m")] += amount

    # Postcondition: every group adds up to the total.
    return {
        "total": total,
        "count": len(expenses),
        "by_category": sorted(
            (
                {"category": c, "total": t, "count": counts[c]}
                for c, t in by_category.items()
            ),
            key=lambda g: (-g["total"], g["category"])
        ),
        "by_month": [
            {"month": m, "total": by_month[m]}
            for m in sorted(by_month)
        ]
    }
