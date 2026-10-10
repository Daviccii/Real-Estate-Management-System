from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.roles import get_current_user
from app.models.user import User
from app.models.property import Property
from app.models.building import Building
from app.models.audit_log import AuditLog
from app.schemas.building import BuildingCreate, BuildingUpdate, BuildingOut

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=List[BuildingOut])
def list_buildings(
    property_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Building)
    if property_id:
        query = query.filter(Building.property_id == property_id)
    buildings = query.order_by(Building.name.asc(), Building.id.asc()).offset(skip).limit(limit).all()
    
    result = []
    for b in buildings:
        prop = db.query(Property).filter(Property.id == b.property_id).first()
        out = BuildingOut.model_validate(b)
        if prop:
            out.property_title = prop.title
        result.append(out)
    return result


@router.get("/{building_id}", response_model=BuildingOut)
def get_building(
    building_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    prop = db.query(Property).filter(Property.id == building.property_id).first()
    out = BuildingOut.model_validate(building)
    if prop:
        out.property_title = prop.title
    return out


@router.post("", response_model=BuildingOut, status_code=status.HTTP_201_CREATED)
def create_building(
    payload: BuildingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prop = db.query(Property).filter(Property.id == payload.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Referenced property not found")
    
    building = Building(
        property_id=payload.property_id,
        name=payload.name,
        total_floors=payload.total_floors or 1,
        units_count=payload.units_count or 0,
        amenities=payload.amenities,
        year_built=payload.year_built,
        description=payload.description
    )
    db.add(building)
    db.commit()
    db.refresh(building)

    # Record audit log
    audit = AuditLog(
        actor_id=current_user.id,
        action="create_building",
        entity_type="building",
        entity_id=building.id,
        changes=f"Created building {building.name} for property {prop.title}"
    )
    db.add(audit)
    db.commit()

    out = BuildingOut.model_validate(building)
    out.property_title = prop.title
    return out


@router.put("/{building_id}", response_model=BuildingOut)
def update_building(
    building_id: int,
    payload: BuildingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(building, field, val)
    
    db.commit()
    db.refresh(building)

    prop = db.query(Property).filter(Property.id == building.property_id).first()
    out = BuildingOut.model_validate(building)
    if prop:
        out.property_title = prop.title
    return out


@router.delete("/{building_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_building(
    building_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    db.delete(building)
    db.commit()
    return None
