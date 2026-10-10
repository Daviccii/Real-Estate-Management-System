from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import require_user
from app.models.lease import Lease
from app.models.property import Property
from app.models.unit import Unit
from app.models.payment import Payment
from app.models.maintenance import Maintenance
from app.models.user import User

router = APIRouter(prefix="/tenant", tags=["tenant"])


from app.models.application import RentalApplication


@router.get("/dashboard")
def get_tenant_dashboard(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns Tenant dashboard metrics: active lease, property info, rent status, open maintenance tickets, and applications.
    """
    tenant_id = current_user.id
    
    # Active lease
    active_lease = db.query(Lease).filter(
        Lease.tenant_id == tenant_id,
        Lease.status == "active"
    ).first()

    # Payments
    payments = db.query(Payment).filter(Payment.tenant_id == tenant_id).order_by(Payment.due_date.desc()).all()
    pending_payments = [p for p in payments if p.status == "pending"]
    total_outstanding = sum(float(p.amount) for p in pending_payments if p.amount)
    
    # Maintenance
    maintenance_tickets = db.query(Maintenance).filter(Maintenance.tenant_id == tenant_id).order_by(Maintenance.created_at.desc()).all()
    open_tickets = [m for m in maintenance_tickets if m.status in ["pending", "in_progress"]]

    # Rental Applications
    applications = db.query(RentalApplication).filter(RentalApplication.applicant_id == tenant_id).order_by(RentalApplication.created_at.desc()).all()

    lease_data = None
    property_data = None
    unit_data = None

    if active_lease:
        prop = active_lease.property
        unit = active_lease.unit
        lease_data = {
            "id": active_lease.id,
            "property_id": active_lease.property_id,
            "unit_id": active_lease.unit_id,
            "property_name": prop.name if prop else "Rental Property",
            "unit_number": unit.unit_number if unit else (active_lease.unit_number or "1"),
            "start_date": active_lease.start_date,
            "end_date": active_lease.end_date,
            "rent_amount": active_lease.rent_amount,
            "deposit": active_lease.deposit,
            "payment_due_date": active_lease.payment_due_date or 1,
            "status": active_lease.status,
            "notes": active_lease.notes
        }
        if prop:
            property_data = {
                "id": prop.id,
                "name": prop.name,
                "address": prop.address,
                "city": prop.city,
                "image_url": prop.image_url,
                "manager_name": prop.manager.full_name if prop.manager else None,
                "manager_phone": prop.manager.phone if (prop.manager and hasattr(prop.manager, "phone")) else None,
                "manager_email": prop.manager.email if prop.manager else None,
            }
        if unit:
            unit_data = {
                "id": unit.id,
                "unit_number": unit.unit_number,
                "unit_type": unit.unit_type,
                "bedrooms": unit.bedrooms,
                "bathrooms": unit.bathrooms,
            }

    formatted_payments = [
        {
            "id": p.id,
            "lease_id": p.lease_id,
            "tenant_id": p.tenant_id,
            "property_id": p.property_id,
            "amount": p.amount,
            "due_date": p.due_date,
            "payment_date": p.payment_date,
            "status": p.status,
            "payment_method": p.payment_method,
            "reference": p.reference,
            "property_name": p.property.name if p.property else None,
        }
        for p in payments
    ]

    formatted_maintenance = [
        {
            "id": m.id,
            "property_id": m.property_id,
            "unit_id": m.unit_id,
            "tenant_id": m.tenant_id,
            "title": m.title,
            "description": m.description,
            "category": m.category,
            "priority": m.priority,
            "status": m.status,
            "cost": float(m.cost) if m.cost else 0.0,
            "property_name": m.property.name if m.property else None,
            "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
        }
        for m in maintenance_tickets
    ]

    formatted_applications = [
        {
            "id": a.id,
            "property_id": a.property_id,
            "applicant_id": a.applicant_id,
            "status": a.status,
            "monthly_income": a.monthly_income,
            "notes": a.notes,
            "created_at": a.created_at.isoformat() if hasattr(a.created_at, "isoformat") else str(a.created_at),
            "property_name": a.property.name if a.property else "Property",
        }
        for a in applications
    ]

    return {
        # Top-level keys expected by TenantDashboardData
        "active_lease": lease_data,
        "pending_payments": [p for p in formatted_payments if p["status"] == "pending"],
        "active_maintenance": [m for m in formatted_maintenance if m["status"] in ["pending", "in_progress"]],
        "applications": formatted_applications,

        # Additional helpers and backwards-compatibility
        "has_active_tenancy": active_lease is not None,
        "lease": lease_data,
        "property": property_data,
        "unit": unit_data,
        "financials": {
            "monthly_rent": float(active_lease.rent_amount) if (active_lease and active_lease.rent_amount) else 0,
            "outstanding_balance": round(total_outstanding, 2),
            "pending_payments_count": len(pending_payments),
            "last_payment_date": payments[0].payment_date if (payments and payments[0].payment_date) else None,
        },
        "maintenance": {
            "total_submitted": len(maintenance_tickets),
            "open_tickets_count": len(open_tickets),
            "recent_tickets": [
                {
                    "id": m.id,
                    "title": m.title,
                    "category": m.category,
                    "priority": m.priority,
                    "status": m.status,
                    "created_at": m.created_at
                }
                for m in maintenance_tickets[:4]
            ]
        },
        "recent_payments": [
            {
                "id": p.id,
                "amount": p.amount,
                "due_date": p.due_date,
                "payment_date": p.payment_date,
                "status": p.status,
                "payment_method": p.payment_method,
                "reference": p.reference
            }
            for p in payments[:5]
        ]
    }


@router.get("/my-tenancy")
def get_my_tenancy(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns current tenant's active lease.
    """
    active_lease = db.query(Lease).filter(
        Lease.tenant_id == current_user.id,
        Lease.status == "active"
    ).first()
    if not active_lease:
        return None

    prop = active_lease.property
    unit = active_lease.unit
    return {
        "id": active_lease.id,
        "property_id": active_lease.property_id,
        "unit_id": active_lease.unit_id,
        "property_name": prop.name if prop else "Rental Property",
        "unit_number": unit.unit_number if unit else (active_lease.unit_number or "1"),
        "start_date": active_lease.start_date,
        "end_date": active_lease.end_date,
        "rent_amount": active_lease.rent_amount,
        "deposit": active_lease.deposit,
        "payment_due_date": active_lease.payment_due_date or 1,
        "status": active_lease.status,
        "notes": active_lease.notes,
        "landlord_name": prop.owner.full_name if (prop and prop.owner) else None,
        "manager_name": prop.manager.full_name if (prop and prop.manager) else None,
    }


@router.get("/payments")
def get_my_payments(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns all payment records for current tenant.
    """
    payments = db.query(Payment).filter(Payment.tenant_id == current_user.id).order_by(Payment.due_date.desc()).all()
    return [
        {
            "id": p.id,
            "lease_id": p.lease_id,
            "tenant_id": p.tenant_id,
            "property_id": p.property_id,
            "amount": p.amount,
            "due_date": p.due_date,
            "payment_date": p.payment_date,
            "status": p.status,
            "payment_method": p.payment_method,
            "reference": p.reference,
            "property_name": p.property.name if p.property else None,
        }
        for p in payments
    ]


@router.get("/maintenance")
def get_my_maintenance(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns all maintenance requests filed by current tenant.
    """
    tickets = db.query(Maintenance).filter(Maintenance.tenant_id == current_user.id).order_by(Maintenance.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "property_id": m.property_id,
            "unit_id": m.unit_id,
            "tenant_id": m.tenant_id,
            "title": m.title,
            "description": m.description,
            "category": m.category,
            "priority": m.priority,
            "status": m.status,
            "cost": float(m.cost) if m.cost else 0.0,
            "property_name": m.property.name if m.property else None,
            "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
        }
        for m in tickets
    ]

