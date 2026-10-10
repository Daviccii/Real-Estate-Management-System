from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Float, cast, func

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access, require_user
from app.models.property import Property
from app.models.unit import Unit
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.maintenance import Maintenance
from app.models.application import RentalApplication
from app.models.user import User

router = APIRouter(prefix="/owner", tags=["owner"])


@router.get("/dashboard")
def get_owner_dashboard(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns real portfolio performance metrics for properties owned by the current user.
    """
    owner_id = current_user.id
    property_query = db.query(Property.id).filter(Property.owner_id == owner_id)
    if current_user.company_id is not None:
        property_query = property_query.filter(Property.company_id == current_user.company_id)
    property_ids = property_query.subquery()
    property_count = db.query(func.count(Property.id)).filter(
        Property.owner_id == owner_id,
        Property.company_id == current_user.company_id if current_user.company_id is not None else True,
    ).scalar() or 0

    if not property_count:
        return {
            "portfolio": {"total_properties": 0, "total_units": 0, "occupied_units": 0, "vacant_units": 0, "occupancy_rate": 0},
            "financials": {"expected_rent": 0, "collected_rent": 0, "outstanding_balance": 0, "maintenance_expenses": 0, "net_income": 0},
            "leases": {"active_leases": 0, "expiring_soon": 0},
            "pending_applications": 0,
            "open_maintenance": 0,
            "recent_properties": []
        }

    total_units = db.query(func.count(Unit.id)).filter(Unit.property_id.in_(property_ids)).scalar() or 0
    occupied_units = db.query(func.count(Unit.id)).filter(
        Unit.property_id.in_(property_ids), Unit.status == "occupied"
    ).scalar() or 0
    vacant_units = total_units - occupied_units
    occupancy_rate = round((occupied_units / total_units * 100), 1) if total_units > 0 else 0

    # Leases
    active_leases = db.query(func.count(Lease.id)).filter(
        Lease.property_id.in_(property_ids), Lease.status == "active"
    ).scalar() or 0
    expected_rent = db.query(func.coalesce(func.sum(cast(Lease.rent_amount, Float)), 0)).filter(
        Lease.property_id.in_(property_ids), Lease.status == "active"
    ).scalar() or 0
    collected_rent = db.query(func.coalesce(func.sum(cast(Payment.amount, Float)), 0)).filter(
        Payment.property_id.in_(property_ids), Payment.status == "paid"
    ).scalar() or 0
    pending_payments = db.query(func.coalesce(func.sum(cast(Payment.amount, Float)), 0)).filter(
        Payment.property_id.in_(property_ids), Payment.status == "pending"
    ).scalar() or 0
    maint_expenses = db.query(func.coalesce(func.sum(cast(Maintenance.cost, Float)), 0)).filter(
        Maintenance.property_id.in_(property_ids), Maintenance.status == "resolved"
    ).scalar() or 0
    open_maint = db.query(func.count(Maintenance.id)).filter(
        Maintenance.property_id.in_(property_ids),
        Maintenance.status.in_(["pending", "in_progress"]),
    ).scalar() or 0

    # Pending rental applications
    pending_apps = db.query(RentalApplication).filter(
        RentalApplication.property_id.in_(property_ids),
        RentalApplication.status.in_(["submitted", "under_review"])
    ).count()
    recent_properties = db.query(Property).filter(
        Property.owner_id == owner_id,
        Property.company_id == current_user.company_id if current_user.company_id is not None else True,
    ).order_by(Property.created_at.desc(), Property.id.desc()).limit(6).all()

    return {
        "portfolio": {
            "total_properties": property_count,
            "total_units": total_units,
            "occupied_units": occupied_units,
            "vacant_units": vacant_units,
            "occupancy_rate": occupancy_rate
        },
        "financials": {
            "expected_rent": round(expected_rent, 2),
            "collected_rent": round(collected_rent, 2),
            "outstanding_balance": round(pending_payments, 2),
            "maintenance_expenses": round(maint_expenses, 2),
            "net_income": round(collected_rent - maint_expenses, 2)
        },
        "leases": {
            "active_leases": active_leases,
            "expiring_soon": 0
        },
        "pending_applications": pending_apps,
        "open_maintenance": open_maint,
        "recent_properties": [
            {
                "id": p.id,
                "name": p.name,
                "city": p.city,
                "units_count": p.units_count or 1,
                "status": p.status,
                "purpose": p.purpose,
                "price": p.price_label or p.price,
                "manager_id": p.manager_id,
                "agent_id": p.agent_id,
                "is_verified": p.is_verified
            }
            for p in recent_properties
        ]
    }


@router.get("/properties")
def get_owner_properties(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns full property list for owner with manager/agent details.
    """
    props = db.query(Property).filter(Property.owner_id == current_user.id).all()
    out = []
    for p in props:
        out.append({
            "id": p.id,
            "name": p.name,
            "city": p.city,
            "county": p.county,
            "address": p.address,
            "property_type": p.property_type,
            "status": p.status,
            "units_count": p.units_count or 1,
            "price": p.price_label or p.price,
            "purpose": p.purpose,
            "image_url": p.image_url,
            "is_verified": p.is_verified,
            "manager_id": p.manager_id,
            "manager_name": p.manager.full_name if p.manager else None,
            "agent_id": p.agent_id,
            "agent_name": p.agent.full_name if p.agent else None,
            "created_at": p.created_at
        })
    return out


from pydantic import BaseModel


class AssignStaffPayload(BaseModel):
    manager_id: Optional[int] = None
    agent_id: Optional[int] = None


@router.get("/portfolio-summary")
def get_owner_portfolio_summary_endpoint(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns high-level summary matching OwnerPortfolioSummary for owner dashboard.
    """
    dash = get_owner_dashboard(current_user=current_user, db=db)
    portfolio = dash.get("portfolio", {})
    financials = dash.get("financials", {})
    return {
        "total_properties": portfolio.get("total_properties", 0),
        "total_units": portfolio.get("total_units", 0),
        "occupied_units": portfolio.get("occupied_units", 0),
        "vacant_units": portfolio.get("vacant_units", 0),
        "occupancy_rate": portfolio.get("occupancy_rate", 0),
        "total_revenue_collected": financials.get("collected_rent", 0),
        "pending_payments": financials.get("outstanding_balance", 0),
        "active_maintenance": dash.get("open_maintenance", 0),
    }


@router.get("/financials")
def get_owner_financials(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns ledger of all payments for owner's properties.
    """
    owner_id = current_user.id
    props = db.query(Property).filter(Property.owner_id == owner_id).all()
    prop_ids = [p.id for p in props]
    if not prop_ids:
        return {"payments": [], "total_collected": 0, "total_pending": 0}

    payments = db.query(Payment).filter(Payment.property_id.in_(prop_ids)).order_by(Payment.due_date.desc()).all()
    collected = sum(float(p.amount) for p in payments if p.status == "paid" and p.amount)
    pending = sum(float(p.amount) for p in payments if p.status == "pending" and p.amount)

    return {
        "payments": [
            {
                "id": p.id,
                "lease_id": p.lease_id,
                "tenant_id": p.tenant_id,
                "property_id": p.property_id,
                "amount": p.amount,
                "status": p.status,
                "due_date": p.due_date,
                "payment_date": p.payment_date,
                "payment_method": p.payment_method,
                "reference": p.reference,
                "tenant_name": p.tenant.full_name if p.tenant else "Tenant",
                "property_name": p.property.name if p.property else "Property",
            }
            for p in payments
        ],
        "total_collected": round(collected, 2),
        "total_pending": round(pending, 2)
    }


@router.get("/maintenance")
def get_owner_maintenance(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns all maintenance tickets for properties owned by current user.
    """
    owner_id = current_user.id
    props = db.query(Property).filter(Property.owner_id == owner_id).all()
    prop_ids = [p.id for p in props]
    if not prop_ids:
        return []

    tickets = db.query(Maintenance).filter(Maintenance.property_id.in_(prop_ids)).order_by(Maintenance.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "property_id": t.property_id,
            "unit_id": t.unit_id,
            "tenant_id": t.tenant_id,
            "title": t.title,
            "description": t.description,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "cost": float(t.cost) if t.cost else 0.0,
            "property_name": t.property.name if t.property else "Property",
            "tenant_name": t.tenant.full_name if t.tenant else "Tenant",
            "created_at": t.created_at.isoformat() if hasattr(t.created_at, "isoformat") else str(t.created_at),
        }
        for t in tickets
    ]


@router.put("/properties/{property_id}/assign")
@router.patch("/properties/{property_id}/assign")
def assign_manager_and_agent(
    property_id: int,
    payload: Optional[AssignStaffPayload] = None,
    manager_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Landlord assigns a Property Manager and/or representing Agent.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not company_resource_access(current_user, prop):
        raise HTTPException(status_code=404, detail="Property not found")

    if prop.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to reassign staff for this property")

    # Read from JSON body payload if provided, otherwise query params
    effective_manager_id = payload.manager_id if (payload and payload.manager_id is not None) else manager_id
    effective_agent_id = payload.agent_id if (payload and payload.agent_id is not None) else agent_id

    for assigned_id, expected_role in (
        (effective_manager_id, "manager"),
        (effective_agent_id, "agent"),
    ):
        if assigned_id is None or assigned_id <= 0:
            continue
        assigned_user = db.query(User).filter(User.id == assigned_id).first()
        if not assigned_user or assigned_user.role != expected_role or not company_resource_access(current_user, assigned_user):
            raise HTTPException(status_code=404, detail=f"{expected_role.title()} not found")

    if effective_manager_id is not None:
        prop.manager_id = effective_manager_id if effective_manager_id > 0 else None
    if effective_agent_id is not None:
        prop.agent_id = effective_agent_id if effective_agent_id > 0 else None

    db.commit()
    db.refresh(prop)
    return {
        "message": "Staff assignment updated successfully",
        "property_id": prop.id,
        "manager_id": prop.manager_id,
        "agent_id": prop.agent_id
    }
