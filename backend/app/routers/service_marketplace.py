from typing import List, Optional, Union
from datetime import datetime
from app.utils.time import utc_now
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access, require_user, require_service_provider
from app.models.service_marketplace import ServiceProviderProfile, MaintenanceQuote, MaintenanceWorkOrder
from app.models.maintenance import Maintenance
from app.models.property import Property
from app.models.user import User
from app.models.notification import Notification
from app.models.provider_rating import ProviderRating
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/service-marketplace", tags=["service-marketplace"])

WORK_ORDER_STATUSES = {"accepted", "in_progress", "completed", "verified"}
REVIEWABLE_ORDER_STATUSES = {"completed", "verified"}
CLOSED_MAINTENANCE_STATUSES = ("resolved", "closed")


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


class ReviewCreate(BaseModel):
    score: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


def _rating_stats(db: Session, provider_user_ids: List[int]) -> dict:
    """Aggregate review stats per provider user id: {user_id: (avg_score, count)}."""
    if not provider_user_ids:
        return {}
    rows = (
        db.query(ProviderRating.provider_id, func.avg(ProviderRating.score), func.count(ProviderRating.id))
        .filter(ProviderRating.provider_id.in_(provider_user_ids))
        .group_by(ProviderRating.provider_id)
        .all()
    )
    return {pid: (float(avg or 0), int(cnt)) for pid, avg, cnt in rows}


def _completed_jobs(db: Session, provider_user_ids: List[int]) -> dict:
    """Completed/verified work order counts per provider user id."""
    if not provider_user_ids:
        return {}
    rows = (
        db.query(MaintenanceWorkOrder.provider_id, func.count(MaintenanceWorkOrder.id))
        .filter(
            MaintenanceWorkOrder.provider_id.in_(provider_user_ids),
            MaintenanceWorkOrder.status.in_(tuple(REVIEWABLE_ORDER_STATUSES)),
        )
        .group_by(MaintenanceWorkOrder.provider_id)
        .all()
    )
    return {pid: int(cnt) for pid, cnt in rows}


def _mask_name(full_name: Optional[str]) -> str:
    parts = (full_name or "").strip().split()
    if not parts:
        return "PropNoxa user"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0]}."


def _truncate(text: Optional[str], limit: int = 300) -> Optional[str]:
    if not text:
        return text
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _provider_dict(
    p: ServiceProviderProfile,
    ratings: dict,
    jobs: dict,
    viewer: Optional[User] = None,
) -> dict:
    avg, count = ratings.get(p.user_id, (None, 0))
    include_contact = bool(viewer and (viewer.role == "admin" or viewer.id == p.user_id))
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
        "bio": p.bio,
        "years_experience": p.years_experience,
        "rating_avg": round(avg, 2) if count else None,
        "reviews_count": count,
        "completed_jobs_count": jobs.get(p.user_id, 0),
        "is_available": p.is_available,
        "created_at": p.created_at.isoformat() if hasattr(p.created_at, "isoformat") else str(p.created_at),
        "user_name": p.user.full_name if p.user else None,
        "user_email": p.user.email if (p.user and include_contact) else None,
        "user_phone": getattr(p.user, "phone", None) if (p.user and include_contact) else None,
    }


def _resolve_provider(db: Session, provider_id: int) -> Optional[ServiceProviderProfile]:
    return db.query(ServiceProviderProfile).filter(
        (ServiceProviderProfile.id == provider_id) | (ServiceProviderProfile.user_id == provider_id)
    ).first()


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
            is_available=payload.is_available if payload.is_available is not None else True,
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
        if payload.is_available is not None:
            profile.is_available = payload.is_available

    db.commit()
    db.refresh(profile)
    log_audit_event(db, current_user.id, "UPDATE_SERVICE_PROVIDER_PROFILE", "service_provider", profile.id)
    ratings = _rating_stats(db, [profile.user_id])
    jobs = _completed_jobs(db, [profile.user_id])
    return _provider_dict(profile, ratings, jobs, viewer=current_user)


@router.get("/profile/me")
@router.get("/providers/profile/me")
def get_my_provider_profile(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    profile = db.query(ServiceProviderProfile).filter(ServiceProviderProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Service provider profile not found")
    ratings = _rating_stats(db, [profile.user_id])
    jobs = _completed_jobs(db, [profile.user_id])
    return _provider_dict(profile, ratings, jobs, viewer=current_user)


@router.get("/providers")
def list_verified_service_providers(
    q: Optional[str] = None,
    category: Optional[str] = None,
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    available_only: bool = False,
    sort: str = Query("rating", pattern="^(rating|jobs|newest|name)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Paginated, searchable directory of service providers for the marketplace.
    """
    query = db.query(ServiceProviderProfile).join(User, ServiceProviderProfile.user_id == User.id)
    query = query.filter(User.is_active.is_(True))

    filter_spec = specialty or category
    if filter_spec:
        query = query.filter(ServiceProviderProfile.specialty.ilike(f"%{filter_spec}%"))
    if city:
        query = query.filter(ServiceProviderProfile.service_areas.ilike(f"%{city}%"))
    if q:
        like = f"%{q}%"
        query = query.filter(
            ServiceProviderProfile.business_name.ilike(like)
            | ServiceProviderProfile.specialty.ilike(like)
            | ServiceProviderProfile.service_areas.ilike(like)
        )
    if available_only:
        query = query.filter(ServiceProviderProfile.is_available.is_(True))

    jobs_subq = (
        db.query(
            MaintenanceWorkOrder.provider_id.label("provider_user_id"),
            func.count(MaintenanceWorkOrder.id).label("jobs_count"),
        )
        .filter(MaintenanceWorkOrder.status.in_(tuple(REVIEWABLE_ORDER_STATUSES)))
        .group_by(MaintenanceWorkOrder.provider_id)
        .subquery()
    )

    if sort == "jobs":
        query = query.outerjoin(jobs_subq, jobs_subq.c.provider_user_id == ServiceProviderProfile.user_id)
        query = query.order_by(func.coalesce(jobs_subq.c.jobs_count, 0).desc(), ServiceProviderProfile.id.asc())
    elif sort == "newest":
        query = query.order_by(ServiceProviderProfile.created_at.desc(), ServiceProviderProfile.id.desc())
    elif sort == "name":
        query = query.order_by(ServiceProviderProfile.business_name.asc())
    else:
        query = query.order_by(ServiceProviderProfile.rating.desc().nulls_last(), ServiceProviderProfile.id.asc())

    total = query.count()
    profiles = query.offset((page - 1) * page_size).limit(page_size).all()

    user_ids = [p.user_id for p in profiles]
    ratings = _rating_stats(db, user_ids)
    jobs = _completed_jobs(db, user_ids)
    return {
        "items": [_provider_dict(p, ratings, jobs, viewer=current_user) for p in profiles],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/providers/{provider_id}")
def get_provider_details(
    provider_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Get public details of a specific service provider.
    """
    p = _resolve_provider(db, provider_id)
    if not p:
        raise HTTPException(status_code=404, detail="Service provider not found")
    ratings = _rating_stats(db, [p.user_id])
    jobs = _completed_jobs(db, [p.user_id])
    return _provider_dict(p, ratings, jobs, viewer=current_user)


@router.get("/providers/{provider_id}/reviews")
def list_provider_reviews(
    provider_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Paginated customer reviews for a service provider (reviewer names masked).
    """
    p = _resolve_provider(db, provider_id)
    if not p:
        raise HTTPException(status_code=404, detail="Service provider not found")

    query = (
        db.query(ProviderRating)
        .filter(ProviderRating.provider_id == p.user_id)
        .order_by(ProviderRating.created_at.desc(), ProviderRating.id.desc())
    )
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": r.id,
                "provider_id": r.provider_id,
                "work_order_id": r.work_order_id,
                "score": r.score,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
                "reviewer_name": _mask_name(r.reviewer.full_name if r.reviewer else None),
                "maintenance_title": r.maintenance.title if r.maintenance else None,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "rating_avg": round(p.rating, 2) if (p.rating is not None and total > 0) else None,
        "reviews_count": total,
    }


@router.get("/open-requests")
def list_open_maintenance_requests(
    category: Optional[str] = None,
    city: Optional[str] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(require_service_provider),
    db: Session = Depends(get_db),
):
    """
    Job board: open maintenance tickets service providers can bid on.
    Privacy-safe projection: no tenant, address or ownership details are exposed.
    """
    query = (
        db.query(Maintenance)
        .join(Property, Maintenance.property_id == Property.id)
        .filter(Maintenance.status.notin_(CLOSED_MAINTENANCE_STATUSES))
    )
    if category:
        query = query.filter(Maintenance.category.ilike(f"%{category}%"))
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if q:
        like = f"%{q}%"
        query = query.filter(Maintenance.title.ilike(like) | Maintenance.description.ilike(like))

    total = query.count()
    rows = (
        query.order_by(Maintenance.created_at.desc(), Maintenance.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    ids = [m.id for m in rows]
    quote_counts: dict = {}
    my_quotes: dict = {}
    if ids:
        quote_counts = dict(
            db.query(MaintenanceQuote.maintenance_id, func.count(MaintenanceQuote.id))
            .filter(MaintenanceQuote.maintenance_id.in_(ids))
            .group_by(MaintenanceQuote.maintenance_id)
            .all()
        )
        my_quotes = {
            quote.maintenance_id: quote
            for quote in db.query(MaintenanceQuote).filter(
                MaintenanceQuote.maintenance_id.in_(ids),
                MaintenanceQuote.provider_id == current_user.id,
            ).all()
        }

    return {
        "items": [
            {
                "id": m.id,
                "title": m.title,
                "description": _truncate(m.description),
                "category": m.category,
                "priority": m.priority,
                "status": m.status,
                "city": m.property.city if m.property else None,
                "county": m.property.county if m.property else None,
                "property_type": m.property.property_type if m.property else None,
                "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
                "quotes_count": int(quote_counts.get(m.id, 0)),
                "my_quote_id": my_quotes[m.id].id if m.id in my_quotes else None,
                "my_quote_status": my_quotes[m.id].status if m.id in my_quotes else None,
                "my_quote_amount": my_quotes[m.id].amount if m.id in my_quotes else None,
            }
            for m in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/quotes")
def submit_maintenance_quote(
    payload: QuoteCreate,
    current_user: User = Depends(require_service_provider),
    db: Session = Depends(get_db),
):
    """
    Contractor submits a price quote for a maintenance issue listed on the marketplace job board.
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
    if maint.status in CLOSED_MAINTENANCE_STATUSES:
        raise HTTPException(status_code=400, detail="This maintenance ticket is no longer open for quotes")

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
    if quote.status != "pending":
        raise HTTPException(status_code=400, detail=f"Quote is already {quote.status}")

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

    notif = Notification(
        recipient_id=quote.provider_id,
        notification_type="MAINTENANCE",
        title="Quote Accepted",
        message=f"Your quote for '{maint.title}' was accepted. A work order is ready for you.",
        priority="HIGH",
        related_entity_type="MAINTENANCE",
        related_entity_id=maint.id,
    )
    db.add(notif)
    db.commit()

    log_audit_event(db, current_user.id, "ACCEPT_MAINTENANCE_QUOTE", "quote", quote.id)
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
    maintenance_id: Optional[int] = None,
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
    if maintenance_id is not None:
        query = query.filter(MaintenanceWorkOrder.maintenance_id == maintenance_id)

    orders = query.order_by(MaintenanceWorkOrder.created_at.desc()).all()

    order_ids = [o.id for o in orders]
    review_scores: dict = {}
    if order_ids:
        review_scores = dict(
            db.query(ProviderRating.work_order_id, ProviderRating.score)
            .filter(ProviderRating.work_order_id.in_(order_ids))
            .all()
        )

    results = []
    for o in orders:
        prop = o.maintenance.property if (o.maintenance and o.maintenance.property) else None
        is_management = current_user.role == "admin" or (
            current_user.role in ("manager", "owner") and prop is not None
            and current_user.id in {prop.owner_id, prop.manager_id}
        )
        has_review = o.id in review_scores
        results.append({
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
            "updated_at": o.updated_at.isoformat() if hasattr(o.updated_at, "isoformat") else str(o.updated_at),
            "property_name": o.maintenance.property.name if (o.maintenance and o.maintenance.property) else "Property",
            "provider_company": o.provider.full_name if o.provider else "Contractor",
            "has_review": has_review,
            "review_score": review_scores.get(o.id),
            "can_review": bool(
                is_management and not has_review and o.status in REVIEWABLE_ORDER_STATUSES
            ),
        })
    return results


@router.post("/work-orders/{work_order_id}/review", status_code=201)
def submit_work_order_review(
    work_order_id: int,
    payload: ReviewCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Property management rates a service provider after a completed/verified work order.
    One review per work order; provider aggregate rating is recomputed.
    """
    wo = db.query(MaintenanceWorkOrder).filter(MaintenanceWorkOrder.id == work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    prop = wo.maintenance.property if (wo.maintenance and wo.maintenance.property) else None
    if not prop or not company_resource_access(current_user, prop):
        raise HTTPException(status_code=404, detail="Work order not found")

    is_admin = current_user.role == "admin"
    is_management = current_user.id in {prop.owner_id, prop.manager_id}
    if not (is_admin or is_management):
        raise HTTPException(status_code=403, detail="Only property management can review providers")
    if wo.status not in REVIEWABLE_ORDER_STATUSES:
        raise HTTPException(status_code=400, detail="Work order must be completed or verified before it can be reviewed")
    if db.query(ProviderRating).filter(ProviderRating.work_order_id == wo.id).first():
        raise HTTPException(status_code=409, detail="This work order has already been reviewed")

    comment = (payload.comment or "").strip() or None
    rating = ProviderRating(
        provider_id=wo.provider_id,
        reviewer_id=current_user.id,
        maintenance_id=wo.maintenance_id,
        work_order_id=wo.id,
        score=payload.score,
        comment=comment,
    )
    db.add(rating)
    db.flush()

    avg, count = (
        db.query(func.avg(ProviderRating.score), func.count(ProviderRating.id))
        .filter(ProviderRating.provider_id == wo.provider_id)
        .first()
    )
    profile = db.query(ServiceProviderProfile).filter(ServiceProviderProfile.user_id == wo.provider_id).first()
    if profile:
        profile.rating = round(float(avg), 2) if avg is not None else None
        profile.reviews_count = int(count or 0)
    db.commit()
    db.refresh(rating)

    notif = Notification(
        recipient_id=wo.provider_id,
        notification_type="MAINTENANCE",
        title="New Customer Review",
        message=f"You received a {payload.score}-star review for '{wo.maintenance.title if wo.maintenance else 'a job'}'.",
        priority="NORMAL",
        related_entity_type="MAINTENANCE",
        related_entity_id=wo.maintenance_id,
    )
    db.add(notif)
    db.commit()

    log_audit_event(db, current_user.id, "SUBMIT_PROVIDER_REVIEW", "provider_rating", rating.id)
    return {
        "id": rating.id,
        "provider_id": rating.provider_id,
        "work_order_id": rating.work_order_id,
        "maintenance_id": rating.maintenance_id,
        "score": rating.score,
        "comment": rating.comment,
        "created_at": rating.created_at.isoformat() if hasattr(rating.created_at, "isoformat") else str(rating.created_at),
        "reviewer_name": _mask_name(current_user.full_name),
        "provider_rating_avg": profile.rating if profile else None,
        "provider_reviews_count": profile.reviews_count if profile else None,
    }


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
    if payload.status not in WORK_ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {', '.join(sorted(WORK_ORDER_STATUSES))}")

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
    if payload.status == "verified" and not (is_management or is_admin):
        raise HTTPException(status_code=403, detail="Only property management can verify completed work")

    wo.status = payload.status
    if payload.completion_notes:
        wo.completion_notes = payload.completion_notes
    if payload.completion_photos_json:
        wo.completion_photos_json = payload.completion_photos_json

    if payload.status == "completed":
        if wo.maintenance:
            wo.maintenance.status = "resolved"
            wo.maintenance.resolved_at = utc_now()
    elif payload.status == "verified":
        wo.verified_by_id = current_user.id
        wo.verified_at = utc_now()
    elif payload.status in ("accepted", "in_progress") and wo.maintenance and wo.maintenance.status == "resolved":
        # Reopening the job reopens the maintenance ticket
        wo.maintenance.status = "in_progress"
        wo.maintenance.resolved_at = None

    db.commit()
    db.refresh(wo)

    log_audit_event(db, current_user.id, f"WORK_ORDER_{payload.status.upper()}", "work_order", wo.id)
    return {
        "message": f"Work order updated to {payload.status}",
        "id": wo.id,
        "status": wo.status,
        "completion_notes": wo.completion_notes
    }
