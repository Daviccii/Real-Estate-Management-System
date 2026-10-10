from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.favorite import FavoriteCreate, FavoriteOut
from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access
from app.repositories.favorite_repo import (
    add_favorite,
    remove_favorite,
    list_user_favorites,
    is_favorite,
)
from app.models.user import User
from app.models.property import Property

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def add_property_to_favorites(
    favorite_in: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a property to user's favorites."""
    prop = db.query(Property).filter(Property.id == favorite_in.property_id).first()
    if not prop or not company_resource_access(current_user, prop):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    # Check if already favorited
    if is_favorite(db, current_user.id, favorite_in.property_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property already in favorites"
        )
    
    return add_favorite(db, user_id=current_user.id, property_id=favorite_in.property_id)


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_property_from_favorites(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a property from user's favorites."""
    success = remove_favorite(db, current_user.id, property_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    return None


@router.get("/", response_model=List[FavoriteOut])
def list_favorites(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all favorites for the current user."""
    return list_user_favorites(db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{property_id}", response_model=dict)
def check_favorite_status(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if a property is in user's favorites."""
    return {"is_favorite": is_favorite(db, current_user.id, property_id)}