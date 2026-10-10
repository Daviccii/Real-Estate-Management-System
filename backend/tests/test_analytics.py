"""Tests for advanced analytics dashboards (P4-34)."""
import uuid
from datetime import timedelta

from app.models.lease import Lease
from app.models.maintenance import Maintenance
from app.models.payment import Payment
from app.models.property import Property
from app.models.unit import Unit
from app.models.user import User
from app.utils.time import utc_now

PASSWORD = "Str0ng!TestPass42"

DASHBOARD = '/api/analytics/dashboard'


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


def _make_lease(db_session, prop, unit, tenant, *, rent_amount="45000", status="active",
                start_date=None, end_date=None):
    now = utc_now()
    lease = Lease(
        tenant_id=tenant.id,
        unit_id=unit.id,
        property_id=prop.id,
        start_date=start_date or now - timedelta(days=90),
        end_date=end_date or now + timedelta(days=275),
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


def _make_maintenance(db_session, prop, *, category, status, cost=None, created_at, resolved_at=None):
    item = Maintenance(
        property_id=prop.id,
        title=f"{category or 'misc'} issue",
        category=category,
        status=status,
        cost=cost,
        created_at=created_at,
        resolved_at=resolved_at,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def _month_anchor(months_back):
    """(key, naive-UTC 12:00 on day 1) for the month N back from the current one."""
    now = utc_now()
    year, month = now.year, now.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    key = f"{year:04d}-{month:02d}"
    anchor = now.replace(year=year, month=month, day=1, hour=12, minute=0, second=0, microsecond=0)
    return key, anchor.replace(tzinfo=None)


def test_analytics_requires_authenticated_staff_role(client, db_session):
    resp = client.get(DASHBOARD)
    assert resp.status_code in (401, 403)

    tenant = _register(client, db_session, "tenant", "an_gate_tenant")
    resp = client.get(DASHBOARD, headers=_login(client, tenant.email))
    assert resp.status_code == 403


def test_months_validation_bounds(client, db_session):
    owner = _register(client, db_session, "owner", "an_bounds_owner")
    headers = _login(client, owner.email)

    assert client.get(DASHBOARD, params={"months": 2}, headers=headers).status_code == 422
    assert client.get(DASHBOARD, params={"months": 25}, headers=headers).status_code == 422
    assert client.get(DASHBOARD, params={"months": 3}, headers=headers).status_code == 200


def test_months_window_zero_filled_and_excludes_old_data(client, db_session):
    owner = _register(client, db_session, "owner", "an_window_owner")
    tenant = _register(client, db_session, "tenant", "an_window_tenant")
    prop = _make_property(db_session, owner, name="Window Court")
    unit = _make_unit(db_session, prop, "1")
    lease = _make_lease(db_session, prop, unit, tenant)

    old_key, old_dt = _month_anchor(4)
    _make_payment(
        db_session, prop, unit, tenant, lease,
        amount="7777", status="paid", due_date=old_dt, payment_date=old_dt,
    )

    headers = _login(client, owner.email)
    resp = client.get(DASHBOARD, params={"months": 3}, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    this_key = _month_anchor(0)[0]
    prev2_key = _month_anchor(2)[0]
    assert data["months"] == 3
    assert data["period"] == {"start": prev2_key, "end": this_key}
    payments = data["series"]["payments"]
    financial = data["series"]["financial"]
    assert [p["month"] for p in payments] == [prev2_key, _month_anchor(1)[0], this_key]
    assert all(p["expected"] == 0 and p["collected"] == 0 for p in payments)  # 4-back payment excluded
    assert all(f["income"] == 0 for f in financial)
    assert data["kpis"]["period_expected"] == 0

    resp = client.get(DASHBOARD, params={"months": 6}, headers=headers)
    data = resp.json()
    assert data["months"] == 6
    assert len(data["series"]["payments"]) == 6
    rows = {p["month"]: p for p in data["series"]["payments"]}
    assert rows[old_key]["expected"] == 7777.0
    assert rows[old_key]["collected"] == 7777.0
    assert data["kpis"]["period_collected"] == 7777.0


def test_role_scoping_manager_owner_admin(client, db_session):
    owner = _register(client, db_session, "owner", "an_scope_owner")
    manager_a = _register(client, db_session, "manager", "an_scope_mgr_a")
    manager_b = _register(client, db_session, "manager", "an_scope_mgr_b")

    _make_property(db_session, owner, name="Alpha Court", manager=manager_a, units_count=2)
    _make_property(db_session, owner, name="Beta Towers", manager=manager_b, units_count=5)

    headers_a = _login(client, manager_a.email)
    resp = client.get(DASHBOARD, headers=headers_a)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["kpis"]["properties"] == 1
    assert data["kpis"]["total_units"] == 2
    assert [row["name"] for row in data["top_properties"]] == ["Alpha Court"]

    resp = client.get(DASHBOARD, headers=_login(client, owner.email))
    data = resp.json()
    assert data["kpis"]["properties"] == 2
    assert data["kpis"]["total_units"] == 7
    assert {row["name"] for row in data["top_properties"]} == {"Alpha Court", "Beta Towers"}

    admin = _register(client, db_session, "admin", "an_scope_admin")
    resp = client.get(DASHBOARD, headers=_login(client, admin.email))
    data = resp.json()
    assert data["kpis"]["properties"] >= 2
    assert {"Alpha Court", "Beta Towers"} <= {row["name"] for row in data["top_properties"]}


def test_manager_without_properties_gets_empty_scope(client, db_session):
    owner = _register(client, db_session, "owner", "an_empty_owner")
    _make_property(db_session, owner, name="Not Mine")
    manager = _register(client, db_session, "manager", "an_empty_mgr")

    resp = client.get(DASHBOARD, headers=_login(client, manager.email))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["kpis"]["properties"] == 0
    assert data["kpis"]["total_units"] == 0
    assert data["top_properties"] == []
    assert data["distributions"]["properties_by_city"] == []
    assert len(data["series"]["financial"]) == 6
    assert all(point["income"] == 0 for point in data["series"]["financial"])


def test_payments_and_financial_series_parse_free_text_amounts(client, db_session):
    owner = _register(client, db_session, "owner", "an_money_owner")
    tenant = _register(client, db_session, "tenant", "an_money_tenant")
    prop = _make_property(db_session, owner, name="Rent Roll")
    unit = _make_unit(db_session, prop, "1")
    lease = _make_lease(db_session, prop, unit, tenant)
    this_key, this_dt = _month_anchor(0)
    prev_key, prev_dt = _month_anchor(1)

    _make_payment(
        db_session, prop, unit, tenant, lease,
        amount="KSh 45,000", status="paid", due_date=this_dt, payment_date=this_dt,
    )
    _make_payment(db_session, prop, unit, tenant, lease, amount="45k", status="pending", due_date=prev_dt)
    _make_payment(db_session, prop, unit, tenant, lease, amount="120000", status="overdue", due_date=prev_dt)

    resp = client.get(DASHBOARD, headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    rows = {p["month"]: p for p in data["series"]["payments"]}

    assert rows[this_key]["expected"] == 45000.0
    assert rows[this_key]["collected"] == 45000.0
    assert rows[this_key]["outstanding"] == 0
    assert rows[prev_key]["expected"] == 165000.0
    assert rows[prev_key]["collected"] == 0
    assert rows[prev_key]["outstanding"] == 165000.0

    financial = {f["month"]: f for f in data["series"]["financial"]}
    assert financial[this_key]["income"] == 45000.0  # paid in this month
    assert financial[this_key]["net"] == 45000.0
    assert financial[prev_key]["income"] == 0  # unpaid amounts are not cash income

    assert data["kpis"]["period_expected"] == 210000.0
    assert data["kpis"]["period_collected"] == 45000.0
    assert data["kpis"]["period_collection_rate"] == 21.4
    assert data["kpis"]["overdue_payments"] == 1


def test_maintenance_series_expenses_and_categories(client, db_session):
    owner = _register(client, db_session, "owner", "an_maint_owner")
    prop = _make_property(db_session, owner, name="Fixer Upper")
    this_key, this_dt = _month_anchor(0)

    _make_maintenance(db_session, prop, category="Plumbing", status="in_progress",
                      cost="KSh 1,500", created_at=this_dt)
    _make_maintenance(db_session, prop, category="Plumbing", status="resolved",
                      cost="500", created_at=this_dt, resolved_at=this_dt + timedelta(days=1))
    _make_maintenance(db_session, prop, category="Electrical", status="resolved",
                      cost="2,000", created_at=this_dt, resolved_at=this_dt + timedelta(days=2))
    _make_maintenance(db_session, prop, category=None, status="pending",
                      cost=None, created_at=this_dt)

    resp = client.get(DASHBOARD, headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    data = resp.json()

    maint = {m["month"]: m for m in data["series"]["maintenance"]}
    assert maint[this_key]["requests"] == 4
    assert maint[this_key]["resolved"] == 2
    assert maint[this_key]["cost"] == 2500.0  # resolved costs only

    financial = {f["month"]: f for f in data["series"]["financial"]}
    assert financial[this_key]["expenses"] == 2500.0
    assert financial[this_key]["net"] == -2500.0

    categories = data["distributions"]["maintenance_by_category"]
    assert [c["category"] for c in categories] == ["Plumbing", "Electrical", "Uncategorised"]
    plumbing = categories[0]
    assert plumbing["requests"] == 2
    assert plumbing["open"] == 1
    assert plumbing["cost"] == 2000.0
    assert categories[1]["cost"] == 2000.0
    assert categories[2]["requests"] == 1
    assert categories[2]["open"] == 1

    assert data["kpis"]["open_maintenance"] == 2
    assert data["kpis"]["period_expenses"] == 2500.0


def test_kpi_snapshot_counts(client, db_session):
    owner = _register(client, db_session, "owner", "an_kpi_owner")
    tenant = _register(client, db_session, "tenant", "an_kpi_tenant")
    prop = _make_property(db_session, owner, name="KPI Court")
    u1 = _make_unit(db_session, prop, "1", status="occupied")
    u2 = _make_unit(db_session, prop, "2", status="occupied")
    u3 = _make_unit(db_session, prop, "3", status="available")
    u4 = _make_unit(db_session, prop, "4", status="available")

    now = utc_now()
    lease = _make_lease(db_session, prop, u1, tenant, end_date=now + timedelta(days=10))  # expiring
    _make_lease(db_session, prop, u2, tenant, end_date=now + timedelta(days=45))   # active, not expiring
    _make_lease(db_session, prop, u3, tenant, end_date=now - timedelta(days=5))    # past end
    _make_lease(db_session, prop, u4, tenant, status="pending", end_date=now + timedelta(days=5))

    _make_maintenance(db_session, prop, category="General", status="pending",
                      cost=None, created_at=now)
    _make_maintenance(db_session, prop, category="General", status="resolved",
                      cost="2,000", created_at=now, resolved_at=now)

    this_dt = _month_anchor(0)[1]
    _make_payment(
        db_session, prop, u1, tenant, lease,
        amount="10000", status="overdue", due_date=this_dt,
    )
    _make_payment(
        db_session, prop, u2, tenant, lease,
        amount="5000", status="paid", due_date=this_dt, payment_date=this_dt,
    )

    resp = client.get(DASHBOARD, headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    kpis = resp.json()["kpis"]

    assert kpis["properties"] == 1
    assert kpis["total_units"] == 4
    assert kpis["occupied_units"] == 2
    assert kpis["vacant_units"] == 2
    assert kpis["occupancy_rate"] == 50.0
    assert kpis["active_leases"] == 3
    assert kpis["leases_expiring_soon"] == 1
    assert kpis["open_maintenance"] == 1
    assert kpis["overdue_payments"] == 1
    assert kpis["period_expected"] == 15000.0
    assert kpis["period_collected"] == 5000.0
    assert kpis["period_collection_rate"] == 33.3
    assert kpis["period_expenses"] == 2000.0
    assert kpis["period_net"] == 3000.0


def test_city_distribution_top8_and_other_rollup(client, db_session):
    owner = _register(client, db_session, "owner", "an_city_owner")
    layout = [
        ("Nairobi", 2), ("Mombasa", 2),
        ("Kisumu", 1), ("Nakuru", 1), ("Eldoret", 1),
        ("Thika", 1), ("Malindi", 1), ("Nyeri", 1), ("Kericho", 1),
    ]
    idx = 0
    for city, count in layout:
        for _ in range(count):
            idx += 1
            _make_property(db_session, owner, name=f"Property {idx}", city=city)

    resp = client.get(DASHBOARD, headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    cities = resp.json()["distributions"]["properties_by_city"]
    assert [row["city"] for row in cities] == [
        "Mombasa", "Nairobi", "Eldoret", "Kericho", "Kisumu", "Malindi", "Nakuru", "Nyeri", "Other",
    ]
    assert cities[0]["count"] == 2
    assert cities[-1]["count"] == 1  # Thika rolled up
    assert sum(row["count"] for row in cities) == 11


def test_top_properties_ordering_and_cap(client, db_session):
    owner = _register(client, db_session, "owner", "an_top_owner")
    tenant = _register(client, db_session, "tenant", "an_top_tenant")
    this_dt = _month_anchor(0)[1]

    amounts = ["50000", "30000", "20000", "10000", "5000"]
    for index, amount in enumerate(amounts, start=1):
        prop = _make_property(db_session, owner, name=f"Prop {index:02d}" if index > 1 else "Prop One")
        unit = _make_unit(db_session, prop, "1", status="occupied" if index == 1 else "available")
        lease = _make_lease(db_session, prop, unit, tenant, status="active")
        _make_payment(
            db_session, prop, unit, tenant, lease,
            amount=amount, status="paid", due_date=this_dt, payment_date=this_dt,
        )

    # Sixth property has the largest outstanding amount but zero collected.
    prop6 = _make_property(db_session, owner, name="Prop Six")
    unit6 = _make_unit(db_session, prop6, "1", status="available")
    lease6 = _make_lease(db_session, prop6, unit6, tenant, status="active")
    _make_payment(db_session, prop6, unit6, tenant, lease6, amount="99999", status="overdue", due_date=this_dt)

    resp = client.get(DASHBOARD, headers=_login(client, owner.email))
    assert resp.status_code == 200, resp.text
    rows = resp.json()["top_properties"]

    assert len(rows) == 5
    assert [row["name"] for row in rows] == ["Prop One", "Prop 02", "Prop 03", "Prop 04", "Prop 05"]
    first = rows[0]
    assert first["units"] == 1
    assert first["occupied"] == 1
    assert first["occupancy_rate"] == 100.0
    assert first["collected"] == 50000.0
    assert first["city"] == "Nairobi"
    assert rows[-1]["collected"] == 5000.0
