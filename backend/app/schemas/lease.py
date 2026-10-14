from pydantic import ConfigDict
from .base import ApiSchema
from typing import Optional
from datetime import datetime


class LeaseBase(ApiSchema):
    tenant_id: int
    unit_id: int
    property_id: int
    start_date: datetime
    end_date: datetime
    rent_amount: str
    deposit: Optional[str] = None
    payment_due_date: Optional[int] = None  # Day of month (1-31)
    status: str = "draft"
    notes: Optional[str] = None


class LeaseCreate(LeaseBase):
    pass


class LeaseUpdate(ApiSchema):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    rent_amount: Optional[str] = None
    deposit: Optional[str] = None
    payment_due_date: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeaseRenew(ApiSchema):
    new_end_date: datetime
    new_rent_amount: Optional[str] = None
    notes: Optional[str] = None


class LeaseTerminate(ApiSchema):
    termination_date: datetime
    reason: Optional[str] = None
    notes: Optional[str] = None


class LeaseOut(LeaseBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)