"""Advanced analytics dashboards (P4-34).

Builds one role-scoped payload (admin: all properties, owner: owned, manager:
assigned) that the portal dashboards render as KPI cards, time-series charts
and distributions. Every money field is free-text in this schema, so amounts
are parsed with matching_service.parse_price — the same convention as the
reporting exports (P4-39).

Unlike the report builders, the time-series are *zero-filled* over the whole
requested window (the last `months` calendar months, ending with the current
one) so charts always render a continuous axis:

    {
        "generated_at": "...",
        "months": 6,
        "period": {"start": "2026-05", "end": "2026-10"},
        "kpis": {...},
        "series": {"financial": [...], "payments": [...], "maintenance": [...]},
        "distributions": {...},
        "top_properties": [...],
    }
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.lease import Lease
from app.models.maintenance import Maintenance
from app.models.payment import Payment
from app.models.property import Property
from app.models.unit import Unit
from app.models.user import User
from app.services.reports_service import (
    OPEN_MAINTENANCE_STATUSES,
    RESOLVED_MAINTENANCE_STATUSES,
    as_naive_utc,
    parse_amount,
    scope_property_ids,
)
from app.utils.time import utc_now

DEFAULT_MONTHS = 6
MONTHS_MIN = 3
MONTHS_MAX = 24
LIST_LIMIT = 8
TOP_PROPERTIES_LIMIT = 5
EXPIRING_SOON_DAYS = 30


def _month_keys(months: int, end: datetime) -> List[str]:
    """The last `months` calendar month keys, oldest first, ending with end's."""
    keys: List[str] = []
    year, month = end.year, end.month
    for _ in range(months):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(keys))


def _month_key(value: Optional[datetime]) -> Optional[str]:
    value = as_naive_utc(value)
    return value.strftime("%Y-%m") if value else None


def _scoped(db: Session, model, property_ids: Optional[List[int]]) -> List[Any]:
    """Rows restricted to the scoped properties (None -> all, [] -> none)."""
    if property_ids is not None and not property_ids:
        return []
    query = db.query(model)
    if property_ids is not None:
        query = query.filter(model.property_id.in_(property_ids))
    return query.all()


def _load_properties(db: Session, property_ids: Optional[List[int]]) -> List[Property]:
    if property_ids is not None and not property_ids:
        return []
    query = db.query(Property)
    if property_ids is not None:
        query = query.filter(Property.id.in_(property_ids))
    return query.order_by(Property.name.asc(), Property.id.asc()).all()


def build_analytics(
    db: Session,
    *,
    property_ids: Optional[List[int]],
    months: int = DEFAULT_MONTHS,
) -> Dict[str, Any]:
    """Build the analytics payload. `property_ids=None` means unscoped (admin)."""
    now = as_naive_utc(utc_now())
    keys = _month_keys(months, now)
    key_set = set(keys)
    expiring_cutoff = now + timedelta(days=EXPIRING_SOON_DAYS)

    properties = _load_properties(db, property_ids)
    units = _scoped(db, Unit, property_ids)
    leases = _scoped(db, Lease, property_ids)
    payments = _scoped(db, Payment, property_ids)
    maintenance = _scoped(db, Maintenance, property_ids)

    units_by_property: Dict[int, List[Unit]] = defaultdict(list)
    for unit in units:
        units_by_property[unit.property_id].append(unit)

    def unit_counts(prop: Property) -> tuple:
        prop_units = units_by_property.get(prop.id, [])
        count = len(prop_units) or (prop.units_count or 0)
        occupied = sum(1 for u in prop_units if (u.status or "").lower() == "occupied")
        return count, occupied

    total_units = 0
    occupied_units = 0
    for prop in properties:
        count, occupied = unit_counts(prop)
        total_units += count
        occupied_units += occupied

    # --- Series buckets ---------------------------------------------------
    payment_buckets: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"expected": 0.0, "collected": 0.0, "outstanding": 0.0}
    )
    income_by_month: Dict[str, float] = defaultdict(float)
    for payment in payments:
        status = (payment.status or "").lower()
        # Due date is the canonical month for expected/outstanding amounts;
        # payment date is the canonical month for cash actually received.
        due_key = _month_key(payment.due_date or payment.payment_date or payment.created_at)
        if due_key in key_set:
            amount = parse_amount(payment.amount)
            payment_buckets[due_key]["expected"] += amount
            if status == "paid":
                payment_buckets[due_key]["collected"] += amount
            else:
                payment_buckets[due_key]["outstanding"] += amount
        if status == "paid":
            paid_key = _month_key(payment.payment_date or payment.due_date or payment.created_at)
            if paid_key in key_set:
                income_by_month[paid_key] += parse_amount(payment.amount)

    maintenance_buckets: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"requests": 0, "resolved": 0, "cost": 0.0}
    )
    resolved_cost_by_month: Dict[str, float] = defaultdict(float)
    for item in maintenance:
        created_key = _month_key(item.created_at)
        if created_key in key_set:
            maintenance_buckets[created_key]["requests"] += 1
        if (item.status or "").lower() in RESOLVED_MAINTENANCE_STATUSES:
            resolved_key = _month_key(item.resolved_at or item.created_at)
            if resolved_key in key_set:
                maintenance_buckets[resolved_key]["resolved"] += 1
                resolved_cost_by_month[resolved_key] += parse_amount(item.cost)
    for key, cost in resolved_cost_by_month.items():
        maintenance_buckets[key]["cost"] = cost

    payments_series = []
    financial_series = []
    maintenance_series = []
    for key in keys:
        bucket = payment_buckets.get(key)
        expected = round(bucket["expected"], 2) if bucket else 0.0
        collected = round(bucket["collected"], 2) if bucket else 0.0
        payments_series.append({
            "month": key,
            "expected": expected,
            "collected": collected,
            "outstanding": round(bucket["outstanding"], 2) if bucket else 0.0,
        })
        income = round(income_by_month.get(key, 0.0), 2)
        expenses = round(resolved_cost_by_month.get(key, 0.0), 2)
        financial_series.append({
            "month": key,
            "income": income,
            "expenses": expenses,
            "net": round(income - expenses, 2),
        })
        maint = maintenance_buckets.get(key)
        maintenance_series.append({
            "month": key,
            "requests": int(maint["requests"]) if maint else 0,
            "resolved": int(maint["resolved"]) if maint else 0,
            "cost": round(maint["cost"], 2) if maint else 0.0,
        })

    # --- KPIs -------------------------------------------------------------
    active_leases = [lease for lease in leases if (lease.status or "").lower() == "active"]
    expiring_soon = 0
    for lease in active_leases:
        end = as_naive_utc(lease.end_date)
        if end is not None and now <= end <= expiring_cutoff:
            expiring_soon += 1

    period_expected = sum(point["expected"] for point in payments_series)
    period_collected = sum(point["collected"] for point in payments_series)
    period_expenses = sum(point["expenses"] for point in financial_series)

    kpis = {
        "properties": len(properties),
        "total_units": total_units,
        "occupied_units": occupied_units,
        "vacant_units": max(total_units - occupied_units, 0),
        "occupancy_rate": round(occupied_units / total_units * 100, 1) if total_units else 0,
        "active_leases": len(active_leases),
        "leases_expiring_soon": expiring_soon,
        "open_maintenance": sum(
            1 for item in maintenance if (item.status or "").lower() in OPEN_MAINTENANCE_STATUSES
        ),
        "overdue_payments": sum(1 for p in payments if (p.status or "").lower() == "overdue"),
        "period_expected": round(period_expected, 2),
        "period_collected": round(period_collected, 2),
        "period_collection_rate": round(period_collected / period_expected * 100, 1) if period_expected else 0,
        "period_expenses": round(period_expenses, 2),
        "period_net": round(period_collected - period_expenses, 2),
    }

    # --- Distributions ----------------------------------------------------
    units_status = Counter((unit.status or "unknown").lower() for unit in units)
    leases_status = Counter((lease.status or "unknown").lower() for lease in leases)

    city_counts = Counter((prop.city or "").strip() or "Unspecified" for prop in properties)
    ordered_cities = sorted(city_counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    properties_by_city = [{"city": city, "count": count} for city, count in ordered_cities[:LIST_LIMIT]]
    overflow = ordered_cities[LIST_LIMIT:]
    if overflow:
        properties_by_city.append({"city": "Other", "count": sum(count for _, count in overflow)})

    category_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"requests": 0, "open": 0, "cost": 0.0}
    )
    for item in maintenance:
        created_key = _month_key(item.created_at)
        if created_key not in key_set:
            continue
        name = (item.category or "").strip() or "Uncategorised"
        stats = category_stats[name]
        stats["requests"] += 1
        if (item.status or "").lower() in OPEN_MAINTENANCE_STATUSES:
            stats["open"] += 1
        stats["cost"] += parse_amount(item.cost)
    ordered_categories = sorted(category_stats.items(), key=lambda kv: (-kv[1]["requests"], kv[0].lower()))
    maintenance_by_category = [
        {
            "category": name,
            "requests": stats["requests"],
            "open": stats["open"],
            "cost": round(stats["cost"], 2),
        }
        for name, stats in ordered_categories[:LIST_LIMIT]
    ]

    # --- Property leaderboard ----------------------------------------------
    collected_by_property: Dict[int, float] = defaultdict(float)
    outstanding_by_property: Dict[int, float] = defaultdict(float)
    for payment in payments:
        amount = parse_amount(payment.amount)
        status = (payment.status or "").lower()
        due_key = _month_key(payment.due_date or payment.payment_date or payment.created_at)
        if due_key not in key_set:
            continue
        if status == "paid":
            collected_by_property[payment.property_id] += amount
        else:
            outstanding_by_property[payment.property_id] += amount

    top_rows: List[Dict[str, Any]] = []
    for prop in properties:
        count, occupied = unit_counts(prop)
        top_rows.append({
            "property_id": prop.id,
            "name": prop.name,
            "city": prop.city or "—",
            "units": count,
            "occupied": occupied,
            "occupancy_rate": round(occupied / count * 100, 1) if count else 0,
            "collected": round(collected_by_property.get(prop.id, 0.0), 2),
            "outstanding": round(outstanding_by_property.get(prop.id, 0.0), 2),
        })
    top_rows.sort(key=lambda row: (-row["collected"], -row["outstanding"], row["name"].lower()))
    top_properties = top_rows[:TOP_PROPERTIES_LIMIT]

    return {
        "generated_at": now.isoformat(),
        "months": months,
        "period": {"start": keys[0], "end": keys[-1]},
        "kpis": kpis,
        "series": {
            "financial": financial_series,
            "payments": payments_series,
            "maintenance": maintenance_series,
        },
        "distributions": {
            "units_by_status": dict(sorted(units_status.items())),
            "leases_by_status": dict(sorted(leases_status.items())),
            "properties_by_city": properties_by_city,
            "maintenance_by_category": maintenance_by_category,
        },
        "top_properties": top_properties,
    }
