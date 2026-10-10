"""
Payment management endpoints.
Supports payment tracking, invoicing, and financial overview with role-based authorization.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.utils.time import utc_now
# FIX: `func.cast(col, func.Float)` is invalid — func.Float is not a type,
# it's SQLAlchemy attempting to render a SQL function call named Float().
# Use the real `cast()` construct with the `Float` type instead.
from sqlalchemy import func, and_, or_, cast, Float

from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentOut, PaymentOverview
from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import verify_role, require_management, require_admin
from app.repositories.payment_repo import (
    create_payment,
    get_payment as repo_get_payment,
    list_payments as repo_list_payments,
    update_payment as repo_update_payment,
    delete_payment as repo_delete_payment,
)
from app.repositories.property_repo import get_property as repo_get_property
from app.repositories.lease_repo import get_lease as repo_get_lease
from app.repositories.user_repo import get_user as repo_get_user
from app.models import User, Property, Payment
from app.config.settings import settings
from app.services.audit_service import log_audit_event
from app.services.document_service import cached_pdf, generate_invoice_pdf
from app.services.payment_gateway_service import PaymentGatewayError, get_gateway
from app.services.security_events import emit_security_event

router = APIRouter(prefix="/payments", tags=["payments"])


def can_manage_payment(current_user: User, payment_property: Property) -> bool:
    """Check if user can manage a payment based on property ownership/management."""
    if (
        payment_property.company_id is not None
        and current_user.company_id != payment_property.company_id
    ):
        return False
    if verify_role(current_user, ["admin"]):
        return True
    if payment_property.owner_id == current_user.id:
        return True
    if payment_property.manager_id == current_user.id:
        return True
    return False


@router.post("/", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create(payment_in: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new payment/invoice. Only admins and managers can create payments."""
    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and managers can create payments"
        )

    lease = repo_get_lease(db, payment_in.lease_id)
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    property_obj = repo_get_property(db, payment_in.property_id)
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if not can_manage_payment(current_user, property_obj):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create payments for this property"
        )

    payment = create_payment(db, **payment_in.model_dump())
    return payment


@router.get("/", response_model=List[PaymentOut])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    property_id: Optional[int] = None,
    unit_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    lease_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List only authorized payments with database-level pagination."""
    authorized_user_id = None
    if verify_role(current_user, ["tenant"]):
        tenant_id = current_user.id
    elif verify_role(current_user, ["manager"]):
        authorized_user_id = current_user.id
    elif not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view payments")
    return repo_list_payments(
        db, skip=skip, limit=limit, property_id=property_id,
        unit_id=unit_id, tenant_id=tenant_id, lease_id=lease_id,
        status=status, authorized_user_id=authorized_user_id
    )


@router.get("/overview", response_model=PaymentOverview)
def payment_overview(
    property_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get financial overview statistics."""
    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view financial overview")

    query = db.query(Payment)
    if property_id:
        property_obj = repo_get_property(db, property_id)
        if not property_obj or not can_manage_payment(current_user, property_obj):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this property's financials")
        query = query.filter(Payment.property_id == property_id)
    elif not verify_role(current_user, ["admin"]):
        managed_properties = db.query(Property).filter(
            or_(
                Property.owner_id == current_user.id,
                Property.manager_id == current_user.id
            )
        ).all()
        managed_property_ids = [p.id for p in managed_properties]
        query = query.filter(Payment.property_id.in_(managed_property_ids))

    # FIX: use cast(Payment.amount, Float), not func.cast(Payment.amount, func.Float)
    total_collected = query.filter(Payment.status == "paid").with_entities(
        func.sum(cast(Payment.amount, Float))
    ).scalar() or 0

    outstanding_balance = query.filter(Payment.status.in_(["pending", "partially_paid"])).with_entities(
        func.sum(cast(Payment.amount, Float))
    ).scalar() or 0

    overdue_amount = query.filter(
        and_(
            Payment.status.in_(["pending", "partially_paid"]),
            Payment.due_date < utc_now()
        )
    ).with_entities(
        func.sum(cast(Payment.amount, Float))
    ).scalar() or 0

    total_revenue = query.with_entities(
        func.sum(cast(Payment.amount, Float))
    ).scalar() or 0

    pending_count = query.filter(Payment.status == "pending").count()
    paid_count = query.filter(Payment.status == "paid").count()
    overdue_count = query.filter(
        and_(
            Payment.status.in_(["pending", "partially_paid"]),
            Payment.due_date < utc_now()
        )
    ).count()

    return PaymentOverview(
        total_collected=str(total_collected),
        outstanding_balance=str(outstanding_balance),
        overdue_amount=str(overdue_amount),
        total_revenue=str(total_revenue),
        pending_payments=pending_count,
        paid_payments=paid_count,
        overdue_payments=overdue_count
    )


@router.get("/tenants/{tenant_id}/payments", response_model=List[PaymentOut])
def list_tenant_payments(
    tenant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all payments for a specific tenant."""
    if verify_role(current_user, ["tenant"]):
        if tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view other tenant's payments")
    elif not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view tenant payments")

    if verify_role(current_user, ["manager"]):
        return repo_list_payments(
            db, skip=skip, limit=limit, tenant_id=tenant_id, status=status,
            authorized_user_id=current_user.id
        )

    return repo_list_payments(db, skip=skip, limit=limit, tenant_id=tenant_id, status=status)


@router.get("/properties/{property_id}/payments", response_model=List[PaymentOut])
def list_property_payments(
    property_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all payments for a specific property."""
    property_obj = repo_get_property(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if not can_manage_payment(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view payments for this property")

    payments = repo_list_payments(db, skip=skip, limit=limit, property_id=property_id, status=status)
    return payments


@router.get("/leases/{lease_id}/payments", response_model=List[PaymentOut])
def list_lease_payments(
    lease_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all payments for a specific lease."""
    lease = repo_get_lease(db, lease_id)
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    if verify_role(current_user, ["tenant"]):
        if lease.tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view payments for this lease")
    elif not verify_role(current_user, ["admin"]):
        property_obj = repo_get_property(db, lease.property_id)
        if not property_obj or not can_manage_payment(current_user, property_obj):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view payments for this lease")

    payments = repo_list_payments(db, skip=skip, limit=limit, lease_id=lease_id, status=status)
    return payments


@router.get("/{payment_id}", response_model=PaymentOut)
def read(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get payment details by ID."""
    payment = repo_get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if verify_role(current_user, ["tenant"]):
        if payment.tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment")
    elif not verify_role(current_user, ["admin"]):
        property_obj = repo_get_property(db, payment.property_id)
        if not property_obj or not can_manage_payment(current_user, property_obj):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment")

    return payment


@router.get("/{payment_id}/invoice")
def download_invoice(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Download the payment invoice as a PDF."""
    payment = repo_get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if verify_role(current_user, ["tenant"]):
        if payment.tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment")
    elif not verify_role(current_user, ["admin"]):
        property_obj = repo_get_property(db, payment.property_id)
        if not property_obj or not can_manage_payment(current_user, property_obj):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment")

    tenant = repo_get_user(db, payment.tenant_id)
    property_obj = repo_get_property(db, payment.property_id)
    path = cached_pdf(
        "invoice", payment.id, payment.updated_at,
        lambda: generate_invoice_pdf(payment, tenant, property_obj),
    )
    return Response(
        content=path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice-{payment.id}.pdf"'},
    )


@router.put("/{payment_id}", response_model=PaymentOut)
def update(payment_id: int, payment_in: PaymentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update payment details (status, payment date, etc.)."""
    payment = repo_get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify payments")

    property_obj = repo_get_property(db, payment.property_id)
    if not property_obj or not can_manage_payment(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this payment")

    updated = repo_update_payment(db, payment, **payment_in.model_dump(exclude_none=True))
    return updated


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a payment (admin only)."""
    if not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete payments")

    payment = repo_get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    db.delete(payment)
    db.commit()
    return None


@router.post("/{payment_id}/gateway/charge")
def create_gateway_charge(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Open a charge for this payment with the configured gateway."""
    payment = repo_get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify payments")

    property_obj = repo_get_property(db, payment.property_id)
    if not property_obj or not can_manage_payment(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this payment")

    if payment.status == "paid":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment is already marked paid")

    try:
        gateway = get_gateway()
        charge = gateway.create_charge(amount=payment.amount, currency="USD", reference=f"payment:{payment.id}")
    except PaymentGatewayError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    payment.reference = charge["provider_txn_id"]
    payment.payment_method = gateway.name
    db.commit()
    db.refresh(payment)
    log_audit_event(
        db,
        current_user.id,
        "PAYMENT_CHARGE_CREATED",
        entity_type="payment",
        entity_id=payment.id,
        details={"provider": gateway.name, "provider_txn_id": charge["provider_txn_id"]},
    )
    return {"provider": gateway.name, "provider_txn_id": charge["provider_txn_id"], "status": payment.status}


@router.post("/webhooks/{provider}")
async def gateway_webhook(provider: str, request: Request, db: Session = Depends(get_db)):
    """
    Gateway webhook ingestion (unauthenticated; signature-verified).

    Marks the matching payment paid/failed based on the verified event.
    Always returns 200 after signature verification so providers stop retrying;
    unmatched events report matched=false instead of erroring.
    """
    raw_body = await request.body()
    try:
        gateway = get_gateway()
    except PaymentGatewayError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    if provider != gateway.name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown payment provider")

    if not gateway.verify_signature(raw_body, request.headers.get("X-Webhook-Signature")):
        emit_security_event(
            "payment.webhook.bad_signature",
            request=request,
            outcome="denied",
            details={"provider": provider},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    try:
        event = gateway.parse_event(json.loads(raw_body))
    except (ValueError, PaymentGatewayError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed webhook payload")

    provider_txn_id = event.get("provider_txn_id")
    payment = (
        db.query(Payment).filter(Payment.reference == provider_txn_id).first()
        if provider_txn_id
        else None
    )
    if payment is None:
        return {"received": True, "matched": False}

    applied = False
    if event.get("type") == "payment.succeeded" and payment.status != "paid":
        payment.status = "paid"
        payment.payment_date = utc_now()
        applied = True
    elif event.get("type") == "payment.failed" and payment.status not in ("paid", "failed"):
        payment.status = "failed"
        applied = True

    if applied:
        db.commit()
    log_audit_event(
        db,
        None,
        "PAYMENT_WEBHOOK_APPLIED" if applied else "PAYMENT_WEBHOOK_IGNORED",
        entity_type="payment",
        entity_id=payment.id,
        details={"provider": provider, "event_id": event.get("event_id"), "type": event.get("type")},
    )
    return {"received": True, "matched": True, "applied": applied}
