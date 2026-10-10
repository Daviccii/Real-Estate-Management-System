from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserOut
from app.database.database import get_db
from app.utils.security import get_password_hash
from app.auth.deps import get_current_user
from app.auth.roles import require_admin, verify_role
from app.repositories.user_repo import get_user_by_email, create_user as repo_create_user, get_user as repo_get_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Public user registration - defaults to 'user' role, ignores provided role for security."""
    existing = get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    # Force role to 'user' for public registration (security measure)
    db_user = repo_create_user(db, email=user.email, hashed_password=get_password_hash(user.password), full_name=user.full_name, role="user")
    return db_user


@router.post("/admin", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_as_admin(user: UserCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Admin-only endpoint to create users with specific roles."""
    existing = get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    db_user = repo_create_user(db, email=user.email, hashed_password=get_password_hash(user.password), full_name=user.full_name, role=user.role)
    return db_user


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserOut)
def read_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Use centralized role checking
    if current_user.id != user_id and not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    user = repo_get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
