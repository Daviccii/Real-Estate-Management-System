from typing import List, Optional, Union
from datetime import datetime
from app.utils.time import utc_now
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access, require_user, require_service_provider, require_management, require_admin
from app.models.service_marketplace import ServiceProviderProfile, MaintenanceQuote, MaintenanceWorkOrder
from app.models.maintenance import Maintenance
from app.models.property import Property
from app.models.user import User
from app.models.notification import Notification
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/service-marketplace", tags=["service-marketplace"])


class ProfileCreate(BaseModel):
    business_name: Optional[str] = None
    company_name: Optional[str] = None
    specialty: Optional[str] = None
    categories: Optional[List[str]] = None
    license_number: Optional[str] = None
    hourly_rate: Optional[str] = None
    years_experience: Optional[int] = 1
    bio: Optional[str] = None
    service_areas: Optional[Union[str, List[str]]] = None
    is_available: Optional[bool] = True


class QuoteCreate(BaseModel):
    maintenance_id: Optional[int] = None
    request_id: Optional[int] = None
    amount: Optional[str] = None
    quoted_amount: Optional[str] = None
    description: Optional[str] = None
    scope_description: Optional[str] = None
    estimated_hours: Optional[int] = None


class WorkOrderCreate(BaseModel):
    request_id: Optional[int] = None
    maintenance_id: Optional[int] = None
    property_id: Optional[int] = None
    unit_id: Optional[int] = None
    provider_id: int
    scheduled_date: Optional[str] = None
    approved_budget: Optional[str] = None
    notes: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    status: str  # accepted, in_progress, completed, verified
    completion_notes: Optional[str] = None
    completion_photos_json: Optional[str] = None


@router.post("/profile")
@router.post("/providers/profile")
def create_or_update_provider_profile(
    payload: ProfileCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Register or update contractor / service provider professional profile.
    """
    b_name = payload.company_name or payload.business_name or f"{current_user.full_name} Services"
    spec = payload.specialty or (payload.categories[0] if payload.categories else "General Maintenance")
    areas = ", ".join(payload.service_areas) if isinstance(payload.service_areas, list) else payload.service_areas

    profile = db.query(ServiceProviderProfile).filter(ServiceProviderProfile.user_id == current_user.id).first()
    if not profile:
        profile = ServiceProviderProfile(
            user_id=current_user.id,
            business_name=b_name,
            specialty=spec,
            license_number=payload.license_number,
            hourly_rate=payload.hourly_rate,
            years_experience=payload.years_experience or 1,
            bio=payload.bio,
            service_areas=areas,
        )
        db.add(profile)
        if current_user.role == "user":
            current_user.role = "service_provider"
    else:
        profile.business_name = b_name
        profile.specialty = spec
        if payload.license_number is not None:
            profile.license_number = payload.license_number
        if payload.hourly_rate is not None:
            profile.hourly_rate = payload.hourly_rate
        if payload.years_experience is not None:
            profile.years_experience = payload.years_experience
        if payload.bio is not None:
            profile.bio = payload.bio
        if areas is not None:
            profile.service_areas = areas

    db.commit()
    db.refresh(profile)
    log_audit_event(db, current_user.id, "UPDATE_SERVICE_PROVIDER_PROFILE", "service_provider", profile.id)
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "company_name": profile.business_name,
        "business_name": profile.business_name,
        "categories": [profile.specialty],
        "specialty": profile.specialty,
        "service_areas": [s.strip() for s in (profile.service_areas or "").split(",") if s.strip()],
        "hourly_rate": profile.hourly_rate,
        "license_number": profile.license_number,
        "insurance_verified": profile.is_verified,
        "rating_avg": profile.rating or 5.0,
        "completed_jobs_count": 0,
        "is_available": True,
        "created_at": profile.created_at.isoformat() if hasattr(profile.created_at, "isoformat") else str(profile.created_at)
    }


@router.get("/profile/me")
def get_my_provider_profile(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    profile = db.query(ServiceProviderProfile).filter(ServiceProviderProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Service provider profile not found")
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "company_name": profile.business_name,
        "business_name": profile.business_name,
        "categories": [profile.specialty],
        "specialty": profile.specialty,
        "service_areas": [s.strip() for s in (profile.service_areas or "").split(",") if s.strip()],
        "hourly_rate": profile.hourly_rate,
        "license_number": profile.license_number,
        "insurance_verified": profile.is_verified,
        "rating_avg": profile.rating or 5.0,
        "completed_jobs_count": 0,
        "is_available": True,
        "created_at": profile.created_at.isoformat() if hasattr(profile.created_at, "isoformat") else str(profile.created_at)
    }


@router.get("/providers")
def list_verified_service_providers(
    category: Optional[str] = None,
    specialty: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List service providers available for dispatching maintenance jobs.
    """
    query = db.query(ServiceProviderProfile)
    filter_spec = specialty or category
    if filter_spec:
        query = query.filter(ServiceProviderProfile.specialty.ilike(f"%{filter_spec}%"))
    
    profiles = query.all()
    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "company_name": p.business_name,
            "business_name": p.business_name,
            "categories": [p.specialty],
            "specialty": p.specialty,
            "service_areas": [s.strip() for s in (p.service_areas or "").split(",") if s.strip()],
            "hourly_rate": p.hourly_rate,
            "license_number": p.license_number,
            "insurance_verified": p.is_verified,
            "rating_avg": p.rating or 5.0,
            "completed_jobs_count": 0,
            "is_available": True,
            "created_at": p.created_at.isoformat() if hasattr(p.created_at, "isoformat") else str(p.created_at),
            "user_name": p.user.full_name if p.user else None,
            "user_email": p.user.email if p.user else None,
            "user_phone": getattr(p.user, "phone", None) if p.user else None,
        }
        for p in profiles
    ]


@router.get("/providers/{provider_id}")
def get_provider_details(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """
    Get public details of a specific service provider.
    """
    p = db.query(ServiceProviderProfile).filter(
        (ServiceProviderProfile.id == provider_id) | (ServiceProviderProfile.user_id == provider_id)
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Service provider not found")
    return {
        "id": p.id,
        "user_id": p.user_id,
        "company_name": p.business_name,
        "business_name": p.business_name,
        "categories": [p.specialty],
        "specialty": p.specialty,
        "service_areas": [s.strip() for s in (p.service_areas or "").split(",") if s.strip()],
        "hourly_rate": p.hourly_rate,
        "license_number": p.license_number,
        "insurance_verified": p.is_verified,
        "rating_avg": p.rating or 5.0,
        "completed_jobs_count": 0,
        "is_available": True,
        "created_at": p.created_at.isoformat() if hasattr(p.created_at, "isoformat") else str(p.created_at),
        "user_name": p.user.full_name if p.user else None,
        "user_email": p.user.email if p.user else None,
        "user_phone": getattr(p.user, "phone", None) if p.user else None,
    }


@router.post("/quotes")
def submit_maintenance_quote(
    payload: QuoteCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Contractor submits a price quote for a reported maintenance issue.
    """
    m_id = payload.maintenance_id or payload.request_id
    if not m_id:
        raise HTTPException(status_code=400, detail="Missing maintenance_id or request_id")
    
    amt = payload.amount or payload.quoted_amount
    if not amt:
        raise HTTPException(status_code=400, detail="Missing amount or quoted_amount")

    desc = payload.description or payload.scope_description or "Maintenance service quote"

    maint = db.query(Maintenance).filter(Maintenance.id == m_id).first()
    if not maint:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")
    if current_user.role != "service_provider":
        raise HTTPException(status_code=403, detail="Only service providers can submit quotes")
    if not maint.property or not company_resource_access(current_user, maint.property):
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")

    quote = MaintenanceQuote(
        maintenance_id=m_id,
        provider_id=current_user.id,
        amount=str(amt),
        description=desc,
        estimated_hours=payload.estimated_hours,
        status="pending"
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    log_audit_event(db, current_user.id, "SUBMIT_MAINTENANCE_QUOTE", "quote", quote.id)
    return {
        "id": quote.id,
        "request_id": quote.maintenance_id,
        "maintenance_id": quote.maintenance_id,
        "provider_id": quote.provider_id,
        "quoted_amount": quote.amount,
        "amount": quote.amount,
        "estimated_hours": quote.estimated_hours,
        "scope_description": quote.description,
        "description": quote.description,
        "status": quote.status,
        "created_at": quote.created_at.isoformat() if hasattr(quote.created_at, "isoformat") else str(quote.created_at),
        "provider_name": current_user.full_name,
    }


@router.get("/quotes/request/{request_id}")
def get_quotes_for_request(
    request_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    List quotes submitted for a given maintenance ticket.
    """
    maint = db.query(Maintenance).filter(Maintenance.id == request_id).first()
    if not maint or not maint.property or not company_resource_access(current_user, maint.property):
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if current_user.role == "service_provider":
        quotes = db.query(MaintenanceQuote).filter(
            MaintenanceQuote.maintenance_id == request_id,
            MaintenanceQuote.provider_id == current_user.id,
        ).all()
    elif current_user.id == maint.property.owner_id or current_user.id == maint.property.manager_id or current_user.role == "admin":
        quotes = db.query(MaintenanceQuote).filter(MaintenanceQuote.maintenance_id == request_id).all()
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view quotes for this request")
    return [
        {
            "id": q.id,
            "request_id": q.maintenance_id,
            "maintenance_id": q.maintenance_id,
            "provider_id": q.provider_id,
            "quoted_amount": q.amount,
            "amount": q.amount,
            "estimated_hours": q.estimated_hours,
            "scope_description": q.description,
            "description": q.description,
            "status": q.status,
            "created_at": q.created_at.isoformat() if hasattr(q.created_at, "isoformat") else str(q.created_at),
            "provider_name": q.provider.full_name if q.provider else "Contractor",
        }
        for q in quotes
    ]


@router.post("/quotes/{quote_id}/accept")
def accept_quote(
    quote_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Accept a quote and generate an active work order.
    """
    quote = db.query(MaintenanceQuote).filter(MaintenanceQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    maint = quote.maintenance
    if not maint or not maint.property or not company_resource_access(current_user, maint.property):
        raise HTTPException(status_code=404, detail="Quote not found")
    if current_user.id != maint.property.owner_id and current_user.id != maint.property.manager_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only property management can accept quotes")

    quote.status = "accepted"
    if maint:
        maint.status = "in_progress"
        maint.cost = float(quote.amount) if quote.amount and quote.amount.replace('.', '', 1).isdigit() else maint.cost

    work_order = MaintenanceWorkOrder(
        maintenance_id=quote.maintenance_id,
        provider_id=quote.provider_id,
        quote_id=quote.id,
        status="assigned"
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    return {
        "id": work_order.id,
        "request_id": work_order.maintenance_id,
        "property_id": maint.property_id if maint else 1,
        "provider_id": work_order.provider_id,
        "assigned_by_id": current_user.id,
        "status": work_order.status,
        "approved_budget": quote.amount,
        "created_at": work_order.created_at.isoformat() if hasattr(work_order.created_at, "isoformat") else str(work_order.created_at),
        "updated_at": work_order.created_at.isoformat() if hasattr(work_order.created_at, "isoformat") else str(work_order.created_at),
        "property_name": maint.property.name if (maint and maint.property) else "Property",
        "request_title": maint.title if maint else "Maintenance Request",
    }


@router.post("/work-orders")
@router.post("/work-orders/dispatch")
def dispatch_work_order(
    payload: Optional[WorkOrderCreate] = None,
    maintenance_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    quote_id: Optional[int] = None,
    scheduled_date: Optional[str] = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Property Manager or Owner assigns and dispatches a maintenance work order to a service provider.
    """
    m_id = (payload.maintenance_id or payload.request_id) if payload else maintenance_id
    p_id = payload.provider_id if payload else provider_id
    q_id = payload.quote_id if payload else quote_id
    sched_str = payload.scheduled_date if payload else scheduled_date

    if not m_id or not p_id:
        raise HTTPException(status_code=400, detail="Missing maintenance/request id or provider id")

    maint = db.query(Maintenance).filter(Maintenance.id == m_id).first()
    if not maint:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if not maint.property or not company_resource_access(current_user, maint.property):
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if current_user.id != maint.property.owner_id and current_user.id != maint.property.manager_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only property management can dispatch work orders")
    provider = db.query(User).filter(User.id == p_id, User.role == "service_provider").first()
    if not provider or not company_resource_access(current_user, provider):
        raise HTTPException(status_code=404, detail="Service provider not found")
    if q_id is not None and not db.query(MaintenanceQuote).filter(
        MaintenanceQuote.id == q_id,
        MaintenanceQuote.maintenance_id == m_id,
        MaintenanceQuote.provider_id == p_id,
    ).first():
        raise HTTPException(status_code=404, detail="Quote not found for this maintenance request")

    sched = None
    if sched_str:
        try:
            sched = datetime.fromisoformat(sched_str.replace("Z", ""))
        except Exception:
            pass

    work_order = MaintenanceWorkOrder(
        maintenance_id=m_id,
        provider_id=p_id,
        quote_id=q_id,
        scheduled_date=sched,
        status="assigned"
    )
    maint.status = "in_progress"
    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    # Notify provider
    notif = Notification(
        recipient_id=p_id,
        notification_type="MAINTENANCE",
        title="New Work Order Dispatched",
        message=f"You have been assigned to maintenance job '{maint.title}'.",
        priority="HIGH",
        related_entity_type="MAINTENANCE",
        related_entity_id=maint.id,
    )
    db.add(notif)
    db.commit()

    log_audit_event(db, current_user.id, "DISPATCH_WORK_ORDER", "work_order", work_order.id)
    return {
        "id": work_order.id,
        "request_id": work_order.maintenance_id,
        "property_id": maint.property_id,
        "provider_id": work_order.provider_id,
        "assigned_by_id": current_user.id,
        "status": work_order.status,
        "scheduled_date": work_order.scheduled_date.isoformat() if work_order.scheduled_date else None,
        "notes": payload.notes if payload else None,
        "created_at": work_order.created_at.isoformat() if hasattr(work_order.created_at, "isoformat") else str(work_order.created_at),
        "updated_at": work_order.created_at.isoformat() if hasattr(work_order.created_at, "isoformat") else str(work_order.created_at),
        "property_name": maint.property.name if maint.property else "Property",
        "request_title": maint.title,
    }


@router.get("/work-orders")
@router.get("/work-orders/my")
def get_work_orders(
    status: Optional[str] = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves work orders: filtered for current provider if contractor, or all relevant orders for manager/admin.
    """
    query = db.query(MaintenanceWorkOrder).join(
        Maintenance, MaintenanceWorkOrder.maintenance_id == Maintenance.id
    ).join(Property, Maintenance.property_id == Property.id)
    property_scope = (
        Property.company_id.is_(None)
        if current_user.company_id is None
        else Property.company_id == current_user.company_id
    )
    query = query.filter(property_scope)
    
    # If user has service_provider role or is contractor, show theirs
    if current_user.role == "service_provider":
        query = query.filter(MaintenanceWorkOrder.provider_id == current_user.id)
    elif current_user.role not in ["admin", "manager", "owner"]:
        # Standard user shouldn't see all orders
        query = query.filter(MaintenanceWorkOrder.provider_id == current_user.id)

    if status:
        query = query.filter(MaintenanceWorkOrder.status == status)

    orders = query.order_by(MaintenanceWorkOrder.created_at.desc()).all()

    return [
        {
            "id": o.id,
            "request_id": o.maintenance_id,
            "maintenance_id": o.maintenance_id,
            "property_id": o.maintenance.property_id if (o.maintenance and o.maintenance.property_id) else 1,
            "provider_id": o.provider_id,
            "assigned_by_id": o.verified_by_id or 1,
            "title": o.maintenance.title if o.maintenance else "Untitled",
            "request_title": o.maintenance.title if o.maintenance else "Untitled",
            "description": o.maintenance.description if o.maintenance else "",
            "priority": o.maintenance.priority if o.maintenance else "medium",
            "status": o.status,
            "scheduled_date": o.scheduled_date.isoformat() if o.scheduled_date else None,
            "completion_notes": o.completion_notes,
            "notes": o.completion_notes,
            "created_at": o.created_at.isoformat() if hasattr(o.created_at, "isoformat") else str(o.created_at),
            "updated_at": o.created_at.isoformat() if hasattr(o.created_at, "isoformat") else str(o.created_at),
            "property_name": o.maintenance.property.name if (o.maintenance and o.maintenance.property) else "Property",
            "provider_company": o.provider.full_name if o.provider else "Contractor",
        }
        for o in orders
    ]


@router.put("/work-orders/{work_order_id}/status")
@router.patch("/work-orders/{work_order_id}/status")
def update_work_order_status(
    work_order_id: int,
    payload: WorkOrderUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Service Provider or Manager updates work order progress (e.g. mark completed with completion notes).
    """
    wo = db.query(MaintenanceWorkOrder).filter(MaintenanceWorkOrder.id == work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if not wo.maintenance or not wo.maintenance.property or not company_resource_access(current_user, wo.maintenance.property):
        raise HTTPException(status_code=404, detail="Work order not found")

    is_provider = wo.provider_id == current_user.id
    is_admin = current_user.role == "admin"
    is_management = (
        current_user.role in ["manager", "owner"]
        and current_user.id in {wo.maintenance.property.owner_id, wo.maintenance.property.manager_id}
    )

    if not (is_provider or is_admin or is_management):
        raise HTTPException(status_code=403, detail="Not authorized to update this work order")

    wo.status = payload.status
    if payload.completion_notes:
        wo.completion_notes = payload.completion_notes
    if payload.completion_photos_json:
        wo.completion_photos_json = payload.completion_photos_json

    if payload.status == "completed":
        if wo.maintenance:
            wo.maintenance.status = "resolved"
            wo.maintenance.resolved_at = utc_now()

    db.commit()
    db.refresh(wo)

    log_audit_event(db, current_user.id, f"WORK_ORDER_{payload.status.upper()}", "work_order", wo.id)
    return {
        "message": f"Work order updated to {payload.status}",
        "id": wo.id,
        "status": wo.status,
        "completion_notes": wo.completion_notes
    }
