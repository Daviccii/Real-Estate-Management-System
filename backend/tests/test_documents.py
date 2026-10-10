"""
Document generation tests: PDF builders, the on-disk cache (reuse per stamp,
regeneration + pruning), and authorization of the download endpoints
(lease agreement, payment invoice).
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.config.settings import settings
from app.models import User
from app.services.document_service import (
    cached_pdf,
    generate_invoice_pdf,
    generate_lease_pdf,
)

PASSWORD = "Str0ng!TestPass42"


@pytest.fixture()
def docs_dir(tmp_path, monkeypatch):
    target = tmp_path / "docs"
    monkeypatch.setattr(settings, "DOCUMENTS_DIR", str(target))
    return target


def _register(client, email, full_name="Doc Tester"):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _login(client, email):
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _set_role(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()
    db_session.refresh(user)


def _bootstrap(client, db_session):
    """Admin + tenant + property + unit + lease + payment. Returns tokens/ids."""
    suffix = uuid4().hex[:8]
    admin_email = f"doc_admin_{suffix}@docs.dev"
    tenant_email = f"doc_tenant_{suffix}@docs.dev"
    _register(client, admin_email, full_name="Doc Admin")
    tenant_id = _register(client, tenant_email, full_name="Doc Tenant")
    # Registrations start as role="user"; lease holders are promoted to
    # "tenant" by the platform (e.g. on application approval).
    _set_role(db_session, tenant_email, "tenant")
    _set_role(db_session, admin_email, "admin")
    admin_h = _login(client, admin_email)
    tenant_h = _login(client, tenant_email)

    resp = client.post(
        "/api/properties/",
        json={
            "name": "Doc Towers",
            "property_type": "apartment",
            "address": "1 Document Way",
            "city": "Nairobi",
            "country": "Kenya",
            "units_count": 1,
        },
        headers=admin_h,
    )
    assert resp.status_code in (200, 201), resp.text
    property_id = resp.json()["id"]

    resp = client.post(
        "/api/units/",
        json={
            "property_id": property_id,
            "unit_number": "101",
            "unit_type": "1 bedroom",
            "bedrooms": 1,
            "bathrooms": 1,
            "area": "750 sqft",
            "rent": "1500",
            "status": "available",
        },
        headers=admin_h,
    )
    assert resp.status_code in (200, 201), resp.text
    unit_id = resp.json()["id"]

    start = datetime.now(timezone.utc)
    resp = client.post(
        "/api/leases/",
        json={
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "property_id": property_id,
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=365)).isoformat(),
            "rent_amount": "1500",
            "deposit": "3000",
            "status": "active",
        },
        headers=admin_h,
    )
    assert resp.status_code == 201, resp.text
    lease_id = resp.json()["id"]

    resp = client.post(
        "/api/payments/",
        json={
            "tenant_id": tenant_id,
            "lease_id": lease_id,
            "property_id": property_id,
            "unit_id": unit_id,
            "amount": "1500",
            "due_date": (start + timedelta(days=30)).isoformat(),
            "payment_type": "RENT",
            "status": "pending",
        },
        headers=admin_h,
    )
    assert resp.status_code == 201, resp.text
    payment_id = resp.json()["id"]

    return SimpleNamespace(
        admin_h=admin_h,
        tenant_h=tenant_h,
        tenant_id=tenant_id,
        property_id=property_id,
        unit_id=unit_id,
        lease_id=lease_id,
        payment_id=payment_id,
    )


# ---------------------------------------------------------------------------
# PDF builders
# ---------------------------------------------------------------------------

def _sample_lease():
    return SimpleNamespace(
        id=3,
        status="active",
        start_date=datetime(2026, 1, 1, 9, 0, 0),
        end_date=datetime(2026, 12, 31, 9, 0, 0),
        rent_amount="1500",
        deposit="3000",
        payment_due_date=5,
        notes="Small pets allowed",
        tenant_id=2,
        unit_id=4,
        property_id=1,
    )


def _sample_payment():
    return SimpleNamespace(
        id=5,
        payment_type="RENT",
        status="paid",
        due_date=datetime(2026, 2, 5),
        payment_date=datetime(2026, 2, 4),
        payment_method="mpesa",
        reference="QGH7X2",
        amount="1500",
        notes=None,
        property_id=1,
        tenant_id=2,
    )


def test_lease_pdf_builds():
    pdf_bytes = generate_lease_pdf(
        _sample_lease(),
        SimpleNamespace(full_name="Ada Tenant"),
        SimpleNamespace(unit_number="101", unit_type="1 bedroom"),
        SimpleNamespace(name="Doc Towers", address="1 Main St", city="Nairobi"),
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_invoice_pdf_builds():
    pdf_bytes = generate_invoice_pdf(
        _sample_payment(),
        SimpleNamespace(full_name="Ada Tenant"),
        SimpleNamespace(name="Doc Towers"),
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_pdf_sanitizes_non_latin_text():
    pdf_bytes = generate_lease_pdf(
        SimpleNamespace(**{**_sample_lease().__dict__, "notes": "café ☕ ünïcode"}),
        SimpleNamespace(full_name="Ünal Öztürk"),
        SimpleNamespace(unit_number="A-1", unit_type=None),
        SimpleNamespace(name="Café Apartments", address=None, city=None),
    )
    assert pdf_bytes.startswith(b"%PDF")


# ---------------------------------------------------------------------------
# On-disk cache
# ---------------------------------------------------------------------------

def test_cached_pdf_reuses_file_for_same_stamp(docs_dir):
    calls = []

    def builder():
        calls.append(1)
        return b"%PDF-1.4 same"

    first = cached_pdf("lease", 7, datetime(2026, 1, 1, 12, 0, 0), builder)
    second = cached_pdf("lease", 7, datetime(2026, 1, 1, 12, 0, 0), builder)

    assert first == second
    assert first.read_bytes() == b"%PDF-1.4 same"
    assert len(calls) == 1


def test_cached_pdf_regenerates_and_prunes_on_new_stamp(docs_dir):
    old = cached_pdf("invoice", 9, datetime(2026, 1, 1), lambda: b"%PDF-old")
    new = cached_pdf("invoice", 9, datetime(2026, 1, 2), lambda: b"%PDF-new")

    assert old != new
    assert new.read_bytes() == b"%PDF-new"
    assert not old.exists()
    assert list(docs_dir.glob("invoice-9-*.pdf")) == [new]


# ---------------------------------------------------------------------------
# Download endpoints (auth + authz)
# ---------------------------------------------------------------------------

def test_document_endpoints_require_auth(client):
    assert client.get("/api/leases/1/document").status_code == 401
    assert client.get("/api/payments/1/invoice").status_code == 401


def test_tenant_downloads_own_lease_pdf(client, db_session, docs_dir):
    data = _bootstrap(client, db_session)
    resp = client.get(f"/api/leases/{data.lease_id}/document", headers=data.tenant_h)
    assert resp.status_code == 200, resp.text
    assert resp.content.startswith(b"%PDF")
    assert resp.headers["content-type"] == "application/pdf"
    assert (
        resp.headers["content-disposition"]
        == f'attachment; filename="lease-{data.lease_id}.pdf"'
    )


def test_other_tenant_cannot_download_lease_pdf(client, db_session, docs_dir):
    data = _bootstrap(client, db_session)
    other_email = f"doc_other_{uuid4().hex[:8]}@docs.dev"
    _register(client, other_email, full_name="Other Tenant")
    other_h = _login(client, other_email)

    resp = client.get(f"/api/leases/{data.lease_id}/document", headers=other_h)
    assert resp.status_code == 403


def test_admin_downloads_invoice_pdf(client, db_session, docs_dir):
    data = _bootstrap(client, db_session)
    resp = client.get(f"/api/payments/{data.payment_id}/invoice", headers=data.admin_h)
    assert resp.status_code == 200, resp.text
    assert resp.content.startswith(b"%PDF")
    assert resp.headers["content-type"] == "application/pdf"
    assert (
        resp.headers["content-disposition"]
        == f'attachment; filename="invoice-{data.payment_id}.pdf"'
    )


def test_other_tenant_cannot_download_invoice_pdf(client, db_session, docs_dir):
    data = _bootstrap(client, db_session)
    other_email = f"doc_other2_{uuid4().hex[:8]}@docs.dev"
    _register(client, other_email, full_name="Other Tenant 2")
    other_h = _login(client, other_email)

    resp = client.get(f"/api/payments/{data.payment_id}/invoice", headers=other_h)
    assert resp.status_code == 403


def test_missing_document_returns_404(client, db_session, docs_dir):
    data = _bootstrap(client, db_session)
    assert client.get("/api/leases/99999/document", headers=data.admin_h).status_code == 404
    assert client.get("/api/payments/99999/invoice", headers=data.admin_h).status_code == 404
