from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    make: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    model: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    year: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    mileage: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    vin: Mapped[str | None] = mapped_column(
        String(17), nullable=True
    )

    license_plate: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )