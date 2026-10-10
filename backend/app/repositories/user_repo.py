from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.user import User


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, *, email: str, hashed_password: str, full_name: str | None = None, role: str = "user") -> User:
    user = User(email=email, hashed_password=hashed_password, full_name=full_name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
