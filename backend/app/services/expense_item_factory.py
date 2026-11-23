from app.models.expense import Expense
from app.models.vehicle import Vehicle


class ExpenseItemFactory:
    """Builds expense overview rows (Factory design pattern)."""

    @staticmethod
    def create_overview_item(expense: Expense, vehicle: Vehicle) -> dict:
        is_maintenance = (
            expense.source_maintenance_id is not None
        )

        return {
            "id": expense.id,
            "vehicle_id": expense.vehicle_id,
            "amount": expense.amount,
            "category": expense.category,
            "date": expense.date,
            "notes": expense.notes,
            "source": (
                "maintenance" if is_maintenance else "manual"
            ),
            "maintenance_id": expense.source_maintenance_id,
            "vehicle": ExpenseItemFactory.create_vehicle_summary(vehicle)
        }

    @staticmethod
    def create_vehicle_summary(vehicle: Vehicle) -> dict:
        return {
            "id": vehicle.id,
            "year": vehicle.year,
            "make": vehicle.make,
            "model": vehicle.model
        }