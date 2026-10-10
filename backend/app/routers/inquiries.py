from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.inquiry import InquiryCreate, InquiryUpdate, InquiryOut
from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access, verify_role
# FIX: alias the repo functions. The route handlers below were previously
# named identically to these imports (create_inquiry/update_inquiry/
# delete_inquiry), which rebound the module-level names — inside each
# handler, calling e.g. create_inquiry(...) recursed into itself instead of
# calling the repository. That made these three endpoints unusable.
from app.repositories.inquiry_repo import (
    create_inquiry as repo_create_inquiry,
    get_inquiry,
    list_user_inquiries,
    update_inquiry as repo_update_inquiry,
    delete_inquiry as repo_delete_inquiry,
)
from app.models.user import User
from app.models.property import Property

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


@router.post("/", response_model=InquiryOut, status_code=status.HTTP_201_CREATED)
def create_inquiry_endpoint(
    inquiry_in: InquiryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new property inquiry."""
    prop = db.query(Property).filter(Property.id == inquiry_in.property_id).first()
    if not prop or not company_resource_access(current_user, prop):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return repo_create_inquiry(
        db,
        user_id=current_user.id,
        property_id=inquiry_in.property_id,
        message=inquiry_in.message,
        status=inquiry_in.status or "pending"
    )


@router.get("/", response_model=List[InquiryOut])
def list_inquiries(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all inquiries for the current user."""
    return list_user_inquiries(db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{inquiry_id}", response_model=InquiryOut)
def read_inquiry(
    inquiry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific inquiry by ID."""
    inquiry = get_inquiry(db, inquiry_id)
    if not inquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    if not company_resource_access(current_user, inquiry.property):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")

    # Only the inquiry owner or admin can view
    if inquiry.user_id != current_user.id and not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this inquiry")

    return inquiry


@router.put("/{inquiry_id}", response_model=InquiryOut)
def update_inquiry_endpoint(
    inquiry_id: int,
    inquiry_in: InquiryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an inquiry (e.g., change status)."""
    inquiry = get_inquiry(db, inquiry_id)
    if not inquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    if not company_resource_access(current_user, inquiry.property):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")

    # Only the inquiry owner or admin can update
    if inquiry.user_id != current_user.id and not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this inquiry")

    # NOTE: as written, any inquiry owner (a regular tenant/user) can set
    # `status` to anything, including admin-triage values like "resolved" or
    # "closed". If status is meant to be an admin/manager-only field, gate it
    # here, e.g.:
    #   update_data = inquiry_in.model_dump(exclude_none=True)
    #   if not verify_role(current_user, ["admin"]):
    #       update_data.pop("status", None)
    updated = repo_update_inquiry(db, inquiry, **inquiry_in.model_dump(exclude_none=True))
    return updated


@router.delete("/{inquiry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inquiry_endpoint(
    inquiry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an inquiry."""
    inquiry = get_inquiry(db, inquiry_id)
    if not inquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    if not company_resource_access(current_user, inquiry.property):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")

    # Only the inquiry owner or admin can delete
    if inquiry.user_id != current_user.id and not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this inquiry")

    repo_delete_inquiry(db, inquiry)
    return None
