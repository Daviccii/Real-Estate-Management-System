from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
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


def _apply_filters(
    query: Query,
    *,
    search: Optional[str] = None,
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    purpose: Optional[str] = None,
    verified_only: bool = False,
) -> Query:
    """Smart, resilient filter logic for list_properties() and count_properties()."""
    if search:
        raw = search.strip()
        tokens = [t.lower() for t in raw.split() if t.lower() not in {"in", "at", "the", "a", "for", "with", "near", "and", "of"} and len(t) > 1]
        if not tokens:
            tokens = [raw.lower()]

        for t in tokens:
            term = f"%{t}%"
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

            query = query.filter(or_(*conds))

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


def list_properties(db: Session, skip: int = 0, limit: int = 100, *, search: Optional[str] = None, property_type: Optional[str] = None, city: Optional[str] = None, status: Optional[str] = None, sort: Optional[str] = None, purpose: Optional[str] = None, verified_only: bool = False, company_id: Optional[int] = None) -> List[Property]:
    q = _apply_filters(db.query(Property), search=search, property_type=property_type, city=city, status=status, purpose=purpose, verified_only=verified_only)
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


def count_properties(db: Session, *, search: Optional[str] = None, property_type: Optional[str] = None, city: Optional[str] = None, status: Optional[str] = None, purpose: Optional[str] = None, verified_only: bool = False) -> int:
    """Total count of properties matching the same filters list_properties()
    would apply — used by the frontend to compute total page count instead of
    guessing from whether the last page came back full."""
    q = _apply_filters(db.query(Property), search=search, property_type=property_type, city=city, status=status, purpose=purpose, verified_only=verified_only)
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