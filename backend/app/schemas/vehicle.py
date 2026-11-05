from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VehicleCreate(BaseModel):
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1886)
    mileage: int = Field(ge=0)
    vin: str | None = None
    license_plate: str | None = Field(default=None, max_length=20)

    @field_validator("vin")
    @classmethod
    def validate_vin(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None

        value = value.strip().upper()

        if len(value) != 17:
            raise ValueError("VIN must contain exactly 17 characters")

        if not value.isalnum() or any(c in value for c in "IOQ"):
            raise ValueError("VIN contains invalid characters")

        return value


class VehicleUpdate(BaseModel):
    make: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=1886)
    mileage: int | None = Field(default=None, ge=0)
    vin: str | None = None
    license_plate: str | None = Field(default=None, max_length=20)

    @field_validator("make", "model", "year", "mileage", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("Field cannot be null")
        return value

    @field_validator("vin")
    @classmethod
    def validate_vin(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None

        value = value.strip().upper()

        if len(value) != 17:
            raise ValueError("VIN must contain exactly 17 characters")

        if not value.isalnum() or any(c in value for c in "IOQ"):
            raise ValueError("VIN contains invalid characters")

        return value


class VehicleResponse(VehicleCreate):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)