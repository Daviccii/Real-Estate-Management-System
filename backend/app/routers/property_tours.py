from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.roles import verify_role
from app.database.database import get_db
from app.models.property import Property
from app.models.property_tour import PropertyTour
from app.models.user import User
from app.schemas.property_tour import PropertyTourCreate, PropertyTourOut, PropertyTourUpdate
from app.services.cache_service import invalidate_property_cache
from app.services.tour_service import parse_tour_url
from app.utils.sanitization import sanitize_string

router = APIRouter(prefix="/properties", tags=["property-tours"])


def get_property_or_404(property_id: int, db: Session) -> Property:
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return property_obj


def _ensure_can_manage(prop: Property, current_user: User) -> None:
    if prop.owner_id != current_user.id and not verify_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage tours for this property",
        )


def get_tour_or_404(property_id: int, tour_id: int, db: Session) -> PropertyTour:
    tour = (
        db.query(PropertyTour)
        .filter(PropertyTour.id == tour_id, PropertyTour.property_id == property_id)
        .first()
    )
    if not tour:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property tour not found")
    return tour


@router.get("/{property_id}/tours", response_model=List[PropertyTourOut])
def list_property_tours(property_id: int, db: Session = Depends(get_db)):
    get_property_or_404(property_id, db)
    return (
        db.query(PropertyTour)
        .filter(PropertyTour.property_id == property_id)
        .order_by(PropertyTour.sort_order.asc(), PropertyTour.id.asc())
        .all()
    )


@router.post("/{property_id}/tours", response_model=PropertyTourOut, status_code=status.HTTP_201_CREATED)
def add_property_tour(
    property_id: int,
    payload: PropertyTourCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = get_property_or_404(property_id, db)
    _ensure_can_manage(prop, current_user)

    parsed = parse_tour_url(payload.url)
    tour = PropertyTour(
        property_id=property_id,
        title=sanitize_string(payload.title, max_length=255) if payload.title else None,
        url=payload.url.strip(),
        provider=parsed.provider,
        embed_url=parsed.embed_url,
        thumbnail_url=payload.thumbnail_url,
        sort_order=payload.sort_order or 0,
    )
    db.add(tour)
    db.commit()
    db.refresh(tour)
    invalidate_property_cache()
    return tour


@router.patch("/{property_id}/tours/{tour_id}", response_model=PropertyTourOut)
def update_property_tour(
    property_id: int,
    tour_id: int,
    payload: PropertyTourUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = get_property_or_404(property_id, db)
    _ensure_can_manage(prop, current_user)
    tour = get_tour_or_404(property_id, tour_id, db)

    data = payload.model_dump(exclude_unset=True)
    if data.get("url") is not None:
        parsed = parse_tour_url(data["url"])
        tour.url = data["url"].strip()
        tour.provider = parsed.provider
        tour.embed_url = parsed.embed_url
    if "title" in data:
        tour.title = sanitize_string(data["title"], max_length=255) if data["title"] else None
    if "thumbnail_url" in data:
        tour.thumbnail_url = data["thumbnail_url"]
    if data.get("sort_order") is not None:
        tour.sort_order = data["sort_order"]

    db.commit()
    db.refresh(tour)
    invalidate_property_cache()
    return tour


@router.delete("/{property_id}/tours/{tour_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property_tour(
    property_id: int,
    tour_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = get_property_or_404(property_id, db)
    _ensure_can_manage(prop, current_user)
    tour = get_tour_or_404(property_id, tour_id, db)
    db.delete(tour)
    db.commit()
    invalidate_property_cache()
    return None
