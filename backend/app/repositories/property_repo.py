import re
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import Float, func, or_
from sqlalchemy.orm import Query
from app.models.property import Property


NAIROBI_AREAS = [
    "kilimani", "westlands", "kileleshwa", "upper hill", "lavington",
    "karen", "parklands", "nairobi cbd", "cbd", "ruaka", "ruiru",
    "syokimau", "south b", "south c", "ngara", "gigiri", "muthaiga",
    "runda", "spring valley", "riverside", "kitisuru", "hurlingham", "milimani",
    "kasarani", "roysambu", "embakasi", "langata", "kiambu rd", "waiyaki way"
]

MOMBASA_AREAS = [
    "nyali", "bamburi", "diani", "shanzu", "mombasa island", "tudor", "kizingo"
]

KIAMBU_AREAS = [
    "ruaka", "ruiru", "thika", "kikuyu", "kiambu town", "limuru", "juja"
]

# Budget-bucket slugs used by the public search UI mapped to numeric bounds.
BUDGET_SLUG_BOUNDS = {
    "under-5m": (None, 5_000_000),
    "5m-15m": (5_000_000, 15_000_000),
    "15m-50m": (15_000_000, 50_000_000),
    "50m-plus": (50_000_000, None),
}

# Filler/operator words that carry no matching value on their own — without
# this, a natural query like "3 bedroom apartment in kilimani under 60k" was
# AND-matched term-by-term and returned nothing because no column contains
# "under", "bedroom" or "60k".
SEARCH_STOP_WORDS = {
    "in", "at", "the", "a", "an", "for", "with", "near", "and", "of", "on",
    "to", "from", "up", "under", "below", "above", "over", "less", "than",
    "more", "most", "least", "not", "max", "maximum", "min", "minimum",
    "around", "about", "between", "ksh", "kes", "sh", "shillings", "shilling",
    "bedroom", "bedrooms", "bed", "beds", "br", "plus", "per", "month",
    "monthly", "renting",
}

_AMOUNT_SUFFIXES = {
    "k": 1_000, "thousand": 1_000,
    "m": 1_000_000, "million": 1_000_000,
}


def _parse_amount(digits: str, suffix: Optional[str]) -> Optional[float]:
    try:
        value = float(digits.replace(",", ""))
    except (TypeError, ValueError):
        return None
    if suffix:
        value *= _AMOUNT_SUFFIXES.get(suffix, 1)
    return value


def _price_numeric_expr():
    """Property.price is stored as a plain-digit string; extract it as a bigint
    so prices can be range-filtered server-side ("under 60000")."""
    return func.cast(func.replace(Property.price, ",", ""), Float)


def _bedrooms_conditions(value: str):
    v = value.strip().lower()
    if v in ("0", "studio", "bedrooms:0", "bedsitter", "bedsit", "bedsitters"):
        return or_(
            Property.bedrooms == 0,
            Property.property_type.ilike("%studio%"),
            Property.property_type.ilike("%bedsitter%"),
            Property.property_type.ilike("%bedsit%"),
        )
    if v in ("4-plus", "4+", "4plus", "5", "6"):
        if v in ("5", "6"):
            return Property.bedrooms == int(v)
        return Property.bedrooms >= 4
    try:
        return Property.bedrooms == int(v)
    except ValueError:
        return None


def _apply_filters(
    query: Query,
    *,
    search: Optional[str] = None,
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    purpose: Optional[str] = None,
    verified_only: bool = False,
    bedrooms: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    budget: Optional[str] = None,
) -> Query:
    """Smart, resilient filter logic for list_properties() and count_properties()."""
    if budget:
        bounds = BUDGET_SLUG_BOUNDS.get(budget.strip().lower())
        if bounds:
            lo, hi = bounds
            if min_price is None:
                min_price = lo
            if max_price is None:
                max_price = hi

    if search:
        raw = search.strip().lower()
        consumed = raw

        # Pull structured facts out of the free text so natural queries like
        # "3 bedroom apartment in kilimani under 60k" constrain properly
        # instead of failing an AND-match on filler words.
        if bedrooms is None:
            m = re.search(r"\b(\d+)\s*(?:bed(?:room)?s?|br)\b", consumed)
            if m:
                bedrooms = m.group(1)
                consumed = consumed.replace(m.group(0), " ")
            elif re.search(r"\b(?:studio|bedsitters?|bedsits?)\b", consumed):
                bedrooms = "0"

        price_pat = r"(?:ksh|kes|sh)?\.?\s*([\d.,]+)\s*(k|thousand|m|million)?\b"
        if max_price is None:
            m = re.search(
                r"\b(?:under|below|less than|not more than|up to|max(?:imum)?(?: of)?)\s*" + price_pat,
                consumed,
            )
            if m:
                max_price = _parse_amount(m.group(1), m.group(2))
                consumed = consumed.replace(m.group(0), " ")
        if min_price is None:
            m = re.search(
                r"\b(?:above|over|more than|at least|min(?:imum)?(?: of)?)\s*" + price_pat,
                consumed,
            )
            if m:
                min_price = _parse_amount(m.group(1), m.group(2))
                consumed = consumed.replace(m.group(0), " ")

        if not purpose:
            for pattern, slug in (
                (r"\bfor rent\b|\brent(?:al|als|ing)?\b", "rent"),
                (r"\bfor sale\b|\bbuy(?:ing)?\b|\bpurchase\b", "buy"),
                (r"\binvest(?:ment|ments)?\b", "invest"),
            ):
                if re.search(pattern, consumed):
                    purpose = slug
                    consumed = re.sub(pattern, " ", consumed)
                    break

        tokens = [
            t for t in re.split(r"[^a-z0-9]+", consumed)
            if len(t) > 1 and t not in SEARCH_STOP_WORDS
        ]
        # Leftover bare numbers (e.g. a lone "5m") are fragments of an amount
        # the user phrased oddly — dropping them beats matching nothing.
        tokens = [t for t in tokens if not re.fullmatch(r"\d+(?:\.\d+)?(?:k|m)?", t)]

        for t in tokens:
            term = f"%{t}%"
            if t in ("land", "lands", "plot", "plots"):
                # "land" as a bare substring matches Westlands/Parklands city
                # names, so for these the type field alone is authoritative.
                query = query.filter(or_(
                    Property.property_type.ilike("%land%"),
                    Property.property_type.ilike("%plot%"),
                ))
                continue
            conds = [
                Property.name.ilike(term),
                Property.city.ilike(term),
                Property.address.ilike(term),
                Property.county.ilike(term),
                Property.sub_location.ilike(term),
                Property.landmark.ilike(term),
                Property.description.ilike(term),
                Property.property_type.ilike(term),
                Property.amenities.ilike(term),
                Property.price_label.ilike(term),
            ]
            if t in ("nairobi", "nairobi county", "kanairo"):
                conds.append(Property.county.ilike("%nairobi%"))
                conds.append(Property.city.ilike("%nairobi%"))
                conds.append(Property.address.ilike("%nairobi%"))
                for area in NAIROBI_AREAS:
                    conds.append(Property.city.ilike(f"%{area}%"))
                    conds.append(Property.sub_location.ilike(f"%{area}%"))
                    conds.append(Property.address.ilike(f"%{area}%"))
            elif t == "apartment" or t == "apartments":
                conds.append(Property.property_type.ilike("%residential%"))
                conds.append(Property.name.ilike("%residences%"))
                conds.append(Property.name.ilike("%apartment%"))
                conds.append(Property.name.ilike("%heights%"))
            elif t in ("commercial", "office", "offices"):
                conds.append(Property.property_type.ilike("%commercial%"))
                conds.append(Property.property_type.ilike("%mixed use%"))
                conds.append(Property.name.ilike("%tower%"))
                conds.append(Property.name.ilike("%plaza%"))
                conds.append(Property.name.ilike("%square%"))
            elif t in ("townhouse", "townhouses"):
                conds.append(Property.property_type.ilike("%town house%"))
            elif t in ("bedsitter", "bedsitters", "bedsit", "bedsits"):
                conds.append(Property.property_type.ilike("%bedsit%"))
                conds.append(Property.property_type.ilike("%studio%"))

            query = query.filter(or_(*conds))

    if bedrooms:
        bed_cond = _bedrooms_conditions(bedrooms)
        if bed_cond is not None:
            query = query.filter(bed_cond)

    if min_price is not None:
        query = query.filter(_price_numeric_expr() >= min_price)
    if max_price is not None:
        query = query.filter(_price_numeric_expr() <= max_price)

    if property_type:
        pt = property_type.strip().lower()
        if pt in ("apartment", "apartments"):
            query = query.filter(or_(
                Property.property_type.ilike("%apartment%"),
                Property.property_type.ilike("%residential%"),
                Property.name.ilike("%residences%"),
                Property.name.ilike("%apartment%"),
                Property.name.ilike("%heights%"),
            ))
        elif pt in ("commercial", "office", "offices"):
            query = query.filter(or_(
                Property.property_type.ilike("%commercial%"),
                Property.property_type.ilike("%office%"),
                Property.property_type.ilike("%mixed use%"),
                Property.name.ilike("%tower%"),
                Property.name.ilike("%plaza%"),
                Property.name.ilike("%square%"),
            ))
        elif pt in ("villa", "villas"):
            query = query.filter(or_(
                Property.property_type.ilike("%villa%"),
                Property.name.ilike("%villa%"),
                Property.description.ilike("%villa%"),
            ))
        elif pt in ("mixed use", "mixed-use"):
            query = query.filter(or_(
                Property.property_type.ilike("%mixed%"),
                Property.name.ilike("%arc%"),
                Property.name.ilike("%nexus%"),
            ))
        else:
            query = query.filter(or_(
                Property.property_type.ilike(f"%{property_type}%"),
                Property.name.ilike(f"%{property_type}%"),
                Property.description.ilike(f"%{property_type}%"),
            ))

    if city:
        c = city.strip().lower()
        city_conds = [
            Property.city.ilike(f"%{city}%"),
            Property.county.ilike(f"%{city}%"),
            Property.sub_location.ilike(f"%{city}%"),
            Property.address.ilike(f"%{city}%"),
            Property.landmark.ilike(f"%{city}%"),
        ]
        if c in ("nairobi", "nairobi county", "nairobi city", "kanairo"):
            city_conds.append(Property.county.ilike("%nairobi%"))
            city_conds.append(Property.city.ilike("%nairobi%"))
            city_conds.append(Property.address.ilike("%nairobi%"))
            for area in NAIROBI_AREAS:
                city_conds.append(Property.city.ilike(f"%{area}%"))
                city_conds.append(Property.sub_location.ilike(f"%{area}%"))
                city_conds.append(Property.address.ilike(f"%{area}%"))
        elif c in ("mombasa", "mombasa county"):
            for area in MOMBASA_AREAS:
                city_conds.append(Property.city.ilike(f"%{area}%"))
                city_conds.append(Property.sub_location.ilike(f"%{area}%"))
        elif c in ("kiambu", "kiambu county"):
            for area in KIAMBU_AREAS:
                city_conds.append(Property.city.ilike(f"%{area}%"))
                city_conds.append(Property.sub_location.ilike(f"%{area}%"))

        query = query.filter(or_(*city_conds))

    if status:
        query = query.filter(Property.status == status)
    if purpose:
        query = query.filter(Property.purpose == purpose)
    if verified_only:
        query = query.filter(Property.is_verified.is_(True), Property.verification_status == "verified")

    return query


def get_property(db: Session, property_id: int) -> Optional[Property]:
    p = db.query(Property).filter(Property.id == property_id).first()
    if p:
        if hasattr(p, 'building') and p.building:
            setattr(p, 'building_name', p.building.name)
        elif hasattr(p, 'landmark') and p.landmark:
            setattr(p, 'building_name', p.landmark)
    return p


def list_properties(db: Session, skip: int = 0, limit: int = 100, *, search: Optional[str] = None, property_type: Optional[str] = None, city: Optional[str] = None, status: Optional[str] = None, sort: Optional[str] = None, purpose: Optional[str] = None, verified_only: bool = False, bedrooms: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, budget: Optional[str] = None, company_id: Optional[int] = None) -> List[Property]:
    q = _apply_filters(db.query(Property), search=search, property_type=property_type, city=city, status=status, purpose=purpose, verified_only=verified_only, bedrooms=bedrooms, min_price=min_price, max_price=max_price, budget=budget)
    if company_id is not None:
        q = q.filter(Property.company_id == company_id)

    # simple sorting options
    if sort == 'newest':
        q = q.order_by(Property.created_at.desc())
    elif sort == 'oldest':
        q = q.order_by(Property.created_at.asc())
    elif sort == 'units_desc':
        q = q.order_by(Property.units_count.desc())
    elif sort == 'units_asc':
        q = q.order_by(Property.units_count.asc())

    props = q.offset(skip).limit(limit).all()
    for p in props:
        if hasattr(p, 'building') and p.building:
            setattr(p, 'building_name', p.building.name)
        elif hasattr(p, 'landmark') and p.landmark:
            setattr(p, 'building_name', p.landmark)
    return props


def count_properties(db: Session, *, search: Optional[str] = None, property_type: Optional[str] = None, city: Optional[str] = None, status: Optional[str] = None, purpose: Optional[str] = None, verified_only: bool = False, bedrooms: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, budget: Optional[str] = None) -> int:
    """Total count of properties matching the same filters list_properties()
    would apply — used by the frontend to compute total page count instead of
    guessing from whether the last page came back full."""
    q = _apply_filters(db.query(Property), search=search, property_type=property_type, city=city, status=status, purpose=purpose, verified_only=verified_only, bedrooms=bedrooms, min_price=min_price, max_price=max_price, budget=budget)
    return q.count()


def create_property(db: Session, *, owner_id: int, company_id: Optional[int] = None, **data) -> Property:
    prop = Property(owner_id=owner_id, company_id=company_id, **data)
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


def update_property(db: Session, property_obj: Property, **data) -> Property:
    for key, value in data.items():
        if hasattr(property_obj, key) and value is not None:
            setattr(property_obj, key, value)
    db.add(property_obj)
    db.commit()
    db.refresh(property_obj)
    return property_obj


def delete_property(db: Session, property_obj: Property) -> None:
    db.delete(property_obj)
    db.commit()