from typing import Optional, List
from sqlalchemy import update
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.lease import Lease
from app.models.property import Property


def get_lease(db: Session, lease_id: int) -> Optional[Lease]:
    return db.query(Lease).filter(Lease.id == lease_id).first()


def list_leases(db: Session, skip: int = 0, limit: int = 100, *, property_id: Optional[int] = None, unit_id: Optional[int] = None, tenant_id: Optional[int] = None, status: Optional[str] = None, authorized_user_id: Optional[int] = None) -> List[Lease]:
    q = db.query(Lease)
    if property_id:
        q = q.filter(Lease.property_id == property_id)
    if unit_id:
        q = q.filter(Lease.unit_id == unit_id)
    if tenant_id:
        q = q.filter(Lease.tenant_id == tenant_id)
    if status:
        q = q.filter(Lease.status == status)
    if authorized_user_id is not None:
        q = q.join(Property, Lease.property_id == Property.id).filter(
            (Property.owner_id == authorized_user_id) |
            (Property.manager_id == authorized_user_id)
        )
    return q.order_by(Lease.created_at.desc(), Lease.id.desc()).offset(skip).limit(limit).all()


def mark_expiring_leases(
    db: Session,
    *,
    expiry_threshold: datetime,
    authorized_user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> int:
    query = db.query(Lease).filter(
        Lease.status == "active",
        Lease.end_date <= expiry_threshold,
    )
    if authorized_user_id is not None:
        query = query.join(Property, Lease.property_id == Property.id).filter(
            (Property.owner_id == authorized_user_id) |
            (Property.manager_id == authorized_user_id)
        )
    if company_id is not None:
        query = query.join(Property, Lease.property_id == Property.id) if authorized_user_id is None else query
        query = query.filter(Property.company_id == company_id)
    leases = query.with_for_update().all()
    for lease in leases:
        lease.status = "expiring soon"
    return len(leases)


def create_lease(db: Session, **data) -> Lease:
    lease = Lease(**data)
    db.add(lease)
    db.commit()
    db.refresh(lease)
    return lease


def update_lease(db: Session, lease_obj: Lease, **data) -> Lease:
    for key, value in data.items():
        if hasattr(lease_obj, key) and value is not None:
            setattr(lease_obj, key, value)
    db.add(lease_obj)
    db.commit()
    db.refresh(lease_obj)
    return lease_obj


def delete_lease(db: Session, lease_obj: Lease) -> None:
    db.delete(lease_obj)
    db.commit()