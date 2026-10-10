from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.inquiry import Inquiry


def get_inquiry(db: Session, inquiry_id: int) -> Optional[Inquiry]:
    return db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()


def list_user_inquiries(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Inquiry]:
    return db.query(Inquiry).filter(Inquiry.user_id == user_id).order_by(Inquiry.created_at.desc()).offset(skip).limit(limit).all()


def list_property_inquiries(db: Session, property_id: int, skip: int = 0, limit: int = 100) -> List[Inquiry]:
    return db.query(Inquiry).filter(Inquiry.property_id == property_id).order_by(Inquiry.created_at.desc()).offset(skip).limit(limit).all()


def create_inquiry(db: Session, user_id: int, property_id: int, message: str, status: str = "pending") -> Inquiry:
    inquiry = Inquiry(user_id=user_id, property_id=property_id, message=message, status=status)
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return inquiry


def update_inquiry(db: Session, inquiry_obj: Inquiry, **data) -> Inquiry:
    for key, value in data.items():
        if hasattr(inquiry_obj, key) and value is not None:
            setattr(inquiry_obj, key, value)
    db.add(inquiry_obj)
    db.commit()
    db.refresh(inquiry_obj)
    return inquiry_obj


def delete_inquiry(db: Session, inquiry_obj: Inquiry) -> None:
    db.delete(inquiry_obj)
    db.commit()