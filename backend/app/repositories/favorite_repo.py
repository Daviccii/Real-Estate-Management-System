from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.favorite import Favorite
from app.models.property import Property


def get_favorite(db: Session, user_id: int, property_id: int) -> Optional[Favorite]:
    return db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.property_id == property_id).first()


def list_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Favorite]:
    return db.query(Favorite).filter(Favorite.user_id == user_id).order_by(Favorite.created_at.desc()).offset(skip).limit(limit).all()


def add_favorite(db: Session, user_id: int, property_id: int) -> Favorite:
    favorite = Favorite(user_id=user_id, property_id=property_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def remove_favorite(db: Session, user_id: int, property_id: int) -> bool:
    favorite = get_favorite(db, user_id, property_id)
    if favorite:
        db.delete(favorite)
        db.commit()
        return True
    return False


def is_favorite(db: Session, user_id: int, property_id: int) -> bool:
    return db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.property_id == property_id).first() is not None