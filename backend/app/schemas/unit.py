from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class UnitBase(BaseModel):
    property_id: int
    unit_number: str
    unit_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[str] = None
    rent: Optional[str] = None
    status: str = "available"
    availability_date: Optional[datetime] = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    unit_number: Optional[str] = None
    unit_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[str] = None
    rent: Optional[str] = None
    status: Optional[str] = None
    availability_date: Optional[datetime] = None


class UnitOut(UnitBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)