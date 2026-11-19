from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False
    )

    service_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    interval_miles: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    interval_months: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # Used as the baseline until a matching maintenance record exists.
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    start_mileage: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
