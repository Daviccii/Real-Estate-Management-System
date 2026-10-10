from pydantic import AliasChoices, BaseModel, ConfigDict, Field, constr, conint
from typing import Dict, Optional, Literal, List
from datetime import datetime

PropertyPurpose = Literal["buy", "rent", "invest"]


class PropertyBase(BaseModel):
    name: constr(min_length=1, max_length=255)
    property_type: Optional[constr(max_length=100)] = None
    description: Optional[str] = None
    address: Optional[constr(max_length=500)] = None
    city: Optional[constr(max_length=200)] = None
    county: Optional[constr(max_length=200)] = None
    sub_location: Optional[constr(max_length=200)] = None
    country: Optional[constr(max_length=100)] = None
    status: Optional[constr(max_length=50)] = "active"
    units_count: Optional[conint(ge=0)] = 1
    price: Optional[constr(max_length=100)] = None
    price_label: Optional[constr(max_length=100)] = None
    bedrooms: Optional[conint(ge=0)] = None
    bathrooms: Optional[conint(ge=0)] = None
    area: Optional[constr(max_length=100)] = None
    image_url: Optional[constr(max_length=500)] = None
    gallery_urls: Optional[str] = None
    showroom_url: Optional[constr(max_length=500)] = None
    construction_status: Optional[constr(max_length=50)] = "completed"
    completion_date: Optional[datetime] = None
    planned_finish_description: Optional[str] = None
    planned_finish_image_url: Optional[constr(max_length=500)] = None
    deposit: Optional[constr(max_length=100)] = None
    lease_term: Optional[constr(max_length=100)] = None
    availability_date: Optional[datetime] = None
    amenities: Optional[str] = None
    furnishing: Optional[str] = None
    parking_spaces: Optional[int] = 0
    is_verified: Optional[bool] = False
    allow_direct_contact: Optional[bool] = False
    source_id: Optional[int] = None
    source_type: Optional[str] = "PROP_NOXA_VERIFIED"
    source_name: Optional[str] = None
    source_reference: Optional[str] = None
    verification_status: Optional[str] = "PENDING_VERIFICATION"
    last_verified_at: Optional[datetime] = None
    listing_status: Optional[str] = "ACTIVE"
    is_demo: Optional[bool] = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark: Optional[str] = None
    building_id: Optional[int] = None
    agent_id: Optional[int] = None
    manager_id: Optional[int] = None


class PropertyCreate(PropertyBase):
    purpose: Optional[PropertyPurpose] = "rent"


class PropertyUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=255)] = None
    property_type: Optional[constr(max_length=100)] = None
    description: Optional[str] = None
    address: Optional[constr(max_length=500)] = None
    city: Optional[constr(max_length=200)] = None
    county: Optional[constr(max_length=200)] = None
    sub_location: Optional[constr(max_length=200)] = None
    country: Optional[constr(max_length=100)] = None
    status: Optional[constr(max_length=50)] = None
    units_count: Optional[conint(ge=0)] = None
    price: Optional[constr(max_length=100)] = None
    price_label: Optional[constr(max_length=100)] = None
    bedrooms: Optional[conint(ge=0)] = None
    bathrooms: Optional[conint(ge=0)] = None
    area: Optional[constr(max_length=100)] = None
    image_url: Optional[constr(max_length=500)] = None
    gallery_urls: Optional[str] = None
    showroom_url: Optional[constr(max_length=500)] = None
    construction_status: Optional[constr(max_length=50)] = None
    completion_date: Optional[datetime] = None
    planned_finish_description: Optional[str] = None
    planned_finish_image_url: Optional[constr(max_length=500)] = None
    purpose: Optional[PropertyPurpose] = None
    deposit: Optional[constr(max_length=100)] = None
    lease_term: Optional[constr(max_length=100)] = None
    availability_date: Optional[datetime] = None
    amenities: Optional[str] = None
    furnishing: Optional[str] = None
    parking_spaces: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark: Optional[str] = None
    building_id: Optional[int] = None
    is_verified: Optional[bool] = None
    allow_direct_contact: Optional[bool] = None
    source_id: Optional[int] = None
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    source_reference: Optional[str] = None
    verification_status: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    listing_status: Optional[str] = None
    is_demo: Optional[bool] = None


class BuildingSummary(BaseModel):
    id: int
    name: str
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
    year_built: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PropertyMediaOut(BaseModel):
    id: int
    url: str
    media_type: str
    source_type: str
    source_name: Optional[str] = None
    license_reference: Optional[str] = None
    caption: Optional[str] = None
    is_primary: bool
    is_public: bool

    model_config = ConfigDict(from_attributes=True)


class PropertyOut(PropertyBase):
    id: int
    owner_id: int
    purpose: Optional[str] = None
    building_name: Optional[str] = None
    building: Optional[BuildingSummary] = None
    media: List[PropertyMediaOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PropertyMatchRequest(BaseModel):
    # Accept both the current field names and the legacy aliases earlier
    # clients posted (city / max_price / location were silently dropped
    # before because they were not schema fields).
    max_budget: Optional[float] = Field(
        default=None, validation_alias=AliasChoices("max_budget", "max_price")
    )
    preferred_city: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("preferred_city", "city", "location")
    )
    min_bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    purpose: Optional[str] = None
    household_size: Optional[int] = None
    require_parking: Optional[bool] = None
    require_security: Optional[bool] = None
    require_balcony: Optional[bool] = None
    furnishing: Optional[str] = None
    amenities: Optional[List[str]] = None


class PropertyMatchResult(BaseModel):
    property: PropertyOut
    match_score: int
    match_label: str = "Possible match"
    match_reasons: List[str]
    score_breakdown: Dict[str, int] = {}
