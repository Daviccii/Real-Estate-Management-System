from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.property import Property


def get_payment(db: Session, payment_id: int) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.id == payment_id).first()


def list_payments(db: Session, skip: int = 0, limit: int = 100, *, property_id: Optional[int] = None, unit_id: Optional[int] = None, tenant_id: Optional[int] = None, lease_id: Optional[int] = None, status: Optional[str] = None, authorized_user_id: Optional[int] = None) -> List[Payment]:
    q = db.query(Payment)
    if property_id:
        q = q.filter(Payment.property_id == property_id)
    if unit_id:
        q = q.filter(Payment.unit_id == unit_id)
    if tenant_id:
        q = q.filter(Payment.tenant_id == tenant_id)
    if lease_id:
        q = q.filter(Payment.lease_id == lease_id)
    if status:
        q = q.filter(Payment.status == status)
    if authorized_user_id is not None:
        q = q.join(Property, Payment.property_id == Property.id).filter(
            (Property.owner_id == authorized_user_id) |
            (Property.manager_id == authorized_user_id)
        )
    return q.order_by(Payment.created_at.desc(), Payment.id.desc()).offset(skip).limit(limit).all()


def create_payment(db: Session, **data) -> Payment:
    payment = Payment(**data)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def update_payment(db: Session, payment_obj: Payment, **data) -> Payment:
    for key, value in data.items():
        if hasattr(payment_obj, key) and value is not None:
            setattr(payment_obj, key, value)
    db.add(payment_obj)
    db.commit()
    db.refresh(payment_obj)
    return payment_obj


def delete_payment(db: Session, payment_obj: Payment) -> None:
    db.delete(payment_obj)
    db.commit()