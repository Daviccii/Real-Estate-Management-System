"""
M-Pesa (Safaricom Daraja) rent-collection endpoints.

Flow: tenant initiates an STK push against their own outstanding rent
obligation -> Safaricom prompts the phone -> the result arrives at the public
`/mpesa/callback` endpoint -> the backend validates and applies it exactly
once -> the frontend polls `GET /mpesa/transactions/{id}` for the
authoritative status. A 200 from initiation is only "prompt sent", never
proof of payment.

Authorization mirrors the payments module: tenants act on their own records,
landlords/managers on properties they manage (via can_manage_payment), and
admins everywhere. The callback is unauthenticated by necessity but grants
no data access: it only matches an existing pending checkout and applies a
structurally valid result.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.roles import require_admin, verify_role
from app.config.settings import settings
from app.database.database import get_db
from app.models import MpesaTransaction, MpesaRefund, Property, User
from app.repositories.payment_repo import get_payment as repo_get_payment
from app.routers.payments import can_manage_payment
from app.schemas.mpesa import (
    MpesaConfigOut,
    MpesaReconcileSummary,
    MpesaRefundCreate,
    MpesaRefundOut,
    MpesaRefundResult,
    MpesaStkPushRequest,
    MpesaTransactionOut,
)
from app.services import mpesa_service
from app.services.mpesa_service import (
    MpesaCallbackError,
    MpesaConfigError,
    MpesaDuplicateRequest,
    MpesaPaymentNotEligible,
    MpesaRequestError,
    MpesaUnconfirmed,
    MpesaValidationError,
    record_refund,
    serialize_refund,
)
from app.services.security_events import emit_security_event
from app.utils.pagination import LimitParam, SkipParam

router = APIRouter(prefix="/mpesa", tags=["mpesa"])


def _txn_or_404(db: Session, txn_id: int) -> MpesaTransaction:
    txn = db.query(MpesaTransaction).filter(MpesaTransaction.id == txn_id).first()
    if txn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="M-Pesa transaction not found")
    return txn


def _ensure_can_view(current_user: User, txn: MpesaTransaction, db: Session) -> None:
    if verify_role(current_user, ["admin"]):
        return
    if txn.tenant_id == current_user.id:
        return
    prop = txn.property or db.query(Property).filter(Property.id == txn.property_id).first()
    if prop is not None and can_manage_payment(current_user, prop):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to view this M-Pesa transaction",
    )


@router.get("/config", response_model=MpesaConfigOut)
def get_mpesa_config(current_user: User = Depends(get_current_user)):
    """Whether the M-Pesa integration is usable (no secrets exposed)."""
    return MpesaConfigOut(**mpesa_service.mpesa_config_status())


@router.post("/stk-push", response_model=MpesaTransactionOut)
def initiate_stk_push(
    payload: MpesaStkPushRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send an M-Pesa Express (STK) prompt for an outstanding rent obligation."""
    if not mpesa_service.allow_mpesa_action(
        current_user.id, "initiate", settings.MPESA_INITIATE_LIMIT_PER_HOUR
    ):
        emit_security_event(
            "mpesa.initiate.rate_limited",
            user_id=current_user.id,
            outcome="denied",
            details={"limit_per_hour": settings.MPESA_INITIATE_LIMIT_PER_HOUR},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many M-Pesa requests. Please wait a little before trying again.",
        )

    payment = repo_get_payment(db, payload.payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    prop = payment.property or db.query(Property).filter(Property.id == payment.property_id).first()
    authorized = (
        verify_role(current_user, ["admin"])
        or payment.tenant_id == current_user.id
        or (prop is not None and can_manage_payment(current_user, prop))
    )
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pay this rent obligation",
        )

    try:
        txn = mpesa_service.initiate_stk_push(
            db,
            payment=payment,
            tenant_id=payment.tenant_id,
            phone_number=payload.phone_number,
            amount=payload.amount,
            actor_id=current_user.id,
        )
    except MpesaConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except MpesaValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except MpesaPaymentNotEligible as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except MpesaDuplicateRequest as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "transaction": mpesa_service.serialize_transaction(exc.transaction),
            },
        )
    except MpesaUnconfirmed as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(exc), "transaction_id": exc.transaction.id,
                    "transaction": mpesa_service.serialize_transaction(exc.transaction)},
        )
    except MpesaRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": str(exc),
                "transaction_id": exc.transaction.id if exc.transaction else None,
                "transaction": (
                    mpesa_service.serialize_transaction(exc.transaction)
                    if exc.transaction
                    else None
                ),
            },
        )

    return mpesa_service.serialize_transaction(txn)


@router.get("/transactions", response_model=list[MpesaTransactionOut])
def list_transactions(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    payment_id: Optional[int] = None,
    property_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Role-scoped M-Pesa collection history (phone numbers always masked)."""
    query = db.query(MpesaTransaction)

    if verify_role(current_user, ["admin"]):
        if tenant_id is not None:
            query = query.filter(MpesaTransaction.tenant_id == tenant_id)
        if property_id is not None:
            query = query.filter(MpesaTransaction.property_id == property_id)
    elif verify_role(current_user, ["manager", "owner"]):
        managed = db.query(Property.id).filter(
            or_(
                Property.owner_id == current_user.id,
                Property.manager_id == current_user.id,
            )
        )
        query = query.filter(MpesaTransaction.property_id.in_(managed))
        if property_id is not None:
            query = query.filter(MpesaTransaction.property_id == property_id)
        if tenant_id is not None:
            query = query.filter(MpesaTransaction.tenant_id == tenant_id)
    elif verify_role(current_user, ["tenant", "user"]):
        query = query.filter(MpesaTransaction.tenant_id == current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view M-Pesa transactions",
        )

    if status_filter:
        query = query.filter(MpesaTransaction.status == status_filter)
    if payment_id is not None:
        query = query.filter(MpesaTransaction.payment_id == payment_id)

    rows = (
        query.order_by(MpesaTransaction.id.desc()).offset(skip).limit(limit).all()
    )
    return [mpesa_service.serialize_transaction(row) for row in rows]


@router.get("/transactions/{txn_id}", response_model=MpesaTransactionOut)
def get_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Authoritative status for one collection attempt (frontend polling target)."""
    txn = _txn_or_404(db, txn_id)
    _ensure_can_view(current_user, txn, db)
    return mpesa_service.serialize_transaction(txn)


@router.post("/transactions/{txn_id}/reconcile", response_model=MpesaTransactionOut)
def reconcile_one(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm one attempt's true status with Safaricom's STK Push Query API."""
    if not mpesa_service.allow_mpesa_action(current_user.id, "reconcile", 30):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many status checks. Please wait a little before trying again.",
        )

    txn = _txn_or_404(db, txn_id)
    _ensure_can_view(current_user, txn, db)

    try:
        mpesa_service.reconcile_transaction(db, txn, actor_id=current_user.id)
    except MpesaConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except MpesaRequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    db.refresh(txn)
    return mpesa_service.serialize_transaction(txn)


@router.post("/reconcile", response_model=MpesaReconcileSummary)
def reconcile_bulk(
    older_than_minutes: int = Query(2, ge=1, le=1440),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin sweep: query Daraja for every stale live transaction."""
    try:
        return MpesaReconcileSummary(
            **mpesa_service.reconcile_stale_transactions(
                db, older_than_minutes=older_than_minutes, limit=limit
            )
        )
    except MpesaConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/transactions/{txn_id}/refunds", response_model=MpesaRefundResult)
def create_refund(
    txn_id: int,
    payload: MpesaRefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record a refund against a succeeded M-Pesa collection.

    The app does not move money (no Daraja B2C): the landlord performs the
    reversal through their own M-Pesa channel and records it here with the
    reversal_reference from their M-Pesa statement.

    Available to admin, owner, and manager roles who can manage the payment.
    """
    # Verify user has appropriate role
    if not verify_role(current_user, ["admin", "owner", "manager"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, owners, and managers can record refunds"
        )

    # Get the transaction
    txn = _txn_or_404(db, txn_id)

    # Verify user can manage this transaction's payment
    prop = txn.property or db.query(Property).filter(Property.id == txn.property_id).first()
    if prop is not None and not can_manage_payment(current_user, prop):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to record refunds for this transaction"
        )

    try:
        refund = record_refund(
            db,
            mpesa_transaction_id=txn_id,
            amount=payload.amount,
            reason=payload.reason,
            reversal_reference=payload.reversal_reference,
            recorded_by=current_user.id,
        )
    except MpesaValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except MpesaPaymentNotEligible as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    # Return both the refund and the updated transaction
    db.refresh(txn)
    return MpesaRefundResult(
        refund=serialize_refund(refund),
        transaction=mpesa_service.serialize_transaction(txn),
    )


@router.post("/callback")
async def mpesa_callback(payload: dict, request: Request, db: Session = Depends(get_db)):
    """
    Public Safaricom callback. Reaching this URL proves nothing on its own:
    the payload must match an existing pending checkout, and applying the
    result is idempotent (exactly-once crediting).
    """
    try:
        result = mpesa_service.process_callback(db, payload)
    except MpesaCallbackError:
        emit_security_event(
            "mpesa.callback.malformed",
            request=request,
            outcome="denied",
            details={"source": "daraja"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed callback payload"
        )

    return {
        "ResultCode": 0,
        "ResultDesc": "Callback received",
        "matched": result["matched"],
        "applied": result["applied"],
        "enriched": result.get("enriched", False),
        "status": result["status"],
    }
