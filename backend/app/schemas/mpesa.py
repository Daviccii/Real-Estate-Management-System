"""
Pydantic schemas for the M-Pesa (Safaricom Daraja) rent-collection integration.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from pydantic import ConfigDict, Field
from .base import ApiSchema


class MpesaStkPushRequest(ApiSchema):
    """Tenant-initiated STK push for an outstanding rent obligation."""
    payment_id: int
    phone_number: str = Field(min_length=9, max_length=20)
    amount: Decimal = Field(gt=0, description="Whole Kenyan shillings; may be partial")


class MpesaTransactionOut(ApiSchema):
    """Serializer output for one collection attempt (phone is always masked)."""
    id: int
    reference: str
    payment_id: int
    tenant_id: int
    lease_id: int
    property_id: int
    unit_id: int
    landlord_id: Optional[int] = None
    company_id: Optional[int] = None
    amount: str
    currency: str
    channel: str
    phone_number: str  # masked
    status: str
    result_code: Optional[int] = None
    result_description: Optional[str] = None
    failure_reason: Optional[str] = None
    merchant_request_id: Optional[str] = None
    checkout_request_id: Optional[str] = None
    mpesa_receipt_number: Optional[str] = None
    applied_to_payment: bool = False
    callback_attempts: int = 0
    # Refund totals for this collection (populated by list/detail views).
    refund_amount: Optional[str] = None
    refund_count: Optional[int] = None
    initiated_at: datetime
    callback_received_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reconciled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Display helpers (populated by the router serializer).
    property_name: Optional[str] = None
    unit_number: Optional[str] = None
    tenant_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MpesaConfigOut(ApiSchema):
    """Whether the integration is usable, for the frontend to gate the UI."""
    configured: bool
    environment: str
    production_enabled: bool
    missing: List[str] = []


class MpesaReconcileSummary(ApiSchema):
    checked: int
    updated: int
    still_processing: int
    errors: int


class MpesaRefundCreate(ApiSchema):
    """Landlord/admin record of a refund issued against a succeeded collection.

    The app does not move money (no Daraja B2C): the landlord performs the
    reversal through their own M-Pesa channel and records it here.
    """
    amount: Decimal = Field(gt=0, description="Whole Kenyan shillings; may be partial")
    reason: str = Field(min_length=3, max_length=500)
    reversal_reference: Optional[str] = Field(None, max_length=64)


class MpesaRefundOut(ApiSchema):
    id: int
    mpesa_transaction_id: int
    payment_id: Optional[int] = None
    amount: str
    currency: str
    reason: str
    reversal_reference: Optional[str] = None
    status: str
    recorded_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class MpesaRefundResult(ApiSchema):
    refund: MpesaRefundOut
    transaction: MpesaTransactionOut


class StkCallbackItem(ApiSchema):
    Name: str
    Value: Optional[Union[str, int, float]] = None


class StkCallbackMetadata(ApiSchema):
    Item: List[StkCallbackItem] = []


class StkCallback(ApiSchema):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[StkCallbackMetadata] = None


class StkCallbackBody(ApiSchema):
    stkCallback: StkCallback


class StkCallbackPayload(ApiSchema):
    """Exact envelope Daraja POSTs to MPESA_CALLBACK_URL."""
    Body: StkCallbackBody
