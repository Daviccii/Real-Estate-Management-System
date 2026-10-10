"""
Maintenance management endpoints.
Supports maintenance request workflow with role-based authorization.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.utils.time import utc_now

from app.schemas.maintenance import (
    MaintenanceCreate, MaintenanceUpdate, MaintenanceOut,
    MaintenanceAssign, MaintenanceResolve
)
from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access, verify_role, require_management, require_admin
from app.repositories.maintenance_repo import (
    create_maintenance,
    get_maintenance as repo_get_maintenance,
    list_maintenance as repo_list_maintenance,
    update_maintenance as repo_update_maintenance,
    delete_maintenance as repo_delete_maintenance,
)
from app.repositories.property_repo import get_property as repo_get_property
from app.repositories.user_repo import get_user as repo_get_user
from app.models import User, Property
from app.config.settings import settings

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


def can_manage_maintenance(current_user: User, maintenance_property: Property) -> bool:
    """Check if user can manage maintenance requests based on property ownership/management."""
    if (
        maintenance_property.company_id is not None
        and current_user.company_id != maintenance_property.company_id
    ):
        return False
    if verify_role(current_user, ["admin"]):
        return True
    if maintenance_property.owner_id == current_user.id:
        return True
    if maintenance_property.manager_id == current_user.id:
        return True
    return False


@router.post("/", response_model=MaintenanceOut, status_code=status.HTTP_201_CREATED)
def create(maintenance_in: MaintenanceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new maintenance request. Tenants, admins, and managers can create requests."""
    property_obj = repo_get_property(db, maintenance_in.property_id)
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if not company_resource_access(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if verify_role(current_user, ["tenant"]):
        maintenance_in.tenant_id = current_user.id
    elif verify_role(current_user, ["admin", "manager"]) and not can_manage_maintenance(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to manage this property")
    elif not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create maintenance requests"
        )

    maintenance = create_maintenance(db, **maintenance_in.model_dump())
    return maintenance


@router.get("/", response_model=List[MaintenanceOut])
def list_maintenance(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    property_id: Optional[int] = None,
    unit_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_manager_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List only authorized maintenance requests with database pagination."""
    authorized_user_id = None
    if verify_role(current_user, ["tenant"]):
        tenant_id = current_user.id
    elif verify_role(current_user, ["manager"]):
        authorized_user_id = current_user.id
    elif not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view maintenance requests")
    return repo_list_maintenance(
        db, skip=skip, limit=limit, property_id=property_id,
        unit_id=unit_id, tenant_id=tenant_id, status=status,
        priority=priority, assigned_manager_id=assigned_manager_id,
        authorized_user_id=authorized_user_id
    )


@router.get("/tenants/{tenant_id}/maintenance", response_model=List[MaintenanceOut])
def list_tenant_maintenance(
    tenant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all maintenance requests for a specific tenant."""
    if verify_role(current_user, ["tenant"]):
        if tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view other tenant's requests")
    elif not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view tenant maintenance requests")

    if verify_role(current_user, ["manager"]):
        return repo_list_maintenance(
            db, skip=skip, limit=limit, tenant_id=tenant_id, status=status,
            authorized_user_id=current_user.id
        )

    return repo_list_maintenance(db, skip=skip, limit=limit, tenant_id=tenant_id, status=status)


@router.get("/properties/{property_id}/maintenance", response_model=List[MaintenanceOut])
def list_property_maintenance(
    property_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all maintenance requests for a specific property."""
    property_obj = repo_get_property(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if not can_manage_maintenance(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view maintenance requests for this property")

    requests = repo_list_maintenance(db, skip=skip, limit=limit, property_id=property_id, status=status)
    return requests


@router.get("/{request_id}", response_model=MaintenanceOut)
def read(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get maintenance request details by ID."""
    request = repo_get_maintenance(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")

    if verify_role(current_user, ["tenant"]):
        if request.tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this request")
    elif not verify_role(current_user, ["admin"]):
        property_obj = repo_get_property(db, request.property_id)
        if not property_obj or not can_manage_maintenance(current_user, property_obj):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this request")

    return request


@router.put("/{request_id}", response_model=MaintenanceOut)
def update(request_id: int, maintenance_in: MaintenanceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update maintenance request details."""
    request = repo_get_maintenance(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")

    if verify_role(current_user, ["tenant"]):
        if request.tenant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this request")
        allowed_fields = {"title", "description", "category"}
        update_data = {k: v for k, v in maintenance_in.model_dump(exclude_none=True).items() if k in allowed_fields}
    elif not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify maintenance requests")
    else:
        update_data = maintenance_in.model_dump(exclude_none=True)

    if update_data.get("status") == "completed" and not request.resolved_at:
        update_data["resolved_at"] = utc_now()

    updated = repo_update_maintenance(db, request, **update_data)
    return updated


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a maintenance request (admin only)."""
    if not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete maintenance requests")

    request = repo_get_maintenance(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")

    repo_delete_maintenance(db, request)
    return None


@router.post("/{request_id}/assign", response_model=MaintenanceOut)
def assign(request_id: int, assign_in: MaintenanceAssign, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Assign a maintenance request to a manager."""
    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to assign maintenance requests")

    request = repo_get_maintenance(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")

    assigned_manager = repo_get_user(db, assign_in.assigned_manager_id)
    if not assigned_manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned manager not found")

    if not verify_role(assigned_manager, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only assign to admins or managers")

    update_data = {
        "assigned_manager_id": assign_in.assigned_manager_id,
        "status": "assigned"
    }

    if assign_in.notes:
        update_data["notes"] = assign_in.notes

    updated = repo_update_maintenance(db, request, **update_data)
    return updated


@router.post("/{request_id}/resolve", response_model=MaintenanceOut)
def resolve(request_id: int, resolve_in: MaintenanceResolve, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Resolve a maintenance request."""
    if not verify_role(current_user, ["admin", "manager"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to resolve maintenance requests")

    request = repo_get_maintenance(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")

    update_data = {
        "status": "completed",
        "resolved_at": utc_now()
    }

    if resolve_in.cost:
        update_data["cost"] = resolve_in.cost

    if resolve_in.resolution_notes:
        current_notes = request.notes or ""
        update_data["notes"] = f"{current_notes}\n\nResolution: {resolve_in.resolution_notes}" if current_notes else resolve_in.resolution_notes

    updated = repo_update_maintenance(db, request, **update_data)
    return updated
