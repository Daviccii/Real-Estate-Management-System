"""Tests for advanced reporting exports (P4-39)."""
import uuid
from datetime import datetime, timedelta

from app.models.lease import Lease
from app.models.maintenance import Maintenance
from app.models.payment import Payment
from app.models.property import Property
from app.models.unit import Unit
from app.models.user import User
from app.utils.time import utc_now

PASSWORD = "Str0ng!TestPass42"


def _register(client, db_session, role, prefix):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": email, "password": PASSWORD})
    assert resp.status_code in (200, 201), resp.text
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    user.roles_csv = role
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client, email):
    resp = client.post('/api/auth/login', json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_property(db_session, owner, *, name, manager=None, city="Nairobi", units_count=1):
    prop = Property(
        owner_id=owner.id,
        manager_id=manager.id if manager else None,
        name=name,
        city=city,
        status="active",
        units_count=units_count,
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop


def _make_unit(db_session, prop, number, *, status="available", rent="45000"):
    unit = Unit(property_id=prop.id, unit_number=number, rent=rent, status=status)
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    return unit


def _make_lease(db_session, prop, unit, tenant, *, rent_amount="45000", status="active"):
    now = utc_now()
    lease = Lease(
        tenant_id=tenant.id,
        unit_id=unit.id,
        property_id=prop.id,
        start_date=now - timedelta(days=90),
        end_date=now + timedelta(days=275),
        rent_amount=rent_amount,
        status=status,
    )
    db_session.add(lease)
    db_session.commit()
    db_session.refresh(lease)
    return lease


def _make_payment(db_session, prop, unit, tenant, lease, *, amount, status, due_date, payment_date=None):
    payment = Payment(
        tenant_id=tenant.id,
        lease_id=lease.id,
        property_id=prop.id,
        unit_id=unit.id,
        amount=amount,
        status=status,
        due_date=due_date,
        payment_date=payment_date,
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


def _month_bounds():
    """Deterministic samples in the current and previous calendar month."""
    now = utc_now()
    first_of_month = now.replace(day=1, hour=12, minute=0, second=0, microsecond=0)
    return {
        "this": first_of_month,
        "this_key": first_of_month.strftime("%Y-%m"),
        "prev": first_of_month - timedelta(days=2),
        "prev_key": (first_of_month - timedelta(days=2)).strftime("%Y-%m"),
    }


def test_occupancy_report_scoped_by_role(client, db_session):
    owner = _register(client, db_session, "owner", "rep_occ_owner")
    manager_a = _register(client, db_session, "manager", "rep_occ_mgr_a")
    manager_b = _register(client, db_session, "manager", "rep_occ_mgr_b")
    tenant = _register(client, db_session, "tenant", "rep_occ_tenant")

    prop_a = _make_property(db_session, owner, name="Alpha Court", manager=manager_a, units_count=2)
    unit_a1 = _make_unit(db_session, prop_a, "A1", status="occupied")
    _make_unit(db_session, prop_a, "A2", status="available")
    _make_lease(db_session, prop_a, unit_a1, tenant)

    prop_b = _make_property(db_session, owner, name="Beta Towers", manager=manager_b, units_count=1)
    _make_unit(db_session, prop_b, "B1", status="available")

    headers_a = _login(client, manager_a.email)
    resp = client.get('/api/reports/occupancy', headers=headers_a)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["report_type"] == "occupancy"
    assert data["summary"][0]["value"] == 1  # only their property
    assert [r["property"] for r in data["rows"]] == ["Alpha Court"]
    row = data["rows"][0]
    assert row["units"] == 2
    assert row["occupied"] == 1
    assert row["vacant"] == 1
    assert row["occupancy_rate"] == 50.0
    assert row["active_leases"] == 1

    # Owner sees both of their properties.
    resp = client.get('/api/reports/occupancy', headers=_login(client, owner.email))
    assert resp.status_code == 200
    assert {r["property"] for r in resp.json()["rows"]} == {"Alpha Court", "Beta Towers"}

    # Manager B only sees theirs.
    resp = client.get('/api/reports/occupancy', headers=_login(client, manager_b.email))
    assert [r["property"] for r in resp.json()["rows"]] == ["Beta Towers"]


def test_admin_sees_all_properties(client, db_session):
    admin = _register(client, db_session, "admin", "rep_admin")
    owner = _register(client, db_session, "owner", "rep_admin_owner")
    _make_property(db_session, owner, name="Gamma House")

    resp = client.get('/api/reports/occupancy', headers=_login(client, admin.email))
    assert resp.status_code == 200
    assert any(r["property"] == "Gamma House" for r in resp.json()["rows"])


def test_reports_require_authenticated_staff_role(client, db_session):
    resp = client.get('/api/reports/occupancy')
    assert resp.status_code in (401, 403)

    tenant = _register(client, db_session, "tenant", "rep_gate_tenant")
    resp = client.get('/api/reports/occupancy', headers=_login(client, tenant.email))
    assert resp.status_code == 403


def test_payments_report_monthly_buckets_and_free_text_amounts(client, db_session):
    owner = _register(client, db_session, "owner", "rep_pay_owner")
    tenant = _register(client, db_session, "tenant", "rep_pay_tenant")
    prop = _make_property(db_session, owner, name="Rent Roll")
    unit = _make_unit(db_session, prop, "1")
    lease = _make_lease(db_session, prop, unit, tenant)
    bounds = _month_bounds()

    _make_payment(
        db_session, prop, unit, tenant, lease,
        amount="KSh 45,000", status="paid",
        due_date=bounds["this"], payment_date=bounds["this"],
    )
    _make_payment(
        db_session, prop, unit, tenant, lease,
        amount="45k", status="pending", due_date=bounds["prev"],
    )
    _make_payment(
        db_session, prop, unit, tenant, lease,
        amount="120000", status="overdue", due_date=bounds["prev"],
    )

    resp = client.get('/api/reports/payments', headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    rows = {r["month"]: r for r in data["rows"]}

    this_row = rows[bounds["this_key"]]
    assert this_row["payments"] == 1
    assert this_row["expected"] == 45000.0  # "KSh 45,000" parsed, not CAST-ed
    assert this_row["collected"] == 45000.0
    assert this_row["collection_rate"] == 100.0

    prev_row = rows[bounds["prev_key"]]
    assert prev_row["payments"] == 2
    assert prev_row["expected"] == 165000.0  # "45k" + "120000"
    assert prev_row["collected"] == 0
    assert prev_row["outstanding"] == 165000.0
    assert prev_row["overdue_count"] == 1

    summary = {s["key"]: s["value"] for s in data["summary"]}
    assert summary["total_payments"] == 3
    assert summary["collected"] == 45000.0
    assert summary["outstanding"] == 165000.0
    assert summary["overdue_count"] == 1


def test_payments_report_date_filter(client, db_session):
    owner = _register(client, db_session, "owner", "rep_paydate_owner")
    tenant = _register(client, db_session, "tenant", "rep_paydate_tenant")
    prop = _make_property(db_session, owner, name="Dated")
    unit = _make_unit(db_session, prop, "1")
    lease = _make_lease(db_session, prop, unit, tenant)
    bounds = _month_bounds()

    _make_payment(db_session, prop, unit, tenant, lease, amount="1000", status="paid", due_date=bounds["this"])
    _make_payment(db_session, prop, unit, tenant, lease, amount="2000", status="paid", due_date=bounds["prev"])

    resp = client.get(
        '/api/reports/payments',
        params={"date_from": bounds["this"].date().isoformat()},
        headers=_login(client, owner.email),
    )
    assert resp.status_code == 200
    rows = resp.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["month"] == bounds["this_key"]
    assert rows[0]["expected"] == 1000.0


def test_maintenance_report_per_category(client, db_session):
    owner = _register(client, db_session, "owner", "rep_maint_owner")
    prop = _make_property(db_session, owner, name="Fixer Upper")
    now = utc_now()

    db_session.add(Maintenance(
        property_id=prop.id, title="Leak", category="Plumbing",
        status="resolved", cost="5,000",
        created_at=now - timedelta(days=10), resolved_at=now - timedelta(days=4),
    ))
    db_session.add(Maintenance(
        property_id=prop.id, title="Wiring", category="Electrical",
        status="pending", cost="KSh 2,500",
        created_at=now - timedelta(days=1),
    ))
    db_session.commit()

    resp = client.get('/api/reports/maintenance', headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    rows = {r["category"]: r for r in data["rows"]}

    assert rows["Plumbing"]["total"] == 1
    assert rows["Plumbing"]["resolved"] == 1
    assert rows["Plumbing"]["avg_days"] == 6.0
    assert rows["Plumbing"]["total_cost"] == 5000.0  # "5,000" parsed
    assert rows["Electrical"]["open"] == 1
    assert rows["Electrical"]["avg_days"] is None
    assert rows["Electrical"]["total_cost"] == 2500.0

    summary = {s["key"]: s["value"] for s in data["summary"]}
    assert summary["total_requests"] == 2
    assert summary["open"] == 1
    assert summary["resolved"] == 1
    assert summary["avg_resolution_days"] == 6.0
    assert summary["total_cost"] == 7500.0


def test_financial_report_income_expenses_net(client, db_session):
    owner = _register(client, db_session, "owner", "rep_fin_owner")
    tenant = _register(client, db_session, "tenant", "rep_fin_tenant")
    prop = _make_property(db_session, owner, name="Ledger House")
    unit = _make_unit(db_session, prop, "1")
    lease = _make_lease(db_session, prop, unit, tenant)
    bounds = _month_bounds()

    _make_payment(
        db_session, prop, unit, tenant, lease,
        amount="60000", status="paid",
        due_date=bounds["this"], payment_date=bounds["this"],
    )
    # Pending payments must not count as income.
    _make_payment(db_session, prop, unit, tenant, lease, amount="9000", status="pending", due_date=bounds["this"])
    db_session.add(Maintenance(
        property_id=prop.id, title="Repaint", category="General",
        status="resolved", cost="10,000",
        created_at=bounds["this"] - timedelta(days=3), resolved_at=bounds["this"],
    ))
    # Unresolved maintenance must not count as expense.
    db_session.add(Maintenance(
        property_id=prop.id, title="Quote", category="General",
        status="pending", cost="99999", created_at=bounds["this"],
    ))
    db_session.commit()

    resp = client.get('/api/reports/financial', headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    row = next(r for r in data["rows"] if r["month"] == bounds["this_key"])
    assert row["income"] == 60000.0
    assert row["expenses"] == 10000.0
    assert row["net"] == 50000.0

    summary = {s["key"]: s["value"] for s in data["summary"]}
    assert summary["total_income"] == 60000.0
    assert summary["total_expenses"] == 10000.0
    assert summary["net_income"] == 50000.0


def test_csv_export_headers_and_attachment(client, db_session):
    owner = _register(client, db_session, "owner", "rep_csv_owner")
    prop = _make_property(db_session, owner, name="Comma, Inc.")
    _make_unit(db_session, prop, "1", status="occupied")

    resp = client.get('/api/reports/occupancy', params={"format": "csv"}, headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    assert ".csv" in resp.headers["content-disposition"]

    lines = resp.text.strip().splitlines()
    assert lines[0] == "Property,City,Units,Occupied,Vacant,Occupancy %,Active leases"
    assert lines[1].startswith('"Comma, Inc."')  # csv quoting intact


def test_csv_formula_injection_guard(client, db_session):
    owner = _register(client, db_session, "owner", "rep_inject_owner")
    _make_property(db_session, owner, name="=SUM(A1:A9)")

    resp = client.get('/api/reports/occupancy', params={"format": "csv"}, headers=_login(client, owner.email))
    assert resp.status_code == 200
    assert "'=SUM(A1:A9)" in resp.text


def test_property_filter_scoped_and_404_for_out_of_scope(client, db_session):
    owner = _register(client, db_session, "owner", "rep_filter_owner")
    manager_a = _register(client, db_session, "manager", "rep_filter_mgr_a")
    manager_b = _register(client, db_session, "manager", "rep_filter_mgr_b")

    prop_a = _make_property(db_session, owner, name="Filtered In", manager=manager_a)
    prop_b = _make_property(db_session, owner, name="Filtered Out", manager=manager_b)

    headers = _login(client, manager_a.email)
    resp = client.get('/api/reports/occupancy', params={"property_id": prop_a.id}, headers=headers)
    assert resp.status_code == 200
    assert [r["property"] for r in resp.json()["rows"]] == ["Filtered In"]

    resp = client.get('/api/reports/occupancy', params={"property_id": prop_b.id}, headers=headers)
    assert resp.status_code == 404


def test_report_validation_errors(client, db_session):
    owner = _register(client, db_session, "owner", "rep_errors_owner")
    headers = _login(client, owner.email)

    resp = client.get('/api/reports/nonsense', headers=headers)
    assert resp.status_code == 404

    resp = client.get(
        '/api/reports/payments',
        params={"date_from": "2026-05-01", "date_to": "2026-04-01"},
        headers=headers,
    )
    assert resp.status_code == 400

    resp = client.get('/api/reports/payments', params={"format": "xml"}, headers=headers)
    assert resp.status_code == 422
