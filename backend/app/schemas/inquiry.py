from pydantic import BaseModel, ConfigDict, constr
from typing import Optional
from datetime import datetime


class InquiryBase(BaseModel):
    message: constr(min_length=1, max_length=2000)
    status: Optional[str] = "pending"


class InquiryCreate(InquiryBase):
    property_id: int


class InquiryUpdate(BaseModel):
    message: Optional[constr(min_length=1, max_length=2000)] = None
    status: Optional[str] = None


class InquiryOut(BaseModel):
    id: int
    user_id: int
    property_id: int
    message: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)