"""
Payment gateway tests (#21).
Tests for the mock gateway charge flow, signed webhook ingestion,
and admin reconciliation — all against the in-process mock provider.
"""
import json
import uuid

import pytest

from app.config.settings import settings
from app.models.user import User
from app.services.payment_gateway_service import mock_gateway, sign_payload

PASSWORD = "Str0ng!TestPass42"
WEBHOOK_SECRET = "test-webhook-secret"


def _set_role(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()
    db_session.refresh(user)


def _register_and_login(client, db_session, tag, role):
    email = f"pgw_{tag}_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, email, role)
    resp = client.post('/api/auth/login', json={"email": email, "password": PASSWORD})
    access = resp.json().get('access_token')
    return {"Authorization": f"Bearer {access}"}, email


def _setup_payment(client, db_session, tag):
    """Create admin + tenant + property + unit + lease + pending payment."""
    admin_headers, admin_email = _register_and_login(client, db_session, f"{tag}_admin", "admin")
    tenant_headers, tenant_email = _register_and_login(client, db_session, f"{tag}_tenant", "tenant")

    resp = client.post('/api/properties/', json={
        "name": f"Gateway Property {tag}",
        "property_type": "apartment",
        "address": "1 Gateway St",
        "city": "Gatewayville",
        "country": "Testland",
        "units_count": 1,
    }, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    property_id = resp.json()['id']

    resp = client.post('/api/units/', json={
        "property_id": property_id,
        "unit_number": "G1",
        "unit_type": "studio",
        "bedrooms": 0,
        "bathrooms": 1,
        "area": "500 sqft",
        "rent": "1200",
        "status": "available",
    }, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    unit_id = resp.json()['id']

    from datetime import datetime, timedelta, timezone
    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    tenant_id = next(u['id'] for u in users if u['email'] == tenant_email)

    start = datetime.now(timezone.utc)
    resp = client.post('/api/leases/', json={
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "property_id": property_id,
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=365)).isoformat(),
        "rent_amount": "1200",
        "status": "active",
    }, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    lease_id = resp.json()['id']

    resp = client.post('/api/payments/', json={
        "tenant_id": tenant_id,
        "lease_id": lease_id,
        "property_id": property_id,
        "unit_id": unit_id,
        "amount": "1200",
        "due_date": (start + timedelta(days=30)).isoformat(),
        "payment_type": "rent",
        "status": "pending",
    }, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    return admin_headers, tenant_headers, resp.json()['id']


def _signed_webhook_headers(payload: dict, secret: str = WEBHOOK_SECRET) -> dict:
    raw = json.dumps(payload).encode()
    return {"Content-Type": "application/json", "X-Webhook-Signature": sign_payload(raw, secret)}


@pytest.fixture(autouse=True)
def _webhook_secret(monkeypatch):
    monkeypatch.setattr(settings, "PAYMENT_WEBHOOK_SECRET", WEBHOOK_SECRET)


def test_charge_creates_gateway_reference(client, db_session):
    admin_headers, _, payment_id = _setup_payment(client, db_session, "charge")

    resp = client.post(f'/api/payments/{payment_id}/gateway/charge', headers=admin_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data['provider'] == "mock"
    txn_id = data['provider_txn_id']

    resp = client.get(f'/api/payments/{payment_id}', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()['reference'] == txn_id
    assert resp.json()['payment_method'] == "mock"


def test_tenant_cannot_create_charge(client, db_session):
    _, tenant_headers, payment_id = _setup_payment(client, db_session, "chargeauth")

    resp = client.post(f'/api/payments/{payment_id}/gateway/charge', headers=tenant_headers)
    assert resp.status_code == 403


def test_charge_rejected_when_already_paid(client, db_session):
    admin_headers, _, payment_id = _setup_payment(client, db_session, "paidcharge")

    client.post(f'/api/payments/{payment_id}/gateway/charge', headers=admin_headers)
    resp = client.put(f'/api/payments/{payment_id}', json={"status": "paid"}, headers=admin_headers)
    assert resp.status_code == 200

    resp = client.post(f'/api/payments/{payment_id}/gateway/charge', headers=admin_headers)
    assert resp.status_code == 409


def test_webhook_marks_payment_paid_and_is_idempotent(client, db_session):
    admin_headers, _, payment_id = _setup_payment(client, db_session, "webhook")

    resp = client.post(f'/api/payments/{payment_id}/gateway/charge', headers=admin_headers)
    txn_id = resp.json()['provider_txn_id']

    payload = {"id": "evt_1", "type": "payment.succeeded", "data": {"provider_txn_id": txn_id}}
    resp = client.post('/api/payments/webhooks/mock', content=json.dumps(payload).encode(),
                       headers=_signed_webhook_headers(payload))
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"received": True, "matched": True, "applied": True}

    resp = client.get(f'/api/payments/{payment_id}', headers=admin_headers)
    assert resp.json()['status'] == "paid"
    assert resp.json()['payment_date'] is not None

    # Replaying the same event must not change anything.
    resp = client.post('/api/payments/webhooks/mock', content=json.dumps(payload).encode(),
                       headers=_signed_webhook_headers(payload))
    assert resp.status_code == 200
    assert resp.json()["applied"] is False


def test_webhook_rejects_bad_signature(client, db_session):
    admin_headers, _, payment_id = _setup_payment(client, db_session, "badsig")

    resp = client.post(f'/api/payments/{payment_id}/gateway/charge', headers=admin_headers)
    txn_id = resp.json()['provider_txn_id']

    payload = {"id": "evt_bad", "type": "payment.succeeded", "data": {"provider_txn_id": txn_id}}
    headers = _signed_webhook_headers(payload, secret="wrong-secret")
    resp = client.post('/api/payments/webhooks/mock', content=json.dumps(payload).encode(), headers=headers)
    assert resp.status_code == 400

    resp = client.get(f'/api/payments/{payment_id}', headers=admin_headers)
    assert resp.json()['status'] == "pending"


def test_webhook_unknown_transaction_is_ignored(client, db_session):
    payload = {"id": "evt_404", "type": "payment.succeeded", "data": {"provider_txn_id": "mock_does_not_exist"}}
    resp = client.post('/api/payments/webhooks/mock', content=json.dumps(payload).encode(),
                       headers=_signed_webhook_headers(payload))
    assert resp.status_code == 200
    assert resp.json() == {"received": True, "matched": False}


def test_webhook_failure_event_marks_payment_failed(client, db_session):
    admin_headers, _, payment_id = _setup_payment(client, db_session, "failed")

    resp = client.post(f'/api/payments/{payment_id}/gateway/charge', headers=admin_headers)
    txn_id = resp.json()['provider_txn_id']

    payload = {"id": "evt_fail", "type": "payment.failed", "data": {"provider_txn_id": txn_id}}
    resp = client.post('/api/payments/webhooks/mock', content=json.dumps(payload).encode(),
                       headers=_signed_webhook_headers(payload))
    assert resp.status_code == 200
    assert resp.json()["applied"] is True

    resp = client.get(f'/api/payments/{payment_id}', headers=admin_headers)
    assert resp.json()['status'] == "failed"


def test_reconciliation_syncs_stale_pending_payment(client, db_session):
    admin_headers, _, payment_id = _setup_payment(client, db_session, "recon")

    resp = client.post(f'/api/payments/{payment_id}/gateway/charge', headers=admin_headers)
    txn_id = resp.json()['provider_txn_id']
    mock_gateway.charges[txn_id] = "succeeded"

    # Simulate drift: the webhook was lost, so the local row is still pending.
    resp = client.put(f'/api/payments/{payment_id}', json={"status": "pending"}, headers=admin_headers)
    assert resp.status_code == 200

    resp = client.post('/api/admin/payments/reconcile', headers=admin_headers)
    assert resp.status_code == 200, resp.text
    counts = resp.json()
    assert counts["checked"] == 1
    assert counts["marked_paid"] == 1

    resp = client.get(f'/api/payments/{payment_id}', headers=admin_headers)
    assert resp.json()['status'] == "paid"


def test_reconciliation_requires_admin(client, db_session):
    _, tenant_headers, _ = _setup_payment(client, db_session, "reconauth")

    resp = client.post('/api/admin/payments/reconcile', headers=tenant_headers)
    assert resp.status_code == 403


def test_unconfigured_gateway_fails_closed(client, db_session, monkeypatch):
    from app.services.payment_gateway_service import PaymentGatewayError

    monkeypatch.setattr(settings, "PAYMENT_GATEWAY", "stripe")
    with pytest.raises(PaymentGatewayError):
        from app.services.payment_gateway_service import get_gateway
        get_gateway().create_charge(amount="10", currency="USD", reference="ref")
