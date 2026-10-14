from pydantic import ConfigDict, constr
from .base import ApiSchema
from typing import Optional
from datetime import datetime


class InquiryBase(ApiSchema):
    message: constr(min_length=1, max_length=2000)
    status: Optional[str] = "pending"


class InquiryCreate(InquiryBase):
    property_id: int


class InquiryUpdate(ApiSchema):
    message: Optional[constr(min_length=1, max_length=2000)] = None
    status: Optional[str] = None


class InquiryOut(ApiSchema):
    id: int
    user_id: int
    property_id: int
    message: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)