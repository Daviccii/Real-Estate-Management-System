import hashlib
import re
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.roles import require_admin, require_management
from app.database.database import get_db
from app.models import Company, CompanyInvitation, User
from app.schemas.company import (
    CompanyCreate,
    CompanyOut,
    InvitationAccept,
    InvitationCreate,
    InvitationOut,
)
from app.utils.security import get_password_hash
from app.utils.time import utc_now

router = APIRouter(prefix="/companies", tags=["companies"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "company"


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.company_id is not None:
        raise HTTPException(status_code=409, detail="User already belongs to a company")
    base_slug = _slugify(payload.name)
    slug = base_slug
    suffix = 1
    while db.query(Company).filter(Company.slug == slug).first():
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    company = Company(name=payload.name.strip(), slug=slug)
    db.add(company)
    db.flush()
    current_user.company_id = company.id
    if current_user.role == "user":
        current_user.role = "admin"
        current_user.roles_csv = "admin"
    db.commit()
    db.refresh(company)
    return company


@router.get("/me", response_model=CompanyOut)
def get_my_company(
    current_user: User = Depends(require_management),
    db: Session = Depends(get_db),
):
    if current_user.company_id is None:
        raise HTTPException(status_code=404, detail="User is not assigned to a company")
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company or not company.is_active:
        raise HTTPException(status_code=404, detail="Company not found or inactive")
    return company


@router.post("/invitations", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: InvitationCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if current_user.company_id is None:
        raise HTTPException(status_code=409, detail="User is not assigned to a company")
    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing and existing.company_id not in (None, current_user.company_id):
        raise HTTPException(status_code=409, detail="User already belongs to another company")
    raw_token = secrets.token_urlsafe(48)
    invitation = CompanyInvitation(
        company_id=current_user.company_id,
        invited_by_id=current_user.id,
        email=email,
        role=payload.role,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=utc_now() + timedelta(days=payload.expires_in_days),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return InvitationOut(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        expires_at=invitation.expires_at,
        token=raw_token,
    )


@router.post("/invitations/accept", response_model=CompanyOut)
def accept_invitation(payload: InvitationAccept, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    invitation = (
        db.query(CompanyInvitation)
        .filter(
            CompanyInvitation.token_hash == token_hash,
            CompanyInvitation.accepted_at.is_(None),
            CompanyInvitation.expires_at > utc_now(),
        )
        .with_for_update()
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=400, detail="Invitation is invalid or expired")

    user = db.query(User).filter(User.email == invitation.email).with_for_update().first()
    if user and user.company_id not in (None, invitation.company_id):
        raise HTTPException(status_code=409, detail="User already belongs to another company")
    if not user:
        user = User(
            email=invitation.email,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name,
            role=invitation.role,
            roles_csv=invitation.role,
            company_id=invitation.company_id,
            is_verified=True,
        )
        db.add(user)
    else:
        user.company_id = invitation.company_id
        if payload.full_name:
            user.full_name = payload.full_name
        user.hashed_password = get_password_hash(payload.password)
        user.role = invitation.role
        user.roles_csv = invitation.role
        user.is_verified = True
    invitation.accepted_at = utc_now()
    db.commit()
    company = db.query(Company).filter(Company.id == invitation.company_id).first()
    if not company:
        raise HTTPException(status_code=500, detail="Invitation company no longer exists")
    return company
