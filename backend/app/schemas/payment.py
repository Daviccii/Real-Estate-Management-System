from pydantic import ConfigDict
from .base import ApiSchema
from typing import Optional
from datetime import datetime


class PaymentBase(ApiSchema):
    tenant_id: int
    lease_id: int
    property_id: int
    unit_id: int
    amount: str
    due_date: datetime
    payment_type: Optional[str] = None
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    status: str = "pending"
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(ApiSchema):
    amount: Optional[str] = None
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    status: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentOut(PaymentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentOverview(ApiSchema):
    total_collected: str
    outstanding_balance: str
    overdue_amount: str
    total_revenue: str
    pending_payments: int
    paid_payments: int
    overdue_payments: int