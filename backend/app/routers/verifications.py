from typing import List, Optional
from datetime import datetime
import json
from app.utils.time import utc_now
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import require_user, require_admin
from app.models.verification import VerificationRecord
from app.models.user import User
from app.models.property import Property
from app.models.service_marketplace import ServiceProviderProfile
from app.models.verification_evidence import VerificationEvidence
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/verifications", tags=["verifications"])


class VerificationSubmit(BaseModel):
    entity_type: str  # user, agent, owner, property, service_provider
    entity_id: int
    verification_type: str  # national_id, real_estate_license, title_deed, business_permit
    submitted_data_json: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    document_url: Optional[str] = None
    property_id: Optional[int] = None
    business_name: Optional[str] = None
    license_number: Optional[str] = None


class VerificationReview(BaseModel):
    status: str  # verified, rejected
    review_notes: Optional[str] = None


class VerificationEvidenceCreate(BaseModel):
    evidence_type: str
    reference: str
    description: Optional[str] = None


@router.post("/submit")
def submit_for_verification(
    payload: VerificationSubmit,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Submit an identity, property, or license verification request.
    """
    submitted_data = {}
    if payload.submitted_data_json:
        try:
            submitted_data = json.loads(payload.submitted_data_json)
        except json.JSONDecodeError:
            submitted_data = {"raw_reference": payload.submitted_data_json}
    submitted_data.update({
        key: value for key, value in {
            "id_type": payload.id_type,
            "id_number": payload.id_number,
            "document_url": payload.document_url,
            "property_id": payload.property_id,
            "business_name": payload.business_name,
            "license_number": payload.license_number,
        }.items() if value is not None
    })
    rec = VerificationRecord(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        verification_type=payload.verification_type,
        submitted_data_json=json.dumps(submitted_data) if submitted_data else None,
        status="pending"
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    log_audit_event(db, current_user.id, "SUBMIT_VERIFICATION", payload.entity_type, payload.entity_id)
    return {"message": "Verification submitted for administrative review", "id": rec.id, "status": rec.status}


@router.get("/pending", dependencies=[Depends(require_admin)])
def list_pending_verifications(db: Session = Depends(get_db)):
    """
    Administrator verification queue.
    """
    recs = db.query(VerificationRecord).filter(VerificationRecord.status == "pending").order_by(VerificationRecord.created_at.desc()).all()
    return recs


@router.get("/status/{entity_type}/{entity_id}")
def get_verification_status(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
):
    """
    Check verification badge status for any entity.
    """
    rec = db.query(VerificationRecord).filter(
        VerificationRecord.entity_type == entity_type,
        VerificationRecord.entity_id == entity_id,
        VerificationRecord.status == "verified"
    ).first()

    return {"is_verified": rec is not None, "status": rec.status if rec else "unverified"}


@router.post("/{record_id}/evidence", dependencies=[Depends(require_user)])
def add_verification_evidence(
    record_id: int,
    payload: VerificationEvidenceCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    rec = db.query(VerificationRecord).filter(VerificationRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Verification record not found")
    evidence = VerificationEvidence(
        verification_id=record_id,
        evidence_type=payload.evidence_type,
        reference=payload.reference,
        description=payload.description,
        created_by_id=current_user.id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return {"id": evidence.id, "verification_id": record_id, "status": rec.status}


@router.get("/{record_id}/evidence", dependencies=[Depends(require_admin)])
def list_verification_evidence(record_id: int, db: Session = Depends(get_db)):
    if not db.query(VerificationRecord).filter(VerificationRecord.id == record_id).first():
        raise HTTPException(status_code=404, detail="Verification record not found")
    return (
        db.query(VerificationEvidence)
        .filter(VerificationEvidence.verification_id == record_id)
        .order_by(VerificationEvidence.created_at.desc())
        .all()
    )


@router.put("/{record_id}/review", dependencies=[Depends(require_admin)])
def review_verification(
    record_id: int,
    payload: VerificationReview,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin reviews and approves/rejects a verification request.
    Applies the verified flag to the corresponding entity table!
    """
    rec = db.query(VerificationRecord).filter(VerificationRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Verification record not found")

    rec.status = payload.status
    rec.reviewed_by_id = current_user.id
    rec.review_notes = payload.review_notes
    rec.reviewed_at = utc_now()

    # Cascade the verified badge to the entity
    if payload.status == "verified":
        if rec.entity_type in ["user", "agent", "owner"]:
            u = db.query(User).filter(User.id == rec.entity_id).first()
            if u:
                u.is_verified = True
        elif rec.entity_type == "property":
            p = db.query(Property).filter(Property.id == rec.entity_id).first()
            if p:
                p.is_verified = True
                p.verification_status = "verified"
                p.last_verified_at = utc_now()
        elif rec.entity_type == "service_provider":
            sp = db.query(ServiceProviderProfile).filter(ServiceProviderProfile.id == rec.entity_id).first()
            if sp:
                sp.is_verified = True
    elif rec.entity_type == "property":
        p = db.query(Property).filter(Property.id == rec.entity_id).first()
        if p:
            p.is_verified = False
            p.verification_status = payload.status

    db.commit()
    log_audit_event(db, current_user.id, f"VERIFICATION_{payload.status.upper()}", rec.entity_type, rec.entity_id)
    return {"message": f"Verification updated to {payload.status}", "record_id": rec.id}
