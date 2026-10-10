from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access, require_agent, require_staff, require_user, same_company
from app.models.lead import Lead
from app.models.property import Property
from app.models.inquiry import Inquiry
from app.models.user import User
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadCreate(BaseModel):
    property_id: Optional[int] = None
    prospect_id: Optional[int] = None
    inquiry_id: Optional[int] = None
    prospect_name: Optional[str] = None
    prospect_email: Optional[str] = None
    prospect_phone: Optional[str] = None
    estimated_budget: Optional[str] = None
    preferred_location: Optional[str] = None
    notes: Optional[str] = None
    stage: Optional[str] = "new"


class LeadStageUpdate(BaseModel):
    stage: str  # new, contacted, interested, viewing, applied, approved, closed, lost
    notes: Optional[str] = None
    commission_amount: Optional[str] = None


class LeadOut(BaseModel):
    id: int
    agent_id: int
    prospect_id: Optional[int]
    property_id: Optional[int]
    inquiry_id: Optional[int]
    stage: str
    prospect_name: Optional[str]
    prospect_email: Optional[str]
    prospect_phone: Optional[str]
    estimated_budget: Optional[str]
    preferred_location: Optional[str]
    notes: Optional[str]
    commission_amount: Optional[str]
    created_at: datetime
    updated_at: datetime
    property_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=LeadOut)
def create_lead(
    payload: LeadCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Create a new prospective lead in the Agent's pipeline.
    """
    if current_user.role not in ("agent", "admin"):
        raise HTTPException(status_code=403, detail="Only agents can create leads")
    prop = None
    if payload.property_id is not None:
        prop = db.query(Property).filter(Property.id == payload.property_id).first()
        if not prop or not company_resource_access(current_user, prop):
            raise HTTPException(status_code=404, detail="Property not found")
    if payload.prospect_id is not None:
        prospect = db.query(User).filter(User.id == payload.prospect_id).first()
        if not prospect or (current_user.company_id is not None and not same_company(current_user, prospect)):
            raise HTTPException(status_code=404, detail="Prospect not found")
    lead = Lead(
        agent_id=current_user.id,
        prospect_id=payload.prospect_id,
        property_id=payload.property_id,
        inquiry_id=payload.inquiry_id,
        stage=payload.stage or "new",
        prospect_name=payload.prospect_name,
        prospect_email=payload.prospect_email,
        prospect_phone=payload.prospect_phone,
        estimated_budget=payload.estimated_budget,
        preferred_location=payload.preferred_location,
        notes=payload.notes,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    log_audit_event(db, current_user.id, "CREATE_LEAD", "lead", lead.id)

    res = LeadOut.model_validate(lead, from_attributes=True)
    if lead.property:
        res.property_name = lead.property.name
    return res


@router.get("/", response_model=List[LeadOut])
def get_agent_leads(
    stage: Optional[str] = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns leads assigned to the current agent (or all leads if admin).
    """
    query = db.query(Lead)
    if current_user.role != "admin":
        query = query.filter(Lead.agent_id == current_user.id)

    if stage:
        query = query.filter(Lead.stage == stage)

    leads = query.order_by(Lead.updated_at.desc()).all()

    out = []
    for l in leads:
        item = LeadOut.model_validate(l, from_attributes=True)
        if l.property:
            item.property_name = l.property.name
        out.append(item)
    return out


@router.put("/{lead_id}/stage", response_model=LeadOut)
@router.patch("/{lead_id}/stage", response_model=LeadOut)
def update_lead_stage(
    lead_id: int,
    payload: LeadStageUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Move lead to another pipeline stage (e.g. from VIEWING to APPLIED or CLOSED).
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.property and not company_resource_access(current_user, lead.property):
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.agent_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this lead")

    lead.stage = payload.stage
    if payload.notes:
        lead.notes = payload.notes
    if payload.commission_amount:
        lead.commission_amount = payload.commission_amount

    db.commit()
    db.refresh(lead)

    log_audit_event(db, current_user.id, f"LEAD_STAGE_{payload.stage.upper()}", "lead", lead.id)

    res = LeadOut.model_validate(lead, from_attributes=True)
    if lead.property:
        res.property_name = lead.property.name
    return res


@router.post("/from-inquiry/{inquiry_id}", response_model=LeadOut)
def convert_inquiry_to_lead(
    inquiry_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    One-click conversion of an inquiry into a tracked lead in the agent pipeline.
    """
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    if not company_resource_access(current_user, inquiry.property):
        raise HTTPException(status_code=404, detail="Inquiry not found")
    if current_user.role not in ("agent", "admin"):
        raise HTTPException(status_code=403, detail="Only agents can convert inquiries")

    prop = inquiry.property
    prospect = inquiry.user

    lead = Lead(
        agent_id=current_user.id,
        prospect_id=prospect.id if prospect else None,
        property_id=inquiry.property_id,
        inquiry_id=inquiry.id,
        stage="contacted",
        prospect_name=prospect.full_name if prospect else "Prospective Client",
        prospect_email=prospect.email if prospect else None,
        notes=f"Converted from inquiry: {inquiry.message}",
    )
    db.add(lead)
    
    # Mark inquiry as responded
    inquiry.status = "responded"
    db.commit()
    db.refresh(lead)

    log_audit_event(db, current_user.id, "CONVERT_INQUIRY_TO_LEAD", "lead", lead.id)

    res = LeadOut.model_validate(lead, from_attributes=True)
    if prop:
        res.property_name = prop.name
    return res
