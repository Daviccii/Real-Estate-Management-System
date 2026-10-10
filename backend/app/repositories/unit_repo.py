from typing import Optional, List
from sqlalchemy import Float, cast
from sqlalchemy.orm import Session
from app.models.unit import Unit
from app.models.property import Property


def get_unit(db: Session, unit_id: int, *, for_update: bool = False) -> Optional[Unit]:
    query = db.query(Unit).filter(Unit.id == unit_id)
    if for_update:
        query = query.with_for_update()
    return query.first()


def list_units(db: Session, skip: int = 0, limit: int = 100, *, property_id: Optional[int] = None, status: Optional[str] = None, unit_type: Optional[str] = None, bedrooms: Optional[int] = None, min_rent: Optional[str] = None, max_rent: Optional[str] = None, authorized_user_id: Optional[int] = None) -> List[Unit]:
    q = db.query(Unit)
    if property_id:
        q = q.filter(Unit.property_id == property_id)
    if status:
        q = q.filter(Unit.status == status)
    if unit_type:
        q = q.filter(Unit.unit_type == unit_type)
    if bedrooms:
        q = q.filter(Unit.bedrooms == bedrooms)
    if min_rent:
        q = q.filter(cast(Unit.rent, Float) >= float(min_rent))
    if max_rent:
        q = q.filter(cast(Unit.rent, Float) <= float(max_rent))
    if authorized_user_id is not None:
        q = q.join(Property, Unit.property_id == Property.id).filter(
            (Property.owner_id == authorized_user_id) |
            (Property.manager_id == authorized_user_id)
        )
    return q.order_by(Unit.id.desc()).offset(skip).limit(limit).all()


def create_unit(db: Session, **data) -> Unit:
    unit = Unit(**data)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def update_unit(db: Session, unit_obj: Unit, **data) -> Unit:
    for key, value in data.items():
        if hasattr(unit_obj, key) and value is not None:
            setattr(unit_obj, key, value)
    db.add(unit_obj)
    db.commit()
    db.refresh(unit_obj)
    return unit_obj


def delete_unit(db: Session, unit_obj: Unit) -> None:
    db.delete(unit_obj)
    db.commit()