from typing import List, Optional
from datetime import datetime
from app.utils.time import utc_now
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import require_user
from app.models.property import Property
from app.models.lead import Lead
from app.models.viewing import Viewing
from app.models.application import RentalApplication
from app.models.inquiry import Inquiry
from app.models.user import User

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/dashboard")
def get_agent_dashboard(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns Agent workspace metrics: leads pipeline counts, scheduled viewings today, active listings, and closed deals.
    """
    agent_id = current_user.id

    # Listings represented by this agent
    listings = db.query(Property).filter(Property.agent_id == agent_id).all()
    
    # Leads
    leads = db.query(Lead).filter(Lead.agent_id == agent_id).all()
    new_leads = len([l for l in leads if l.stage == "new"])
    active_leads = len([l for l in leads if l.stage in ["contacted", "interested", "viewing", "applied"]])
    closed_leads = len([l for l in leads if l.stage == "closed"])
    
    # Commissions from closed leads
    total_commission = sum(float(l.commission_amount) for l in leads if l.stage == "closed" and l.commission_amount)

    # Viewings
    today_str = utc_now().strftime("%Y-%m-%d")
    upcoming_viewings = db.query(Viewing).filter(
        Viewing.host_user_id == agent_id,
        Viewing.status.in_(["requested", "confirmed"])
    ).all()

    viewings_today = [v for v in upcoming_viewings if v.viewing_date == today_str]

    # Inquiries on represented properties
    prop_ids = [p.id for p in listings]
    pending_inquiries = db.query(Inquiry).filter(
        Inquiry.property_id.in_(prop_ids),
        Inquiry.status == "pending"
    ).count() if prop_ids else 0

    return {
        "listings_count": len(listings),
        "total_leads": len(leads),
        "new_leads": new_leads,
        "active_leads": active_leads,
        "closed_deals": closed_leads,
        "total_commission": round(total_commission, 2),
        "viewings_today": len(viewings_today),
        "upcoming_viewings_count": len(upcoming_viewings),
        "pending_inquiries": pending_inquiries,
        "pipeline_breakdown": {
            "new": len([l for l in leads if l.stage == "new"]),
            "contacted": len([l for l in leads if l.stage == "contacted"]),
            "interested": len([l for l in leads if l.stage == "interested"]),
            "viewing": len([l for l in leads if l.stage == "viewing"]),
            "applied": len([l for l in leads if l.stage == "applied"]),
            "approved": len([l for l in leads if l.stage == "approved"]),
            "closed": closed_leads,
            "lost": len([l for l in leads if l.stage == "lost"]),
        }
    }


@router.get("/listings")
def get_agent_listings(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    List properties represented by current agent.
    """
    props = db.query(Property).filter(Property.agent_id == current_user.id).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "city": p.city,
            "county": p.county,
            "price": p.price_label or p.price,
            "property_type": p.property_type,
            "status": p.status,
            "purpose": p.purpose,
            "bedrooms": p.bedrooms,
            "bathrooms": p.bathrooms,
            "image_url": p.image_url,
            "is_verified": p.is_verified,
            "owner_name": p.owner.full_name if p.owner else "Owner",
            "created_at": p.created_at
        }
        for p in props
    ]


@router.get("/workspace")
def get_agent_workspace(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns Agent workspace metrics matching frontend AgentWorkspaceData.
    """
    agent_id = current_user.id
    listings = db.query(Property).filter(Property.agent_id == agent_id).all()
    leads = db.query(Lead).filter(Lead.agent_id == agent_id).all()
    upcoming_viewings = db.query(Viewing).filter(
        Viewing.host_user_id == agent_id,
        Viewing.status.in_(["requested", "confirmed"])
    ).count()
    prop_ids = [p.id for p in listings]
    pending_apps = db.query(RentalApplication).filter(
        RentalApplication.property_id.in_(prop_ids),
        RentalApplication.status.in_(["submitted", "under_review"])
    ).count() if prop_ids else 0
    total_commission = sum(float(l.commission_amount) for l in leads if l.stage == "closed" and l.commission_amount)

    return {
        "total_leads": len(leads),
        "active_listings": len(listings),
        "upcoming_viewings": upcoming_viewings,
        "pending_applications": pending_apps,
        "total_commissions_earned": round(total_commission, 2)
    }


@router.get("/commissions")
def get_agent_commissions(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns leads list and total commission earned for current agent.
    """
    agent_id = current_user.id
    leads = db.query(Lead).filter(Lead.agent_id == agent_id).order_by(Lead.updated_at.desc()).all()
    total_commission = sum(float(l.commission_amount) for l in leads if l.stage == "closed" and l.commission_amount)

    return {
        "leads": [
            {
                "id": l.id,
                "agent_id": l.agent_id,
                "prospect_id": l.prospect_id,
                "property_id": l.property_id,
                "stage": l.stage,
                "prospect_name": l.prospect_name,
                "prospect_email": l.prospect_email,
                "prospect_phone": l.prospect_phone,
                "estimated_budget": l.estimated_budget,
                "preferred_location": l.preferred_location,
                "notes": l.notes,
                "commission_amount": l.commission_amount,
                "created_at": l.created_at.isoformat() if hasattr(l.created_at, "isoformat") else str(l.created_at),
                "updated_at": l.updated_at.isoformat() if hasattr(l.updated_at, "isoformat") else str(l.updated_at),
                "property_name": l.property.name if l.property else None,
            }
            for l in leads
        ],
        "total_commission": round(total_commission, 2)
    }


@router.get("/leads")
def get_agent_leads_alias(
    stage: Optional[str] = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    List leads managed by current agent.
    """
    q = db.query(Lead).filter(Lead.agent_id == current_user.id)
    if stage:
        q = q.filter(Lead.stage == stage)
    leads = q.order_by(Lead.updated_at.desc()).all()
    return [
        {
            "id": l.id,
            "agent_id": l.agent_id,
            "prospect_id": l.prospect_id,
            "property_id": l.property_id,
            "stage": l.stage,
            "prospect_name": l.prospect_name,
            "prospect_email": l.prospect_email,
            "prospect_phone": l.prospect_phone,
            "estimated_budget": l.estimated_budget,
            "preferred_location": l.preferred_location,
            "notes": l.notes,
            "commission_amount": l.commission_amount,
            "created_at": l.created_at.isoformat() if hasattr(l.created_at, "isoformat") else str(l.created_at),
            "updated_at": l.updated_at.isoformat() if hasattr(l.updated_at, "isoformat") else str(l.updated_at),
            "property_name": l.property.name if l.property else None,
        }
        for l in leads
    ]


@router.get("/viewings")
def get_agent_viewings_alias(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    List viewings hosted or attended by current agent.
    """
    viewings = db.query(Viewing).filter(Viewing.host_user_id == current_user.id).order_by(Viewing.viewing_date.desc()).all()
    return [
        {
            "id": v.id,
            "property_id": v.property_id,
            "prospect_id": v.prospect_id,
            "host_user_id": v.host_user_id,
            "viewing_date": v.viewing_date,
            "start_time": v.start_time,
            "end_time": v.end_time,
            "status": v.status,
            "prospect_name": v.prospect.full_name if v.prospect else "Prospect",
            "prospect_phone": getattr(v.prospect, "phone", None) if v.prospect else None,
            "notes": v.notes,
            "created_at": v.created_at.isoformat() if hasattr(v.created_at, "isoformat") else str(v.created_at),
            "property_name": v.property.name if v.property else None,
        }
        for v in viewings
    ]


