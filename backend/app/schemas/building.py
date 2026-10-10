from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class BuildingBase(BaseModel):
    property_id: Optional[int] = None
    name: str
    building_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    sub_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark: Optional[str] = None
    image_url: Optional[str] = None
    total_floors: Optional[int] = 1
    units_count: Optional[int] = 0
    amenities: Optional[str] = None
    year_built: Optional[int] = None
    description: Optional[str] = None


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    building_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    sub_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark: Optional[str] = None
    image_url: Optional[str] = None
    total_floors: Optional[int] = None
    units_count: Optional[int] = None
    amenities: Optional[str] = None
    year_built: Optional[int] = None
    description: Optional[str] = None


class BuildingOut(BuildingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    property_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

