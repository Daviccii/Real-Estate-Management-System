from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, constr, conint

from app.services.tour_service import parse_tour_url


class PropertyTourBase(BaseModel):
    title: Optional[constr(max_length=255)] = None
    url: constr(min_length=1, max_length=1000)
    thumbnail_url: Optional[constr(max_length=1000)] = None
    sort_order: Optional[conint(ge=0)] = 0

    @field_validator("url")
    @classmethod
    def _validate_tour_url(cls, value: str) -> str:
        # Raises ValueError -> FastAPI 422 with the message below.
        parse_tour_url(value)
        return value

    @field_validator("thumbnail_url")
    @classmethod
    def _validate_thumbnail(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.lower().startswith(("http://", "https://")):
            raise ValueError("Thumbnail must be an http(s) image URL")
        return value


class PropertyTourCreate(PropertyTourBase):
    pass


class PropertyTourUpdate(BaseModel):
    title: Optional[constr(max_length=255)] = None
    url: Optional[constr(min_length=1, max_length=1000)] = None
    thumbnail_url: Optional[constr(max_length=1000)] = None
    sort_order: Optional[conint(ge=0)] = None

    @field_validator("url")
    @classmethod
    def _validate_tour_url(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            parse_tour_url(value)
        return value

    @field_validator("thumbnail_url")
    @classmethod
    def _validate_thumbnail(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.lower().startswith(("http://", "https://")):
            raise ValueError("Thumbnail must be an http(s) image URL")
        return value


class PropertyTourOut(BaseModel):
    id: int
    property_id: int
    title: Optional[str] = None
    url: str
    provider: str
    embed_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
