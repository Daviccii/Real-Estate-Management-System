from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app.schemas.property import PropertyCreate, PropertyOut, PropertyUpdate, PropertyMatchRequest, PropertyMatchResult
from app.database.database import get_db, get_read_db
from app.auth.deps import get_current_user
from app.auth.roles import verify_role, require_staff
from app.repositories.property_repo import (
    create_property,
    get_property as repo_get_property,
    list_properties as repo_list_properties,
    count_properties as repo_count_properties,
    update_property as repo_update_property,
    delete_property as repo_delete_property,
)
from app.models.user import User
from app.models.property import Property
from app.services.audit_service import log_audit_event
from app.services.cache_service import (
    cache_get_json,
    cache_set_json,
    invalidate_property_cache,
    property_detail_key,
    property_list_key,
)

router = APIRouter(prefix="/properties", tags=["properties"])


def calculate_property_match(prop: Property, criteria: PropertyMatchRequest) -> tuple[int, list[str]]:
    score = 40  # base compatibility score
    reasons = []

    # 1. Budget Fit (up to 30 pts)
    prop_price = None
    try:
        if prop.price:
            prop_price = float(str(prop.price).replace(",", "").replace("KSh", "").replace("$", "").strip())
    except Exception:
        pass

    if criteria.max_budget and prop_price:
        if prop_price <= criteria.max_budget:
            score += 30
            reasons.append(f"Within your budget: Listed at {prop.price_label or f'KSh {prop_price:,.0f}'} (Under your {criteria.max_budget:,.0f} limit)")
        elif prop_price <= criteria.max_budget * 1.15:
            score += 15
            reasons.append(f"Close to budget: {prop.price_label or f'KSh {prop_price:,.0f}'} (within 15% of your max budget)")
        else:
            score -= 10
    elif prop_price:
        score += 10
        reasons.append(f"Pricing: {prop.price_label or f'KSh {prop_price:,.0f}'}")

    # 2. Location Fit (up to 20 pts)
    if criteria.preferred_city:
        if prop.city and criteria.preferred_city.lower() in prop.city.lower():
            score += 20
            reasons.append(f"Prime location: Situated in {prop.city}")
        else:
            score += 5

    # 3. Bedroom / Household Size (up to 20 pts)
    if criteria.min_bedrooms is not None:
        if prop.bedrooms is not None and prop.bedrooms >= criteria.min_bedrooms:
            score += 15
            reasons.append(f"Space: Offers {prop.bedrooms} bedroom{'s' if prop.bedrooms != 1 else ''} (Matches your {criteria.min_bedrooms}+ requirement)")
    
    if criteria.household_size:
        needed_beds = 1 if criteria.household_size <= 2 else (2 if criteria.household_size <= 4 else 3)
        if prop.bedrooms and prop.bedrooms >= needed_beds:
            score += 5
            reasons.append(f"Household size: Comfortably accommodates a family of {criteria.household_size}")

    # 4. Property Type
    if criteria.property_type and prop.property_type:
        if criteria.property_type.lower() in prop.property_type.lower():
            score += 10
            reasons.append(f"Type: Matches requested {prop.property_type.capitalize()}")

    # 5. Amenities & Lifestyle
    prop_amenities = (prop.amenities or "").lower()
    if criteria.require_parking:
        if prop.parking_spaces and prop.parking_spaces > 0 or "parking" in prop_amenities:
            score += 10
            reasons.append("Parking: Includes dedicated on-site parking spaces")
    if criteria.require_security and ("security" in prop_amenities or "cctv" in prop_amenities):
        score += 5
        reasons.append("Security: Features 24/7 security & access control")
    if criteria.require_balcony and "balcony" in prop_amenities:
        score += 5
        reasons.append("Outdoor space: Includes private balcony")

    if criteria.furnishing and prop.furnishing:
        if criteria.furnishing.lower() == prop.furnishing.lower():
            score += 5
            reasons.append(f"Furnishing: {prop.furnishing.capitalize()}")

    final_score = min(100, max(15, score))
    return final_score, reasons


@router.post("/public/match", response_model=List[PropertyMatchResult], tags=["public"])
@router.post("/match", response_model=List[PropertyMatchResult])
def match_properties(
    criteria: PropertyMatchRequest,
    db: Session = Depends(get_db),
):
    """
    Transparent Smart Discovery Match Engine.
    Evaluates properties against user lifestyle, budget, and size criteria,
    computing transparent compatibility scores with clear explanations.
    """
    query = db.query(Property).filter(Property.status == "active")
    if criteria.purpose:
        query = query.filter(Property.purpose == criteria.purpose)

    properties = query.all()
    results = []

    for p in properties:
        score, reasons = calculate_property_match(p, criteria)
        results.append(PropertyMatchResult(
            property=PropertyOut.model_validate(p, from_attributes=True),
            match_score=score,
            match_reasons=reasons
        ))

    # Sort descending by compatibility score
    results.sort(key=lambda x: x.match_score, reverse=True)
    return results


@router.post("/", response_model=PropertyOut, status_code=status.HTTP_201_CREATED)
def create(
    prop_in: PropertyCreate,
    # FIX: previously any authenticated user (including plain 'user'/'tenant'
    # accounts) could create listings via get_current_user, with no role
    # check at all. require_staff restricts creation to agent/manager/admin —
    # when a managers page is built, a 'manager' account already works here
    # with no further backend change needed.
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    prop = create_property(
        db, owner_id=current_user.id, company_id=current_user.company_id,
        **prop_in.model_dump()
    )
    invalidate_property_cache()
    return prop


@router.get("/", response_model=List[PropertyOut])
def list_props(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    sort: Optional[str] = None,
    purpose: Optional[str] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.company_id is None:
        return []
    return repo_list_properties(
        db, skip=skip, limit=limit, search=search, property_type=property_type,
        city=city, status=status, sort=sort, purpose=purpose,
        verified_only=verified_only, company_id=current_user.company_id,
    )


@router.get("/public", response_model=List[PropertyOut], tags=["public"])
def list_public(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    sort: Optional[str] = None,
    purpose: Optional[str] = None,
    verified_only: bool = False,
    db: Session = Depends(get_read_db),
):
    """Public properties listing — no authentication required."""
    key = property_list_key(
        skip=skip, limit=limit, search=search, property_type=property_type,
        city=city, status=status, sort=sort, purpose=purpose,
        verified_only=verified_only,
    )
    cached = cache_get_json(key)
    if cached is not None:
        return cached
    props = repo_list_properties(db, skip=skip, limit=limit, search=search, property_type=property_type, city=city, status=status, sort=sort, purpose=purpose, verified_only=verified_only)
    payload = [PropertyOut.model_validate(p).model_dump(mode="json") for p in props]
    cache_set_json(key, payload)
    return payload


@router.get('/public/count', tags=['public'])
def public_count(
    search: Optional[str] = None,
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    purpose: Optional[str] = None,
    verified_only: bool = False,
    db: Session = Depends(get_read_db),
):
    """
    Total number of properties matching the given filters — same filter
    params as GET /public, minus pagination/sort. The frontend uses this to
    compute real total page counts instead of guessing from whether the last
    page came back full.
    """
    total = repo_count_properties(db, search=search, property_type=property_type, city=city, status=status, purpose=purpose, verified_only=verified_only)
    return {"total": total}


@router.get('/public/meta', tags=['public'])
def public_meta(db: Session = Depends(get_read_db)):
    """Return lightweight metadata about public properties: total count and total units."""
    total = db.query(func.count(Property.id)).scalar() or 0
    total_units = db.query(func.coalesce(func.sum(Property.units_count), 0)).scalar() or 0
    return {"total": int(total), "total_units": int(total_units)}


@router.get('/public/market-insights', tags=['public'])
def market_insights(db: Session = Depends(get_read_db)):
    """Return market insights derived from property data."""
    key = "props:v1:market-insights"
    cached = cache_get_json(key)
    if cached is not None:
        return cached
    total = db.query(func.count(Property.id)).scalar() or 0
    
    # Properties by purpose
    purpose_counts = db.query(
        Property.purpose,
        func.count(Property.id)
    ).group_by(Property.purpose).all()
    
    purpose_data = {purpose: count for purpose, count in purpose_counts if purpose}
    
    # Properties by type
    type_counts = db.query(
        Property.property_type,
        func.count(Property.id)
    ).group_by(Property.property_type).all()
    
    type_data = {ptype: count for ptype, count in type_counts if ptype}
    
    # Properties by location (top cities)
    city_counts = db.query(
        Property.city,
        func.count(Property.id)
    ).group_by(Property.city).order_by(func.count(Property.id).desc()).limit(10).all()
    
    location_data = [{"city": city, "count": count} for city, count in city_counts if city]
    
    # Status distribution
    status_counts = db.query(
        Property.status,
        func.count(Property.id)
    ).group_by(Property.status).all()
    
    status_data = {status: count for status, count in status_counts}

    report = {
        "total_properties": int(total),
        "by_purpose": purpose_data,
        "by_type": type_data,
        "top_locations": location_data,
        "by_status": status_data,
    }
    cache_set_json(key, report)
    return report


# FIX: previously there was no public single-property endpoint. The frontend's
# PropertyDetailsPage called the authenticated GET /{property_id} below, which
# explicitly blocks anyone who isn't the property's owner or an admin — so any
# buyer clicking "View Details" on a listing that wasn't theirs got a 403.
# This mirrors the existing /public list/meta/market-insights pattern: open
# read access to listing details, same as any real estate site's detail page.
# Declared LAST among /public/... routes so it doesn't shadow the static paths
# above (FastAPI matches path operations in declaration order, and "meta",
# "count", "market-insights" would otherwise structurally match {property_id}
# and fail int conversion before ever reaching the real handler).
@router.get('/public/{property_id}', response_model=PropertyOut, tags=['public'])
def read_public(property_id: int, db: Session = Depends(get_read_db)):
    key = property_detail_key(property_id)
    cached = cache_get_json(key)
    if cached is not None:
        return cached
    prop = repo_get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    payload = PropertyOut.model_validate(prop).model_dump(mode="json")
    cache_set_json(key, payload)
    return payload


@router.get('/public/{property_id}/contact', tags=['public'])
def read_public_contact(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Consent-gated direct-contact reveal (Kenya Data Protection Act, 2019).

    Returns the listing's direct contact person only when the owner enabled
    `allow_direct_contact` on the property. Every successful reveal is
    audit-logged. When consent was not given, the prospect is directed to
    in-app messaging instead.
    """
    prop = repo_get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if not prop.allow_direct_contact:
        return {
            "direct_contact_allowed": False,
            "contact": None,
            "property_id": prop.id,
            "message": "The owner has not enabled direct contact for this listing. Send an inquiry or message instead.",
        }

    contact_user = prop.agent or prop.owner
    if not contact_user:
        return {
            "direct_contact_allowed": False,
            "contact": None,
            "property_id": prop.id,
            "message": "No contact person is available for this listing yet.",
        }

    log_audit_event(
        db,
        current_user.id,
        "REVEAL_PROPERTY_CONTACT",
        "property",
        prop.id,
        details={"contact_user_id": contact_user.id, "contact_role": contact_user.role},
    )

    return {
        "direct_contact_allowed": True,
        "property_id": prop.id,
        "contact": {
            "user_id": contact_user.id,
            "name": contact_user.full_name or contact_user.email,
            "phone": contact_user.phone,
            "email": contact_user.email,
            "role": contact_user.role,
        },
    }


@router.get("/{property_id}", response_model=PropertyOut)
def read(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prop = repo_get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if prop.company_id is not None and prop.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    # Only owner or admin can view via the authenticated management route
    # (used by the edit flow) — public viewing goes through /public/{id} above.
    if prop.owner_id != current_user.id and not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this property")
    return prop


@router.put("/{property_id}", response_model=PropertyOut)
def update(property_id: int, prop_in: PropertyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prop = repo_get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    # Only owner or admin can update
    if prop.owner_id != current_user.id and not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify property")
    updated = repo_update_property(db, prop, **prop_in.model_dump(exclude_none=True))
    invalidate_property_cache()
    return updated


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prop = repo_get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if prop.owner_id != current_user.id and not verify_role(current_user, ["admin"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete property")
    repo_delete_property(db, prop)
    invalidate_property_cache()
    return None