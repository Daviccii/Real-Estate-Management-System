"""
Admin-specific endpoints for platform management.
All endpoints require admin role.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func
from pydantic import BaseModel

from app.database.database import get_db
from app.auth.permissions import PERMISSION_CATALOG, ROLE_PERMISSIONS
from app.auth.roles import (
    company_resource_access,
    require_admin,
    require_company_resource,
    require_permission,
)
from app.models.user import User
from app.models.property import Property
from app.models.inquiry import Inquiry
from app.models.payment import Payment
from app.models.role_profiles import ManagerProfile
from app.models.audit_log import AuditLog
from app.schemas.property import PropertyUpdate
from app.schemas.platform_settings import PlatformSettingsOut, PlatformSettingsUpdate
from app.schemas.role_profiles import ManagerProvisionPayload, ManagerProfileOut
from app.utils.security import get_password_hash
from app.repositories.user_repo import list_users, get_user as repo_get_user
from app.repositories.property_repo import list_properties as repo_list_properties, get_property as repo_get_property, update_property as repo_update_property
from app.repositories.inquiry_repo import list_user_inquiries
from app.repositories.platform_settings_repo import get_or_create_settings, update_settings as repo_update_settings
from app.services.account_lockout import unlock_account

router = APIRouter(prefix="/admin", tags=["admin"])


def _company_scope(model, current_user: User):
    return (
        model.company_id.is_(None)
        if current_user.company_id is None
        else model.company_id == current_user.company_id
    )


# FIX: these three request bodies were previously bare scalar function
# parameters (e.g. `role: str`), which FastAPI parses as *required query
# parameters*, not JSON body fields. The frontend (adminService) sends a
# JSON body, so those requests either 422'd (role/inquiry-status — no
# default) or silently no-op'd (property update — all fields optional with
# defaults, so the request "succeeded" with 200 but changed nothing).
class RoleUpdate(BaseModel):
    role: str


class InquiryStatusUpdate(BaseModel):
    status: str


class UserStatusUpdate(BaseModel):
    """New — backs the suspend/reactivate action. Previously the only ways
    to act on a problem account were a full role change or permanent
    deletion; there was no soft "disable this account" option even though
    User.is_active already exists on the model."""
    is_active: bool


class PropertyReassign(BaseModel):
    """
    New — lets admin change who owns a property and/or who manages it.
    Deliberately a separate schema/endpoint from PropertyUpdate (used by
    both admin and the property's own owner via PUT /properties/{id}):
    owner_id must stay admin-only, since letting an owner reassign their own
    property's owner_id via self-service update risks them accidentally
    transferring away a listing they meant to keep. manager_id could
    reasonably be owner-editable too, but is kept here for now to keep the
    admin-only reassignment story simple and centralized in one place.
    """
    owner_id: Optional[int] = None
    manager_id: Optional[int] = None


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin dashboard with platform statistics."""
    user_scope = _company_scope(User, current_user)
    property_scope = _company_scope(Property, current_user)
    total_users = db.query(func.count(User.id)).filter(user_scope).scalar() or 0
    users_by_role = db.query(
        User.role,
        func.count(User.id)
    ).filter(user_scope).group_by(User.role).all()
    role_data = {role: count for role, count in users_by_role if role}

    total_properties = db.query(func.count(Property.id)).filter(property_scope).scalar() or 0
    active_properties = db.query(func.count(Property.id)).filter(property_scope, Property.status == "active").scalar() or 0

    properties_by_purpose = db.query(
        Property.purpose,
        func.count(Property.id)
    ).filter(property_scope).group_by(Property.purpose).all()
    purpose_data = {purpose: count for purpose, count in properties_by_purpose if purpose}

    total_inquiries = db.query(func.count(Inquiry.id)).join(Property, Inquiry.property_id == Property.id).filter(property_scope).scalar() or 0

    inquiries_by_status = db.query(
        Inquiry.status,
        func.count(Inquiry.id)
    ).join(Property, Inquiry.property_id == Property.id).filter(property_scope).group_by(Inquiry.status).all()
    status_data = {status: count for status, count in inquiries_by_status if status}

    recent_properties = db.query(Property).filter(property_scope).order_by(Property.created_at.desc()).limit(5).all()
    recent_inquiries = db.query(Inquiry).join(Property, Inquiry.property_id == Property.id).filter(property_scope).order_by(Inquiry.created_at.desc()).limit(5).all()

    return {
        "users": {
            "total": total_users,
            "by_role": role_data
        },
        "properties": {
            "total": total_properties,
            "active": active_properties,
            "by_purpose": purpose_data
        },
        "inquiries": {
            "total": total_inquiries,
            "by_status": status_data
        },
        "recent_activity": {
            "properties": [
                {
                    "id": p.id,
                    "name": p.name,
                    "city": p.city,
                    "owner_id": p.owner_id,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                } for p in recent_properties
            ],
            "inquiries": [
                {
                    "id": i.id,
                    "user_id": i.user_id,
                    "property_id": i.property_id,
                    "status": i.status,
                    "created_at": i.created_at.isoformat() if i.created_at else None
                } for i in recent_inquiries
            ]
        }
    }


@router.get("/settings", response_model=PlatformSettingsOut)
def get_platform_settings(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Return the current platform settings, creating the singleton row with
    defaults on first access."""
    return get_or_create_settings(db)


@router.put("/settings", response_model=PlatformSettingsOut)
def update_platform_settings(
    payload: PlatformSettingsUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update one or more platform settings. Only fields present in the
    request body are changed."""
    settings_row = get_or_create_settings(db)
    updated = repo_update_settings(
        db, settings_row,
        updated_by_id=current_user.id,
        **payload.model_dump(exclude_none=True)
    )
    return updated


@router.get("/users")
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users with optional role filtering."""
    query = db.query(User).filter(_company_scope(User, current_user))
    if role:
        query = query.filter(User.role == role)

    users = query.order_by(User.id.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
        } for user in users
    ]


@router.get("/properties")
def list_all_properties(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all properties with optional status filtering."""
    query = db.query(Property).filter(_company_scope(Property, current_user))
    if status:
        query = query.filter(Property.status == status)

    properties = query.order_by(Property.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": prop.id,
            "name": prop.name,
            "city": prop.city,
            "owner_id": prop.owner_id,
            "status": prop.status,
            "purpose": prop.purpose,
            "property_type": prop.property_type,
            "units_count": prop.units_count,
            "price_label": prop.price_label,
            "created_at": prop.created_at.isoformat() if prop.created_at else None
        } for prop in properties
    ]


@router.get("/payments")
def list_all_payments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all payments with optional status filtering."""
    query = db.query(Payment).join(Property, Payment.property_id == Property.id).filter(_company_scope(Property, current_user))
    if status:
        query = query.filter(Payment.status == status)

    payments = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": p.id,
            "tenant_id": p.tenant_id,
            "lease_id": p.lease_id,
            "property_id": p.property_id,
            "unit_id": p.unit_id,
            "amount": p.amount,
            "payment_type": p.payment_type,
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "due_date": p.due_date.isoformat() if p.due_date else None,
            "status": p.status,
            "reference": p.reference,
            "payment_method": p.payment_method,
            "notes": p.notes,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        } for p in payments
    ]


@router.get("/inquiries")
def list_all_inquiries(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all inquiries with optional status filtering."""
    query = db.query(Inquiry).join(Property, Inquiry.property_id == Property.id).filter(_company_scope(Property, current_user))
    if status:
        query = query.filter(Inquiry.status == status)

    inquiries = query.order_by(Inquiry.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": inquiry.id,
            "user_id": inquiry.user_id,
            "property_id": inquiry.property_id,
            "message": inquiry.message,
            "status": inquiry.status,
            "created_at": inquiry.created_at.isoformat() if inquiry.created_at else None,
            "updated_at": inquiry.updated_at.isoformat() if inquiry.updated_at else None
        } for inquiry in inquiries
    ]


@router.get("/market-insights")
def admin_market_insights(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Enhanced market insights for admin."""
    total_properties = db.query(func.count(Property.id)).scalar() or 0

    purpose_counts = db.query(
        Property.purpose,
        func.count(Property.id)
    ).group_by(Property.purpose).all()

    purpose_data = {purpose: count for purpose, count in purpose_counts if purpose}

    type_counts = db.query(
        Property.property_type,
        func.count(Property.id)
    ).group_by(Property.property_type).all()

    type_data = {ptype: count for ptype, count in type_counts if ptype}

    city_counts = db.query(
        Property.city,
        func.count(Property.id)
    ).group_by(Property.city).order_by(func.count(Property.id).desc()).limit(10).all()

    location_data = [{"city": city, "count": count} for city, count in city_counts if city]

    status_counts = db.query(
        Property.status,
        func.count(Property.id)
    ).group_by(Property.status).all()

    status_data = {status: count for status, count in status_counts}

    return {
        "total_properties": int(total_properties),
        "by_purpose": purpose_data,
        "by_type": type_data,
        "top_locations": location_data,
        "by_status": status_data,
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    require_company_resource(current_user, user, "User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: Optional[RoleUpdate] = None,
    role: Optional[str] = Query(default=None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a user's role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    require_company_resource(current_user, user, "User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    requested_role = payload.role if payload else role
    valid_roles = ["user", "tenant", "agent", "manager", "admin"]
    if requested_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of {valid_roles}")

    user.role = requested_role
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "message": "User role updated successfully"
    }


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Suspend or reactivate a user without deleting their account. This is the
    admin action for "temporarily disable this agent/manager/tenant" — as
    opposed to DELETE, which is permanent and cascades to their properties,
    leases, and payments.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    require_company_resource(current_user, user, "User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own account status")

    user.is_active = payload.is_active
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "message": "User status updated successfully"
    }


@router.delete("/properties/{property_id}")
def delete_property(
    property_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a property by ID."""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    require_company_resource(current_user, property, "Property not found")

    db.delete(property)
    db.commit()
    return {"message": "Property deleted successfully"}


@router.put("/properties/{property_id}")
def update_property(
    property_id: int,
    payload: PropertyUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a property by ID."""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    require_company_resource(current_user, property, "Property not found")

    updated = repo_update_property(db, property, **payload.model_dump(exclude_none=True))

    return {
        "id": updated.id,
        "name": updated.name,
        "city": updated.city,
        "owner_id": updated.owner_id,
        "status": updated.status,
        "purpose": updated.purpose,
        "property_type": updated.property_type,
        "units_count": updated.units_count,
        "price_label": updated.price_label,
        "created_at": updated.created_at.isoformat() if updated.created_at else None
    }


@router.put("/properties/{property_id}/reassign")
def reassign_property(
    property_id: int,
    payload: PropertyReassign,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    New — admin-only reassignment of a property's owner and/or manager.
    Previously there was no way to do this at all: PropertyUpdate (used by
    both this router's generic update_property above and the owner-facing
    PUT /properties/{id}) doesn't include owner_id or manager_id, so a
    property could never be transferred or have a manager assigned to it
    once created. Validates both ids actually exist before assigning so a
    typo doesn't silently attach a property to a nonexistent user.
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    require_company_resource(current_user, property, "Property not found")

    if payload.owner_id is not None:
        new_owner = repo_get_user(db, payload.owner_id)
        if not new_owner:
            raise HTTPException(status_code=404, detail=f"No user with id {payload.owner_id} to assign as owner")
        property.owner_id = payload.owner_id

    if payload.manager_id is not None:
        new_manager = repo_get_user(db, payload.manager_id)
        if not new_manager:
            raise HTTPException(status_code=404, detail=f"No user with id {payload.manager_id} to assign as manager")
        property.manager_id = payload.manager_id

    db.add(property)
    db.commit()
    db.refresh(property)

    return {
        "id": property.id,
        "name": property.name,
        "owner_id": property.owner_id,
        "manager_id": property.manager_id,
        "message": "Property reassigned successfully"
    }


@router.put("/inquiries/{inquiry_id}/status")
def update_inquiry_status(
    inquiry_id: int,
    payload: InquiryStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update an inquiry's status."""
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    require_company_resource(current_user, inquiry.property, "Inquiry not found")

    valid_statuses = ["pending", "in_progress", "resolved", "closed"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    inquiry.status = payload.status
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    return {
        "id": inquiry.id,
        "status": inquiry.status,
        "message": "Inquiry status updated successfully"
    }


@router.post("/provision-manager", status_code=status.HTTP_201_CREATED)
def provision_manager(
    payload: ManagerProvisionPayload,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to provision a verified Property Manager and their ManagerProfile.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    hashed = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed,
        full_name=payload.full_name,
        phone=payload.phone,
        role="manager",
        roles_csv="manager",
        is_verified=True,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ManagerProfile(
        user_id=user.id,
        company_name=payload.company_name,
        license_number=payload.license_number,
        operating_areas=payload.operating_areas,
        max_managed_units=payload.max_managed_units or 100,
        emergency_phone=payload.emergency_phone or payload.phone,
        is_verified=True
    )
    db.add(profile)

    audit = AuditLog(
        actor_id=current_user.id,
        action="PROVISION_MANAGER",
        entity_type="user",
        entity_id=user.id,
        details_json=f"Admin {current_user.email} provisioned manager {user.email} ({payload.company_name or payload.full_name})"
    )
    db.add(audit)
    db.commit()
    db.refresh(profile)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_verified": user.is_verified,
        "profile": ManagerProfileOut.model_validate(profile),
        "message": "Property Manager provisioned successfully"
    }


class AccountUnlockRequest(BaseModel):
    email: str


@router.post("/unlock-account")
async def admin_unlock_account(
    payload: AccountUnlockRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to unlock a user account that was locked due to failed login attempts.
    """
    # Verify user exists
    target_user = db.query(User).filter(User.email == payload.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Attempt to unlock
    unlocked = await unlock_account(payload.email)
    
    if unlocked:
        audit = AuditLog(
            actor_id=current_user.id,
            action="UNLOCK_ACCOUNT",
            entity_type="user",
            entity_id=target_user.id,
            details_json=f"Admin {current_user.email} unlocked account {payload.email}"
        )
        db.add(audit)
        db.commit()
        
        return {"message": f"Account {payload.email} has been unlocked successfully"}
    else:
        return {"message": f"Account {payload.email} was not locked"}


@router.post("/retention/run")
def run_retention_endpoint(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Run the data retention jobs now (expired auth tokens, audit log and
    notification pruning; suspended by LEGAL_HOLD_ENABLED). Scheduled runs use
    scripts/run_retention.py; this endpoint lets an admin trigger on demand.
    """
    from app.services import retention_service

    return retention_service.run_retention(db, actor_id=current_user.id)


@router.post("/payments/reconcile")
def reconcile_payments_endpoint(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Reconcile gateway-tracked payments: sync local status of pending payments
    that carry a provider transaction reference against the gateway's record.
    """
    from app.services.audit_service import log_audit_event
    from app.services.payment_gateway_service import PaymentGatewayError, get_gateway
    from app.utils.time import utc_now

    try:
        gateway = get_gateway()
    except PaymentGatewayError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    pending = (
        db.query(Payment)
        .filter(Payment.reference.isnot(None), Payment.status == "pending")
        .all()
    )
    counts = {"checked": 0, "marked_paid": 0, "marked_failed": 0, "unknown": 0}
    for payment in pending:
        status_at_gateway = gateway.fetch_transaction_status(payment.reference)
        counts["checked"] += 1
        if status_at_gateway == "succeeded" or status_at_gateway == "paid":
            payment.status = "paid"
            payment.payment_date = utc_now()
            counts["marked_paid"] += 1
        elif status_at_gateway == "failed":
            payment.status = "failed"
            counts["marked_failed"] += 1
        else:
            counts["unknown"] += 1
    db.commit()

    log_audit_event(
        db,
        current_user.id,
        "PAYMENT_RECONCILIATION_RUN",
        entity_type="payment",
        details=counts,
    )
    return counts


@router.get("/permissions/catalog")
def permission_catalog(current_user: User = Depends(require_permission("users:manage"))):
    """Permission vocabulary and per-role default grants, for admin UI gating."""
    return {
        "permissions": [
            {"permission": perm, "description": desc}
            for perm, desc in PERMISSION_CATALOG.items()
        ],
        "role_permissions": {
            role: sorted(grants) for role, grants in ROLE_PERMISSIONS.items()
        },
    }
