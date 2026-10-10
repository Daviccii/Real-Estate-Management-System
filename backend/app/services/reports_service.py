"""Advanced reporting exports (P4-39).

Builds four report types — occupancy, payments, maintenance and financial —
over the properties a caller may see (admin: all, owner: owned, manager:
assigned). Money fields across the schema are free-text (Payment.amount,
Lease.rent_amount, Maintenance.cost, ...), so every amount is parsed with
matching_service.parse_price rather than a SQL CAST that would silently
zero out values like "KSh 45,000/Month".

All builders return the same envelope so the router can serve it directly
as JSON or stream the identical rows as CSV:

    {
        "report_type": "occupancy",
        "generated_at": "...",
        "filters": {...},
        "summary": [{"key", "label", "value"}, ...],
        "columns": [{"key", "label"}, ...],
        "rows": [{...}, ...],
    }
"""
import csv
import io
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.lease import Lease
from app.models.maintenance import Maintenance
from app.models.payment import Payment
from app.models.property import Property
from app.models.unit import Unit
from app.models.user import User
from app.services.matching_service import parse_price
from app.utils.time import utc_now

REPORT_TYPES = ("occupancy", "payments", "maintenance", "financial")

OPEN_MAINTENANCE_STATUSES = ("pending", "in_progress")
RESOLVED_MAINTENANCE_STATUSES = ("resolved", "closed")


def parse_amount(value: Any) -> float:
    """Free-text amount -> float; unparseable values count as 0."""
    amount = parse_price(value)
    return float(amount) if amount is not None else 0.0


def as_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normalise aware/naive datetimes so comparisons never raise."""
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _in_range(value: Optional[datetime], date_from: Optional[datetime], date_to: Optional[datetime]) -> bool:
    value = as_naive_utc(value)
    if value is None:
        return date_from is None and date_to is None
    if date_from is not None and value < date_from:
        return False
    if date_to is not None and value > date_to:
        return False
    return True


def scope_property_ids(db: Session, user: User) -> Optional[List[int]]:
    """Property ids the user may report on; None means "all" (admin)."""
    if user.role == "admin":
        return None
    query = db.query(Property.id)
    if user.role == "manager":
        query = query.filter(Property.manager_id == user.id)
    elif user.role == "owner":
        query = query.filter(Property.owner_id == user.id)
    else:
        return []
    return [row[0] for row in query.all()]


def build_report(
    db: Session,
    report_type: str,
    *,
    property_ids: Optional[List[int]],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    property_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Build one report envelope. `property_ids=None` means unscoped (admin)."""
    date_from = as_naive_utc(date_from)
    date_to = as_naive_utc(date_to)

    if report_type not in REPORT_TYPES:
        raise ValueError(f"Unknown report type: {report_type}")

    properties = _load_properties(db, property_ids, property_id)
    effective_ids = [p.id for p in properties]

    if report_type == "occupancy":
        summary, columns, rows = _occupancy_report(db, properties, effective_ids)
    elif report_type == "payments":
        summary, columns, rows = _payments_report(db, effective_ids, date_from, date_to)
    elif report_type == "maintenance":
        summary, columns, rows = _maintenance_report(db, effective_ids, date_from, date_to)
    else:
        summary, columns, rows = _financial_report(db, effective_ids, date_from, date_to)

    return {
        "report_type": report_type,
        "generated_at": utc_now().isoformat(),
        "filters": {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "property_id": property_id,
        },
        "summary": summary,
        "columns": columns,
        "rows": rows,
    }


def _load_properties(
    db: Session, property_ids: Optional[List[int]], property_id: Optional[int]
) -> List[Property]:
    if property_ids is not None and not property_ids:
        return []
    query = db.query(Property)
    if property_ids is not None:
        query = query.filter(Property.id.in_(property_ids))
    if property_id is not None:
        query = query.filter(Property.id == property_id)
    return query.order_by(Property.name.asc(), Property.id.asc()).all()


def _scoped(db: Session, model, effective_ids: List[int]):
    """Query `model` restricted to the report's property ids ([] -> no rows)."""
    if not effective_ids:
        return []
    return db.query(model).filter(model.property_id.in_(effective_ids)).all()


def _occupancy_report(db: Session, properties: List[Property], effective_ids: List[int]):
    # Point-in-time snapshot: date filters intentionally do not apply here.
    units = _scoped(db, Unit, effective_ids)
    active_leases = db.query(Lease).filter(
        Lease.property_id.in_(effective_ids), Lease.status == "active"
    ).all() if effective_ids else []

    units_by_property: Dict[int, List[Unit]] = defaultdict(list)
    for unit in units:
        units_by_property[unit.property_id].append(unit)
    leases_by_property: Dict[int, int] = defaultdict(int)
    for lease in active_leases:
        leases_by_property[lease.property_id] += 1

    rows: List[Dict[str, Any]] = []
    total_units = 0
    occupied_units = 0
    for prop in properties:
        prop_units = units_by_property.get(prop.id, [])
        unit_count = len(prop_units) or (prop.units_count or 0)
        occupied = sum(1 for u in prop_units if (u.status or "").lower() == "occupied")
        total_units += unit_count
        occupied_units += occupied
        rows.append({
            "property": prop.name,
            "city": prop.city or "—",
            "units": unit_count,
            "occupied": occupied,
            "vacant": max(unit_count - occupied, 0),
            "occupancy_rate": round(occupied / unit_count * 100, 1) if unit_count else 0,
            "active_leases": leases_by_property.get(prop.id, 0),
        })

    vacant_units = max(total_units - occupied_units, 0)
    summary = [
        {"key": "properties", "label": "Properties", "value": len(properties)},
        {"key": "total_units", "label": "Total units", "value": total_units},
        {"key": "occupied_units", "label": "Occupied units", "value": occupied_units},
        {"key": "vacant_units", "label": "Vacant units", "value": vacant_units},
        {
            "key": "occupancy_rate",
            "label": "Occupancy rate %",
            "value": round(occupied_units / total_units * 100, 1) if total_units else 0,
        },
    ]
    columns = [
        {"key": "property", "label": "Property"},
        {"key": "city", "label": "City"},
        {"key": "units", "label": "Units"},
        {"key": "occupied", "label": "Occupied"},
        {"key": "vacant", "label": "Vacant"},
        {"key": "occupancy_rate", "label": "Occupancy %"},
        {"key": "active_leases", "label": "Active leases"},
    ]
    return summary, columns, rows


def _payments_report(db: Session, effective_ids: List[int], date_from, date_to):
    payments = _scoped(db, Payment, effective_ids)
    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"payments": 0, "expected": 0.0, "collected": 0.0, "outstanding": 0.0, "overdue_count": 0}
    )
    for payment in payments:
        when = payment.due_date or payment.payment_date or payment.created_at
        if not _in_range(when, date_from, date_to):
            continue
        bucket = buckets[as_naive_utc(when).strftime("%Y-%m")]
        amount = parse_amount(payment.amount)
        bucket["payments"] += 1
        bucket["expected"] += amount
        if (payment.status or "").lower() == "paid":
            bucket["collected"] += amount
        else:
            bucket["outstanding"] += amount
        if (payment.status or "").lower() == "overdue":
            bucket["overdue_count"] += 1

    rows: List[Dict[str, Any]] = []
    for month in sorted(buckets):
        bucket = buckets[month]
        expected = round(bucket["expected"], 2)
        collected = round(bucket["collected"], 2)
        rows.append({
            "month": month,
            "payments": bucket["payments"],
            "expected": expected,
            "collected": collected,
            "outstanding": round(bucket["outstanding"], 2),
            "overdue_count": bucket["overdue_count"],
            "collection_rate": round(collected / expected * 100, 1) if expected else 0,
        })

    expected_total = sum(r["expected"] for r in rows)
    collected_total = sum(r["collected"] for r in rows)
    summary = [
        {"key": "months", "label": "Months", "value": len(rows)},
        {"key": "total_payments", "label": "Payments", "value": sum(r["payments"] for r in rows)},
        {"key": "expected", "label": "Expected", "value": round(expected_total, 2)},
        {"key": "collected", "label": "Collected", "value": round(collected_total, 2)},
        {"key": "outstanding", "label": "Outstanding", "value": round(sum(r["outstanding"] for r in rows), 2)},
        {"key": "overdue_count", "label": "Overdue", "value": sum(r["overdue_count"] for r in rows)},
        {
            "key": "collection_rate",
            "label": "Collection rate %",
            "value": round(collected_total / expected_total * 100, 1) if expected_total else 0,
        },
    ]
    columns = [
        {"key": "month", "label": "Month"},
        {"key": "payments", "label": "Payments"},
        {"key": "expected", "label": "Expected"},
        {"key": "collected", "label": "Collected"},
        {"key": "outstanding", "label": "Outstanding"},
        {"key": "overdue_count", "label": "Overdue"},
        {"key": "collection_rate", "label": "Collection %"},
    ]
    return summary, columns, rows


def _maintenance_report(db: Session, effective_ids: List[int], date_from, date_to):
    requests = _scoped(db, Maintenance, effective_ids)
    categories: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "open": 0, "resolved": 0, "total_cost": 0.0, "_days": []}
    )
    for item in requests:
        if not _in_range(item.created_at, date_from, date_to):
            continue
        name = (item.category or "").strip() or "Uncategorised"
        bucket = categories[name]
        bucket["total"] += 1
        status = (item.status or "").lower()
        if status in OPEN_MAINTENANCE_STATUSES:
            bucket["open"] += 1
        if status in RESOLVED_MAINTENANCE_STATUSES:
            bucket["resolved"] += 1
            created = as_naive_utc(item.created_at)
            resolved_at = as_naive_utc(item.resolved_at)
            if created and resolved_at:
                bucket["_days"].append(max((resolved_at - created).total_seconds() / 86400.0, 0.0))
        bucket["total_cost"] += parse_amount(item.cost)

    rows: List[Dict[str, Any]] = []
    all_days: List[float] = []
    for name in sorted(categories, key=str.lower):
        bucket = categories[name]
        all_days.extend(bucket["_days"])
        rows.append({
            "category": name,
            "total": bucket["total"],
            "open": bucket["open"],
            "resolved": bucket["resolved"],
            "avg_days": round(sum(bucket["_days"]) / len(bucket["_days"]), 1) if bucket["_days"] else None,
            "total_cost": round(bucket["total_cost"], 2),
        })

    summary = [
        {"key": "categories", "label": "Categories", "value": len(rows)},
        {"key": "total_requests", "label": "Requests", "value": sum(r["total"] for r in rows)},
        {"key": "open", "label": "Open", "value": sum(r["open"] for r in rows)},
        {"key": "resolved", "label": "Resolved", "value": sum(r["resolved"] for r in rows)},
        {
            "key": "avg_resolution_days",
            "label": "Avg resolution (days)",
            "value": round(sum(all_days) / len(all_days), 1) if all_days else None,
        },
        {"key": "total_cost", "label": "Total cost", "value": round(sum(r["total_cost"] for r in rows), 2)},
    ]
    columns = [
        {"key": "category", "label": "Category"},
        {"key": "total", "label": "Requests"},
        {"key": "open", "label": "Open"},
        {"key": "resolved", "label": "Resolved"},
        {"key": "avg_days", "label": "Avg resolution (days)"},
        {"key": "total_cost", "label": "Total cost"},
    ]
    return summary, columns, rows


def _financial_report(db: Session, effective_ids: List[int], date_from, date_to):
    income_by_month: Dict[str, float] = defaultdict(float)
    for payment in _scoped(db, Payment, effective_ids):
        if (payment.status or "").lower() != "paid":
            continue
        when = payment.payment_date or payment.due_date or payment.created_at
        if not _in_range(when, date_from, date_to):
            continue
        income_by_month[as_naive_utc(when).strftime("%Y-%m")] += parse_amount(payment.amount)

    expenses_by_month: Dict[str, float] = defaultdict(float)
    for item in _scoped(db, Maintenance, effective_ids):
        if (item.status or "").lower() not in RESOLVED_MAINTENANCE_STATUSES:
            continue
        when = item.resolved_at or item.created_at
        if not _in_range(when, date_from, date_to):
            continue
        expenses_by_month[as_naive_utc(when).strftime("%Y-%m")] += parse_amount(item.cost)

    rows: List[Dict[str, Any]] = []
    for month in sorted(set(income_by_month) | set(expenses_by_month)):
        income = round(income_by_month.get(month, 0.0), 2)
        expenses = round(expenses_by_month.get(month, 0.0), 2)
        rows.append({
            "month": month,
            "income": income,
            "expenses": expenses,
            "net": round(income - expenses, 2),
        })

    total_income = sum(r["income"] for r in rows)
    total_expenses = sum(r["expenses"] for r in rows)
    summary = [
        {"key": "months", "label": "Months", "value": len(rows)},
        {"key": "total_income", "label": "Income", "value": round(total_income, 2)},
        {"key": "total_expenses", "label": "Expenses", "value": round(total_expenses, 2)},
        {"key": "net_income", "label": "Net", "value": round(total_income - total_expenses, 2)},
    ]
    columns = [
        {"key": "month", "label": "Month"},
        {"key": "income", "label": "Income"},
        {"key": "expenses", "label": "Expenses"},
        {"key": "net", "label": "Net"},
    ]
    return summary, columns, rows


_CSV_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")
    text = str(value)
    # Spreadsheet formula injection guard: text cells that begin with a
    # formula trigger are prefixed so Excel/Sheets treat them as text.
    if text.startswith(_CSV_INJECTION_PREFIXES):
        return "'" + text
    return text


def to_csv(report: Dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([column["label"] for column in report["columns"]])
    for row in report["rows"]:
        writer.writerow([_csv_value(row.get(column["key"])) for column in report["columns"]])
    return buffer.getvalue()
