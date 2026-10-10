"""
Lease management endpoints.
Supports complete lease lifecycle with role-based authorization and validation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.utils.time import as_utc, utc_now

from app.schemas.lease import LeaseCreate, LeaseUpdate, LeaseOut, LeaseRenew, LeaseTerminate
from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import verify_role, require_management, require_admin
from app.repositories.lease_repo import (
    create_lease,
    get_lease as repo_get_lease,
    list_leases as repo_list_leases,
    update_lease as repo_update_lease,
    delete_lease as repo_delete_lease,
    mark_expiring_leases,
)
from app.repositories.property_repo import get_property as repo_get_property
from app.repositories.unit_repo import get_unit as repo_get_unit
from app.repositories.user_repo import get_user as repo_get_user
from app.models import User, Property, Lease
from app.config.settings import settings
from app.services.document_service import cached_pdf, generate_lease_pdf

router = APIRouter(prefix="/leases", tags=["leases"])


def can_manage_lease(current_user: User, lease_property: Property) -> bool:
    """Check if user can manage a lease based on property ownership/management."""
    if (
        lease_property.company_id is not None
        and current_user.company_id != lease_property.company_id
    ):
        return False
    if verify_role(current_user, ["admin"]):
        return True
    if lease_property.owner_id == current_user.id:
        return True
    if lease_property.manager_id == current_user.id:
        return True
    return False


def validate_lease_dates(start_date: datetime, end_date: datetime):
    """Validate lease dates."""
    start_date = as_utc(start_date)
    end_date = as_utc(end_date)
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )


def check_conflicting_lease(db: Session, unit_id: int, start_date: datetime, end_date: datetime, exclude_lease_id: Optional[int] = None):
    """Check for conflicting active leases for the same unit."""
    query = db.query(Lease).filter(
        Lease.unit_id == unit_id,
        Lease.status.in_(["active", "expiring soon"])
    )

    if exclude_lease_id:
        query = query.filter(Lease.id != exclude_lease_id)

    existing_leases = query.all()

    for lease in existing_leases:
        existing_start = as_utc(lease.start_date)
        existing_end = as_utc(lease.end_date)
        if not (as_utc(end_date) <= existing_start or as_utc(start_date) >= existing_end):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Conflicting active lease exists for this unit (Lease ID: {lease.id})"
            )


@router.post("/", response_model=LeaseOut, status_code=status.HTTP_201_CREATED)
def create(lease_in: LeaseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new lease. Only admins and managers can create leases."""
    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and managers can create leases"
        )

    validate_lease_dates(lease_in.start_date, lease_in.end_date)

    tenant = repo_get_user(db, lease_in.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    unit = repo_get_unit(db, lease_in.unit_id, for_update=True)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    property_obj = repo_get_property(db, lease_in.property_id)
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if not can_manage_lease(current_user, property_obj):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create leases for this property"
        )

    check_conflicting_lease(db, lease_in.unit_id, lease_in.start_date, lease_in.end_date)

    lease = Lease(**lease_in.model_dump())
    db.add(lease)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(lease)
    return lease


@router.get("/", response_model=List[LeaseOut])
def list_leases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    property_id: Optional[int] = None,
    unit_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List only authorized leases with database-level pagination."""
    authorized_user_id = None
    if verify_role(current_user, ["tenant"]):
        tenant_id = current_user.id
    elif verify_role(current_user, ["manager"]):
        authorized_user_id = current_user.id
    elif not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view leases")
    return repo_list_leases(
        db, skip=skip, limit=limit, property_id=property_id,
        unit_id=unit_id, tenant_id=tenant_id, status=status,
        authorized_user_id=authorized_user_id
    )


@router.get("/expiring-soon", response_model=List[LeaseOut])
def list_expiring_leases(
    days: int = 30,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get leases expiring within the specified number of days."""
    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view expiring leases")

    expiry_threshold = utc_now() + timedelta(days=days)
    authorized_user_id = None if verify_role(current_user, ["admin"]) else current_user.id
    mark_expiring_leases(
        db, expiry_threshold=expiry_threshold,
        authorized_user_id=authorized_user_id,
    )
    db.commit()
    return repo_list_leases(
        db, skip=skip, limit=limit, status="expiring soon",
        authorized_user_id=authorized_user_id,
    )


@router.get("/{lease_id}", response_model=LeaseOut)
def read(lease_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get lease details by ID."""
    lease = repo_get_lease(db, lease_id)
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    if verify_role(current_user, ["tenant"]):
        if lease.tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this lease")
    elif not verify_role(current_user, ["admin"]):
        property_obj = repo_get_property(db, lease.property_id)
        if not property_obj or not can_manage_lease(current_user, property_obj):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this lease")

    return lease


@router.get("/{lease_id}/document")
def download_document(lease_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Download the lease agreement as a PDF."""
    lease = repo_get_lease(db, lease_id)
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    if verify_role(current_user, ["tenant"]):
        if lease.tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this lease")
    elif not verify_role(current_user, ["admin"]):
        property_obj = repo_get_property(db, lease.property_id)
        if not property_obj or not can_manage_lease(current_user, property_obj):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this lease")

    tenant = repo_get_user(db, lease.tenant_id)
    unit = repo_get_unit(db, lease.unit_id)
    property_obj = repo_get_property(db, lease.property_id)
    path = cached_pdf(
        "lease", lease.id, lease.updated_at,
        lambda: generate_lease_pdf(lease, tenant, unit, property_obj),
    )
    return Response(
        content=path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="lease-{lease.id}.pdf"'},
    )


@router.put("/{lease_id}", response_model=LeaseOut)
def update(lease_id: int, lease_in: LeaseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update lease details."""
    lease = repo_get_lease(db, lease_id)
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify leases")

    property_obj = repo_get_property(db, lease.property_id)
    if not property_obj or not can_manage_lease(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this lease")

    if lease_in.start_date and lease_in.end_date:
        validate_lease_dates(lease_in.start_date, lease_in.end_date)
        check_conflicting_lease(db, lease.unit_id, lease_in.start_date, lease_in.end_date, exclude_lease_id=lease_id)

    updated = repo_update_lease(db, lease, **lease_in.model_dump(exclude_none=True))
    return updated


@router.delete("/{lease_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(lease_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a lease (admin only)."""
    if not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete leases")

    lease = repo_get_lease(db, lease_id)
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    repo_delete_lease(db, lease)
    return None


@router.post("/{lease_id}/renew", response_model=LeaseOut)
def renew(lease_id: int, renewal_in: LeaseRenew, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Renew an existing lease."""
    lease = repo_get_lease(db, lease_id)
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to renew leases")

    property_obj = repo_get_property(db, lease.property_id)
    if not property_obj or not can_manage_lease(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to renew this lease")

    if as_utc(renewal_in.new_end_date) <= as_utc(lease.end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New end date must be after current end date"
        )

    check_conflicting_lease(db, lease.unit_id, as_utc(lease.end_date), renewal_in.new_end_date, exclude_lease_id=lease_id)

    update_data = {
        "end_date": renewal_in.new_end_date,
        "status": "renewed"
    }

    if renewal_in.new_rent_amount:
        update_data["rent_amount"] = renewal_in.new_rent_amount

    updated = repo_update_lease(db, lease, **update_data)
    return updated


@router.post("/{lease_id}/terminate", response_model=LeaseOut)
def terminate(lease_id: int, termination_in: LeaseTerminate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Terminate a lease."""
    lease = repo_get_lease(db, lease_id)
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to terminate leases")

    property_obj = repo_get_property(db, lease.property_id)
    if not property_obj or not can_manage_lease(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to terminate this lease")

    update_data = {
        "end_date": termination_in.termination_date,
        "status": "terminated"
    }

    if termination_in.notes:
        update_data["notes"] = termination_in.notes

    updated = repo_update_lease(db, lease, **update_data)
    return updated
