from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.roles import require_staff
from app.config.settings import settings
from app.database.database import get_db
from app.models.property import Property
from app.models.property_media import PropertyMedia
from app.models.user import User
from app.observability.metrics import increment
from app.schemas.property_media import PropertyMediaCreate, PropertyMediaOut
from app.services.cache_service import invalidate_property_cache
from app.utils.file_validation import FileValidationError, validate_upload
from app.utils.sanitization import sanitize_string

router = APIRouter(prefix="/properties", tags=["property-media"])


def get_property_or_404(property_id: int, db: Session) -> Property:
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return property_obj


@router.get("/{property_id}/media", response_model=List[PropertyMediaOut])
def list_property_media(property_id: int, db: Session = Depends(get_db)):
    get_property_or_404(property_id, db)
    return (
        db.query(PropertyMedia)
        .filter(PropertyMedia.property_id == property_id, PropertyMedia.is_public.is_(True))
        .order_by(PropertyMedia.is_primary.desc(), PropertyMedia.id.asc())
        .all()
    )


@router.post("/{property_id}/media", response_model=PropertyMediaOut, status_code=status.HTTP_201_CREATED)
def add_property_media(
    property_id: int,
    payload: PropertyMediaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    get_property_or_404(property_id, db)
    if payload.is_primary:
        db.query(PropertyMedia).filter(PropertyMedia.property_id == property_id).update(
            {PropertyMedia.is_primary: False}, synchronize_session=False
        )
    media = PropertyMedia(property_id=property_id, **payload.model_dump())
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.post("/{property_id}/media/upload", response_model=PropertyMediaOut, status_code=status.HTTP_201_CREATED)
async def upload_property_media(
    property_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """
    Upload a property photo/document with security validation.

    File type is verified from magic bytes (not the filename or Content-Type),
    size is capped by MAX_UPLOAD_FILE_BYTES, and files are stored under a
    random name in UPLOAD_DIR.
    """
    get_property_or_404(property_id, db)

    file_bytes = await file.read()
    try:
        media_type, extension, stored_filename = validate_upload(file_bytes)
    except FileValidationError as exc:
        increment("uploads_rejected_total")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    upload_dir = settings.upload_root
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / stored_filename
    if destination.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload storage conflict")
    destination.write_bytes(file_bytes)

    if is_primary:
        db.query(PropertyMedia).filter(PropertyMedia.property_id == property_id).update(
            {PropertyMedia.is_primary: False}, synchronize_session=False
        )

    media = PropertyMedia(
        property_id=property_id,
        url=f"/media/uploads/{stored_filename}",
        media_type="document" if extension == ".pdf" else "image",
        source_type="OWNER_UPLOADED",
        source_name=sanitize_string(file.filename or stored_filename, max_length=255),
        caption=sanitize_string(caption, max_length=500) if caption else None,
        is_primary=is_primary,
        is_public=True,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    increment("uploads_accepted_total")
    invalidate_property_cache()
    return media


@router.delete("/{property_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property_media(
    property_id: int,
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    media = (
        db.query(PropertyMedia)
        .filter(PropertyMedia.id == media_id, PropertyMedia.property_id == property_id)
        .first()
    )
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property media not found")
    db.delete(media)
    db.commit()
    invalidate_property_cache()
