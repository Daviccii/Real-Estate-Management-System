"""
Manager-specific endpoints for property management.
All endpoints require manager role and filter by manager's assigned properties.

A manager can only view/manage properties where they are assigned as manager_id.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel

from app.database.database import get_db
from app.auth.roles import require_role
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.property import Property
from app.models.unit import Unit
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.maintenance import Maintenance
from app.models.inquiry import Inquiry
from app.repositories.property_repo import (
    get_property as repo_get_property,
    update_property as repo_update_property,
)

router = APIRouter(prefix="/manager", tags=["manager"])


class MaintenanceStatusUpdate(BaseModel):
    """Update maintenance request status"""
    status: str


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard")
def manager_dashboard(
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    Manager dashboard with statistics for managed properties.
    Shows only data related to properties where current_user is the manager.
    """
    # Properties managed by this manager
    managed_properties = db.query(Property).filter(
        Property.manager_id == current_user.id
    ).all()
    
    property_ids = [p.id for p in managed_properties]
    
    if not property_ids:
        # No managed properties, return empty stats
        return {
            "properties": {
                "total": 0,
                "occupied": 0,
                "vacant": 0,
                "by_status": {}
            },
            "leases": {
                "total": 0,
                "active": 0,
                "expiring_soon": 0
            },
            "tenants": {
                "total": 0
            },
            "payments": {
                "total": 0,
                "pending": 0,
                "overdue": 0,
                "total_amount": 0,
                "pending_amount": 0
            },
            "maintenance": {
                "total": 0,
                "open": 0,
                "in_progress": 0
            },
            "inquiries": {
                "total": 0,
                "pending": 0
            },
            "recent_activity": {
                "properties": [],
                "leases": [],
                "maintenance": [],
                "payments": []
            }
        }
    
    # Properties stats
    total_properties = len(managed_properties)
    
    status_counts = db.query(
        Property.status,
        func.count(Property.id)
    ).filter(Property.manager_id == current_user.id).group_by(Property.status).all()
    status_data = {status: count for status, count in status_counts if status}
    
    # Occupied vs Vacant
    occupied = db.query(func.count(Lease.id)).filter(
        Lease.property_id.in_(property_ids),
        Lease.status == "active"
    ).scalar() or 0
    
    # Leases stats
    total_leases = db.query(func.count(Lease.id)).filter(
        Lease.property_id.in_(property_ids)
    ).scalar() or 0
    
    active_leases = db.query(func.count(Lease.id)).filter(
        Lease.property_id.in_(property_ids),
        Lease.status == "active"
    ).scalar() or 0
    
    # Count leases expiring in next 30 days
    from datetime import datetime, timedelta
    from app.utils.time import utc_now
    thirty_days = utc_now() + timedelta(days=30)
    expiring_soon = db.query(func.count(Lease.id)).filter(
        Lease.property_id.in_(property_ids),
        Lease.end_date <= thirty_days,
        Lease.status == "active"
    ).scalar() or 0
    
    # Tenants (distinct users with active leases in managed properties)
    total_tenants = db.query(func.count(Lease.tenant_id.distinct())).filter(
        Lease.property_id.in_(property_ids),
        Lease.status == "active"
    ).scalar() or 0
    
    # Payments stats
    total_payments = db.query(func.count(Payment.id)).filter(
        Payment.property_id.in_(property_ids)
    ).scalar() or 0
    
    pending_payments = db.query(func.count(Payment.id)).filter(
        Payment.property_id.in_(property_ids),
        Payment.status.in_(["pending", "overdue"])
    ).scalar() or 0
    
    overdue_payments = db.query(func.count(Payment.id)).filter(
        Payment.property_id.in_(property_ids),
        Payment.status == "overdue"
    ).scalar() or 0
    
    total_payment_amount = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.property_id.in_(property_ids)
    ).scalar() or 0
    
    pending_payment_amount = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.property_id.in_(property_ids),
        Payment.status.in_(["pending", "overdue"])
    ).scalar() or 0
    
    # Maintenance stats
    total_maintenance = db.query(func.count(Maintenance.id)).filter(
        Maintenance.property_id.in_(property_ids)
    ).scalar() or 0
    
    open_maintenance = db.query(func.count(Maintenance.id)).filter(
        Maintenance.property_id.in_(property_ids),
        Maintenance.status == "open"
    ).scalar() or 0
    
    in_progress_maintenance = db.query(func.count(Maintenance.id)).filter(
        Maintenance.property_id.in_(property_ids),
        Maintenance.status == "in_progress"
    ).scalar() or 0
    
    # Inquiries stats
    total_inquiries = db.query(func.count(Inquiry.id)).filter(
        Inquiry.property_id.in_(property_ids)
    ).scalar() or 0
    
    pending_inquiries = db.query(func.count(Inquiry.id)).filter(
        Inquiry.property_id.in_(property_ids),
        Inquiry.status == "pending"
    ).scalar() or 0
    
    # Recent activity
    recent_properties = db.query(Property).filter(
        Property.manager_id == current_user.id
    ).order_by(Property.updated_at.desc()).limit(5).all()
    
    recent_leases = db.query(Lease).filter(
        Lease.property_id.in_(property_ids)
    ).order_by(Lease.created_at.desc()).limit(5).all()
    
    recent_maintenance = db.query(Maintenance).filter(
        Maintenance.property_id.in_(property_ids)
    ).order_by(Maintenance.created_at.desc()).limit(5).all()
    
    recent_payments = db.query(Payment).filter(
        Payment.property_id.in_(property_ids)
    ).order_by(Payment.created_at.desc()).limit(5).all()
    
    return {
        "properties": {
            "total": total_properties,
            "occupied": occupied,
            "vacant": total_properties - occupied,
            "by_status": status_data
        },
        "leases": {
            "total": total_leases,
            "active": active_leases,
            "expiring_soon": expiring_soon
        },
        "tenants": {
            "total": total_tenants
        },
        "payments": {
            "total": total_payments,
            "pending": pending_payments,
            "overdue": overdue_payments,
            "total_amount": float(total_payment_amount),
            "pending_amount": float(pending_payment_amount)
        },
        "maintenance": {
            "total": total_maintenance,
            "open": open_maintenance,
            "in_progress": in_progress_maintenance
        },
        "inquiries": {
            "total": total_inquiries,
            "pending": pending_inquiries
        },
        "recent_activity": {
            "properties": [
                {
                    "id": p.id,
                    "name": p.name,
                    "city": p.city,
                    "status": p.status,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None
                } for p in recent_properties
            ],
            "leases": [
                {
                    "id": l.id,
                    "tenant_id": l.tenant_id,
                    "property_id": l.property_id,
                    "status": l.status,
                    "start_date": l.start_date.isoformat() if l.start_date else None,
                    "end_date": l.end_date.isoformat() if l.end_date else None,
                    "created_at": l.created_at.isoformat() if l.created_at else None
                } for l in recent_leases
            ],
            "maintenance": [
                {
                    "id": m.id,
                    "property_id": m.property_id,
                    "title": m.title,
                    "status": m.status,
                    "priority": m.priority,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                } for m in recent_maintenance
            ],
            "payments": [
                {
                    "id": p.id,
                    "tenant_id": p.tenant_id,
                    "amount": float(p.amount) if p.amount else 0,
                    "status": p.status,
                    "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                } for p in recent_payments
            ]
        }
    }


# ============================================================================
# PROPERTIES
# ============================================================================

@router.get("/properties")
def list_manager_properties(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    List properties managed by the current manager.
    """
    query = db.query(Property).filter(Property.manager_id == current_user.id)
    
    if status:
        query = query.filter(Property.status == status)
    
    properties = query.order_by(Property.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "city": p.city,
            "owner_id": p.owner_id,
            "manager_id": p.manager_id,
            "status": p.status,
            "purpose": p.purpose,
            "property_type": p.property_type,
            "units_count": p.units_count,
            "address": p.address,
            "bedrooms": p.bedrooms,
            "bathrooms": p.bathrooms,
            "price_label": p.price_label,
            "image_url": p.image_url,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None
        }
        for p in properties
    ]


@router.get("/properties/{property_id}")
def get_manager_property(
    property_id: int,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    Get a specific property managed by the current manager.
    """
    prop = repo_get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    # Verify manager owns this property
    if prop.manager_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this property")
    
    return prop


@router.put("/properties/{property_id}")
def update_manager_property(
    property_id: int,
    property_update: dict,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    Update a property managed by the current manager.
    Manager can update property details but not owner/manager assignment.
    """
    prop = repo_get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    if prop.manager_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this property")
    
    # Remove owner_id and manager_id from update data if present
    property_update.pop("owner_id", None)
    property_update.pop("manager_id", None)
    
    updated = repo_update_property(db, prop, **property_update)
    return updated


# ============================================================================
# TENANTS
# ============================================================================

@router.get("/tenants")
def list_manager_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    List all tenants with active leases in properties managed by the current manager.
    """
    # Get managed property IDs
    managed_property_ids = db.query(Property.id).filter(
        Property.manager_id == current_user.id
    ).subquery()
    
    # Get tenants with active leases
    tenants = db.query(User).distinct(User.id).join(
        Lease, User.id == Lease.tenant_id
    ).filter(
        Lease.property_id.in_(db.query(Property.id).filter(Property.manager_id == current_user.id)),
        Lease.status == "active"
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": t.id,
            "email": t.email,
            "full_name": t.full_name,
            "role": t.role,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tenants
    ]


# ============================================================================
# LEASES
# ============================================================================

@router.get("/leases")
def list_manager_leases(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    List leases for properties managed by the current manager.
    """
    query = db.query(Lease).filter(
        Lease.property_id.in_(
            db.query(Property.id).filter(Property.manager_id == current_user.id)
        )
    )
    
    if status:
        query = query.filter(Lease.status == status)
    
    leases = query.order_by(Lease.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": l.id,
            "tenant_id": l.tenant_id,
            "property_id": l.property_id,
            "unit_id": l.unit_id,
            "start_date": l.start_date.isoformat() if l.start_date else None,
            "end_date": l.end_date.isoformat() if l.end_date else None,
            "rent_amount": float(l.rent_amount) if l.rent_amount else 0,
            "deposit": float(l.deposit) if l.deposit else 0,
            "status": l.status,
            "payment_due_date": l.payment_due_date.isoformat() if hasattr(l.payment_due_date, "isoformat") else l.payment_due_date,
            "created_at": l.created_at.isoformat() if l.created_at else None
        }
        for l in leases
    ]


# ============================================================================
# PAYMENTS
# ============================================================================

@router.get("/payments")
def list_manager_payments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    List payments for leases in properties managed by the current manager.
    """
    query = db.query(Payment).filter(
        Payment.property_id.in_(
            db.query(Property.id).filter(Property.manager_id == current_user.id)
        )
    )
    
    if status:
        query = query.filter(Payment.status == status)
    
    payments = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": p.id,
            "tenant_id": p.tenant_id,
            "lease_id": p.lease_id,
            "property_id": p.property_id,
            "amount": float(p.amount) if p.amount else 0,
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "due_date": p.due_date.isoformat() if p.due_date else None,
            "status": p.status,
            "payment_type": p.payment_type,
            "reference": p.reference,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in payments
    ]


@router.get("/payments/overview")
def manager_payments_overview(
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    Payment overview for properties managed by the current manager.
    """
    managed_property_ids = db.query(Property.id).filter(
        Property.manager_id == current_user.id
    ).all()
    
    property_ids = [p.id for p in managed_property_ids]
    
    if not property_ids:
        return {"total": 0, "paid": 0, "pending": 0, "overdue": 0, "total_amount": 0}
    
    total = db.query(func.count(Payment.id)).filter(
        Payment.property_id.in_(property_ids)
    ).scalar() or 0
    
    paid = db.query(func.count(Payment.id)).filter(
        Payment.property_id.in_(property_ids),
        Payment.status == "paid"
    ).scalar() or 0
    
    pending = db.query(func.count(Payment.id)).filter(
        Payment.property_id.in_(property_ids),
        Payment.status == "pending"
    ).scalar() or 0
    
    overdue = db.query(func.count(Payment.id)).filter(
        Payment.property_id.in_(property_ids),
        Payment.status == "overdue"
    ).scalar() or 0
    
    total_amount = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.property_id.in_(property_ids)
    ).scalar() or 0
    
    return {
        "total": total,
        "paid": paid,
        "pending": pending,
        "overdue": overdue,
        "total_amount": float(total_amount)
    }


# ============================================================================
# MAINTENANCE
# ============================================================================

@router.get("/maintenance")
def list_manager_maintenance(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    List maintenance requests for properties managed by the current manager.
    """
    query = db.query(Maintenance).filter(
        Maintenance.property_id.in_(
            db.query(Property.id).filter(Property.manager_id == current_user.id)
        )
    )
    
    if status:
        query = query.filter(Maintenance.status == status)
    
    maintenance = query.order_by(Maintenance.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": m.id,
            "tenant_id": m.tenant_id,
            "property_id": m.property_id,
            "unit_id": m.unit_id,
            "title": m.title,
            "description": m.description,
            "category": m.category,
            "priority": m.priority,
            "status": m.status,
            "assigned_manager_id": m.assigned_manager_id,
            "cost": float(m.cost) if m.cost else 0,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "resolved_at": m.resolved_at.isoformat() if m.resolved_at else None
        }
        for m in maintenance
    ]


@router.put("/maintenance/{maintenance_id}/status")
def update_maintenance_status(
    maintenance_id: int,
    status_update: MaintenanceStatusUpdate,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    Update maintenance request status for properties managed by the current manager.
    """
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")
    
    # Verify manager owns this maintenance request's property
    if maintenance.property_id not in [p.id for p in db.query(Property.id).filter(Property.manager_id == current_user.id).all()]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this maintenance request")
    
    maintenance.status = status_update.status
    if status_update.status == "resolved":
        from datetime import datetime
        maintenance.resolved_at = utc_now()
    
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    
    return {
        "id": maintenance.id,
        "status": maintenance.status,
        "message": "Maintenance status updated successfully"
    }


# ============================================================================
# INQUIRIES
# ============================================================================

@router.get("/inquiries")
def list_manager_inquiries(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    List inquiries for properties managed by the current manager.
    """
    query = db.query(Inquiry).filter(
        Inquiry.property_id.in_(
            db.query(Property.id).filter(Property.manager_id == current_user.id)
        )
    )
    
    if status:
        query = query.filter(Inquiry.status == status)
    
    inquiries = query.order_by(Inquiry.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": i.id,
            "user_id": i.user_id,
            "property_id": i.property_id,
            "message": i.message,
            "status": i.status,
            "created_at": i.created_at.isoformat() if i.created_at else None
        }
        for i in inquiries
    ]


# ============================================================================
# UNITS
# ============================================================================

@router.get("/units")
def list_manager_units(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["manager"])),
    db: Session = Depends(get_db)
):
    """
    List all units in properties managed by the current manager.
    """
    units = db.query(Unit).filter(
        Unit.property_id.in_(
            db.query(Property.id).filter(Property.manager_id == current_user.id)
        )
    ).order_by(Unit.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": u.id,
            "property_id": u.property_id,
            "unit_number": u.unit_number,
            "unit_type": u.unit_type,
            "bedrooms": u.bedrooms,
            "bathrooms": u.bathrooms,
            "area": u.area,
            "rent": float(u.rent) if u.rent else 0,
            "status": u.status,
            "availability_date": u.availability_date.isoformat() if u.availability_date else None,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in units
    ]
