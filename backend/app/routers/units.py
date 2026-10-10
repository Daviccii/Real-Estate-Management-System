"""
Unit management endpoints.
Supports CRUD operations for property units with role-based authorization.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.schemas.unit import UnitCreate, UnitUpdate, UnitOut
from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import verify_role, require_admin, require_management
from app.repositories.unit_repo import (
    create_unit,
    get_unit as repo_get_unit,
    list_units as repo_list_units,
    update_unit as repo_update_unit,
    delete_unit as repo_delete_unit,
)
from app.repositories.property_repo import get_property as repo_get_property
from app.models import User, Property
from app.config.settings import settings

router = APIRouter(prefix="/units", tags=["units"])


def can_manage_unit(current_user: User, unit_property: Property) -> bool:
    """Check if user can manage a unit based on property ownership/management."""
    if (
        unit_property.company_id is not None
        and current_user.company_id != unit_property.company_id
    ):
        return False
    if verify_role(current_user, ["admin"]):
        return True
    if unit_property.owner_id == current_user.id:
        return True
    if unit_property.manager_id == current_user.id:
        return True
    return False


@router.post("/", response_model=UnitOut, status_code=status.HTTP_201_CREATED)
def create(unit_in: UnitCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new unit. Admin, property owner, or assigned manager can create units."""
    property_obj = repo_get_property(db, unit_in.property_id)
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if not can_manage_unit(current_user, property_obj):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create units for this property"
        )

    unit = create_unit(db, **unit_in.model_dump())
    return unit


@router.get("/", response_model=List[UnitOut])
def list_units(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    property_id: Optional[int] = None,
    status: Optional[str] = None,
    unit_type: Optional[str] = None,
    bedrooms: Optional[int] = None,
    min_rent: Optional[str] = None,
    max_rent: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List filtered and authorized units with database-level pagination."""
    authorized_user_id = None
    if not verify_role(current_user, ["admin"]):
        authorized_user_id = current_user.id
    try:
        return repo_list_units(
            db, skip=skip, limit=limit, property_id=property_id, status=status,
            unit_type=unit_type, bedrooms=bedrooms, min_rent=min_rent,
            max_rent=max_rent, authorized_user_id=authorized_user_id
        )
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Rent filters must be numeric")


@router.get("/properties/{property_id}/units", response_model=List[UnitOut])
def list_property_units(
    property_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all units for a specific property."""
    property_obj = repo_get_property(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if not can_manage_unit(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view units for this property")

    units = repo_list_units(db, skip=skip, limit=limit, property_id=property_id, status=status)
    return units


@router.get("/{unit_id}", response_model=UnitOut)
def read(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get unit details by ID."""
    unit = repo_get_unit(db, unit_id)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    property_obj = repo_get_property(db, unit.property_id)
    if not property_obj or not can_manage_unit(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this unit")

    return unit


@router.put("/{unit_id}", response_model=UnitOut)
def update(unit_id: int, unit_in: UnitUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update unit details."""
    unit = repo_get_unit(db, unit_id)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    property_obj = repo_get_property(db, unit.property_id)
    if not property_obj or not can_manage_unit(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this unit")

    updated = repo_update_unit(db, unit, **unit_in.model_dump(exclude_none=True))
    return updated


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a unit."""
    unit = repo_get_unit(db, unit_id)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    property_obj = repo_get_property(db, unit.property_id)
    if not property_obj or not can_manage_unit(current_user, property_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this unit")

    repo_delete_unit(db, unit)
    return None
