from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

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

    service_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    mileage: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )