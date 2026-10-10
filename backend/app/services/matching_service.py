"""Explainable property matching engine.

Ranks active listings against a buyer/tenant's stated criteria using a
deterministic weighted model. Every point awarded traces back to a
human-readable reason, so the API can explain *why* a property matched.

Scoring model (100 points when every factor applies):
    Budget 25 | Location 20 | Size 15 | Type 10 | Amenities 10
    Quality 10 | Furnishing 5 | Freshness 5

Factors that the user did not ask about are removed from BOTH the earned
and the available points, so leaving a field blank never penalises a
listing — it simply stops contributing to the denominator.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.models.property import Property
from app.schemas.property import PropertyMatchRequest
from app.utils.time import as_utc, utc_now

# Weight of each factor out of 100 when all factors apply.
FACTOR_WEIGHTS: Dict[str, int] = {
    "Budget": 25,
    "Location": 20,
    "Size": 15,
    "Type": 10,
    "Amenities": 10,
    "Quality": 10,
    "Furnishing": 5,
    "Freshness": 5,
}

# Listings priced above this multiple of the stated maximum are dropped
# entirely — a "match" that far outside the budget is noise, not a result.
BUDGET_HARD_CAP_RATIO = 1.3
BUDGET_SOFT_CAP_RATIO = 1.15

# Property-type synonym groups so "Flat" matches "Apartment" and so on.
TYPE_GROUPS: Dict[str, set] = {
    "apartment": {
        "apartment", "apartments", "flat", "flats", "studio", "studios",
        "penthouse", "penthouses", "loft", "lofts",
    },
    "house": {
        "house", "houses", "home", "villa", "villas", "bungalow",
        "bungalows", "townhouse", "townhouses", "maisonette",
        "maisonettes", "duplex", "duplexes",
    },
    "commercial": {
        "commercial", "office", "offices", "shop", "shops", "retail",
        "warehouse", "warehouses", "industrial", "godown", "godowns",
    },
    "land": {"land", "plot", "plots", "acre", "acres"},
}

_PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([km])?", re.IGNORECASE)


@dataclass
class MatchScore:
    score: int
    label: str
    reasons: List[str] = field(default_factory=list)
    breakdown: Dict[str, int] = field(default_factory=dict)


def parse_price(value) -> Optional[float]:
    """Extract a numeric price from free-text listing values.

    Handles "45000", "KSh 45,000/Month", "45k", "1.2M" and similar.
    """
    if value is None:
        return None
    text = str(value).strip().lower().replace(",", "")
    match = _PRICE_RE.search(text)
    if not match:
        return None
    amount = float(match.group(1))
    suffix = (match.group(2) or "").lower()
    if suffix == "k":
        amount *= 1_000
    elif suffix == "m":
        amount *= 1_000_000
    return amount


def match_label(score: int) -> str:
    if score >= 85:
        return "Excellent match"
    if score >= 70:
        return "Strong match"
    if score >= 55:
        return "Good match"
    return "Possible match"


def _normalise(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _type_group(value: Optional[str]) -> Optional[str]:
    tokens = set(_normalise(value).split())
    for group, keywords in TYPE_GROUPS.items():
        if tokens & keywords:
            return group
    return None


def _types_match(wanted: Optional[str], actual: Optional[str]) -> bool:
    a, b = _normalise(wanted), _normalise(actual)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    group_a, group_b = _type_group(a), _type_group(b)
    return group_a is not None and group_a == group_b


def _bedroom_requirement(household_size: int) -> int:
    if household_size <= 2:
        return 1
    if household_size <= 4:
        return 2
    return 3


def _display_price(prop: Property) -> str:
    if prop.price_label:
        return prop.price_label
    price = parse_price(prop.price)
    if price is None:
        return "price on request"
    return f"KSh {price:,.0f}"


def _score_budget(
    prop: Property, criteria: PropertyMatchRequest, reasons: List[str]
) -> Optional[float]:
    """Return the budget fraction, or None when the listing must be excluded."""
    price = parse_price(prop.price)
    if price is None:
        return 0.0
    if price > criteria.max_budget * BUDGET_HARD_CAP_RATIO:
        return None
    if price <= criteria.max_budget:
        reasons.append(f"Within your budget ({_display_price(prop)})")
        return 1.0
    if price <= criteria.max_budget * BUDGET_SOFT_CAP_RATIO:
        reasons.append(f"Slightly over budget ({_display_price(prop)})")
        return 0.6
    reasons.append(f"Above budget ({_display_price(prop)})")
    return 0.25


def _score_location(
    prop: Property, preferred_city: str
) -> Tuple[float, Optional[str]]:
    target = _normalise(preferred_city)
    if not target:
        return 0.0, None
    city = _normalise(prop.city)
    if city and len(city) >= 3 and (target in city or city in target):
        return 1.0, f"Located in {prop.city}"
    for value in (prop.county, prop.sub_location, prop.address, prop.landmark):
        norm = _normalise(value)
        if norm and len(norm) >= 3 and (target in norm or norm in target):
            return 0.6, f"Near your preferred area ({value})"
    return 0.0, None


def _score_size(
    prop: Property, criteria: PropertyMatchRequest, reasons: List[str]
) -> float:
    fractions: List[float] = []
    if criteria.min_bedrooms is not None:
        minimum = max(1, criteria.min_bedrooms)
        fractions.append(min(1.0, (prop.bedrooms or 0) / minimum) if prop.bedrooms else 0.0)
    if criteria.household_size:
        needed = _bedroom_requirement(criteria.household_size)
        fractions.append(min(1.0, (prop.bedrooms or 0) / needed) if prop.bedrooms else 0.0)
    fraction = sum(fractions) / len(fractions)
    if prop.bedrooms:
        plural = "s" if prop.bedrooms != 1 else ""
        if fraction >= 0.999:
            reasons.append(f"{prop.bedrooms} bedroom{plural} — fits your space needs")
        elif fraction > 0:
            reasons.append(f"{prop.bedrooms} bedroom{plural} — below your space needs")
    return fraction


def _score_amenities(
    prop: Property, criteria: PropertyMatchRequest, reasons: List[str]
) -> Optional[float]:
    prop_tokens = set(_normalise(prop.amenities).split())
    requirements: List[Tuple[str, bool]] = []  # (display name, met)

    if criteria.require_parking:
        met = bool(prop.parking_spaces and prop.parking_spaces > 0) or bool(
            prop_tokens & {"parking", "garage"}
        )
        requirements.append(("parking", met))
    if criteria.require_security:
        met = bool(prop_tokens & {"security", "cctv", "gated", "guard", "guards", "alarm"})
        requirements.append(("24/7 security", met))
    if criteria.require_balcony:
        met = bool(prop_tokens & {"balcony", "terrace"})
        requirements.append(("balcony or terrace", met))
    for wanted in (criteria.amenities or [])[:6]:
        norm = _normalise(wanted)
        if not norm:
            continue
        met = all(word in prop_tokens for word in norm.split())
        requirements.append((wanted, met))

    if not requirements:
        return None
    met_names = [name for name, met in requirements if met]
    if met_names:
        reasons.append("Includes " + ", ".join(met_names))
    return len(met_names) / len(requirements)


def _score_furnishing(
    prop: Property, criteria: PropertyMatchRequest, reasons: List[str]
) -> float:
    wanted, actual = _normalise(criteria.furnishing), _normalise(prop.furnishing)
    if not wanted or not actual:
        return 0.0
    if wanted == actual:
        reasons.append(f"Furnishing matches ({prop.furnishing})")
        return 1.0
    if wanted in actual or actual in wanted:
        reasons.append(f"Furnishing close to your preference ({prop.furnishing})")
        return 0.5
    return 0.0


def _score_quality(prop: Property, reasons: List[str]) -> float:
    fraction = 0.0
    if prop.is_verified:
        fraction += 0.6
        reasons.append("Verified listing")
    if prop.image_url or prop.gallery_urls:
        fraction += 0.2
        reasons.append("Professional photos")
    if prop.description and len(prop.description.strip()) >= 80:
        fraction += 0.2
        reasons.append("Detailed listing description")
    return fraction


def _score_freshness(prop: Property, reasons: List[str]) -> float:
    created = as_utc(prop.created_at) if prop.created_at else None
    if created is None:
        return 0.5
    age_days = (utc_now() - created).total_seconds() / 86400
    if age_days <= 14:
        reasons.append("Recently listed")
        return 1.0
    if age_days <= 45:
        return 0.7
    if age_days <= 90:
        return 0.4
    return 0.2


def score_property(
    prop: Property, criteria: PropertyMatchRequest
) -> Optional[MatchScore]:
    """Score one listing. Returns None when it is excluded (way over budget)."""
    reasons: List[str] = []
    fractions: Dict[str, float] = {}

    if criteria.max_budget:
        budget = _score_budget(prop, criteria, reasons)
        if budget is None:
            return None
        fractions["Budget"] = budget

    if criteria.preferred_city:
        fraction, reason = _score_location(prop, criteria.preferred_city)
        fractions["Location"] = fraction
        if reason:
            reasons.append(reason)

    if criteria.min_bedrooms is not None or criteria.household_size:
        fractions["Size"] = _score_size(prop, criteria, reasons)

    if criteria.property_type:
        if _types_match(criteria.property_type, prop.property_type):
            fractions["Type"] = 1.0
            reasons.append(f"Matches the requested property type ({prop.property_type})")
        else:
            fractions["Type"] = 0.0

    amenities = _score_amenities(prop, criteria, reasons)
    if amenities is not None:
        fractions["Amenities"] = amenities

    if criteria.furnishing:
        fractions["Furnishing"] = _score_furnishing(prop, criteria, reasons)

    fractions["Quality"] = _score_quality(prop, reasons)
    fractions["Freshness"] = _score_freshness(prop, reasons)

    earned = sum(fraction * FACTOR_WEIGHTS[key] for key, fraction in fractions.items())
    available = sum(FACTOR_WEIGHTS[key] for key in fractions)
    raw = earned / available * 100 if available else 0.0
    score = max(0, min(100, int(round(raw))))

    # Round each factor's normalised contribution, then nudge the largest
    # one by the rounding drift so the breakdown always sums to the score.
    breakdown = {
        key: int(round(fraction * FACTOR_WEIGHTS[key] / available * 100))
        for key, fraction in fractions.items()
    }
    drift = score - sum(breakdown.values())
    if drift:
        top = max(breakdown, key=breakdown.get)
        breakdown[top] += drift

    return MatchScore(
        score=score,
        label=match_label(score),
        reasons=reasons,
        breakdown=breakdown,
    )


def rank_properties(
    properties: List[Property],
    criteria: PropertyMatchRequest,
    limit: int = 20,
) -> List[Tuple[Property, MatchScore]]:
    """Score and sort listings: best score first, signed-then-fresh tiebreak."""
    scored: List[Tuple[Property, MatchScore, float]] = []
    for prop in properties:
        result = score_property(prop, criteria)
        if result is None:
            continue
        created = as_utc(prop.created_at) if prop.created_at else None
        recency = created.timestamp() if created else 0.0
        scored.append((prop, result, recency))

    scored.sort(
        key=lambda item: (item[1].score, bool(item[0].is_verified), item[2]),
        reverse=True,
    )
    return [(prop, result) for prop, result, _ in scored[:limit]]
