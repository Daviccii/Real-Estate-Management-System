"""
M-Pesa (Safaricom Daraja) integration tests.

All Safaricom HTTP calls are intercepted by FakeDaraja — no test ever touches
a real Daraja endpoint and no real payment is ever initiated. Covers phone
normalization, amount validation, configuration gating, OAuth caching and
refresh, STK request generation, rejection/timeout handling, callback
processing (success/failure/malformed/replay/mismatch), reconciliation,
authorization (including cross-tenant IDOR), duplicate prevention, ledger
crediting (partial + overpayment protection), receipts, rate limiting, and
secret non-exposure.
"""
import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest

from app.config.settings import settings
from app.models.audit_log import AuditLog
from app.models.mpesa_transaction import MpesaTransaction
from app.models.payment import Payment
from app.models.user import User
from app.services import mpesa_service
from app.utils.money import parse_amount
from app.utils.phone import mask_phone, normalize_kenyan_phone

PASSWORD = "Str0ng!TestPass42"
SHORTCODE = "174379"
PASSKEY = "test-passkey"
CALLBACK_URL = "https://example.test/api/v1/mpesa/callback"

STK_OK = {
    "MerchantRequestID": "mrq-0001-aaaa",
    "CheckoutRequestID": "ws_CO_0001",
    "ResponseCode": "0",
    "ResponseDescription": "Success. Request accepted for processing",
    "CustomerMessage": "Success. Request accepted for processing",
}


# ---------------------------------------------------------------------------
# Fake Daraja transport
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


class FakeDaraja:
    """Records every call; scripted per-endpoint responses."""

    def __init__(self):
        self.calls = []
        self.token_responses = []
        self.stk_responses = []
        self.query_responses = []
        self.token_requests = 0
        self.stk_requests = 0

    def __call__(self, method, url, *, headers=None, json_body=None, params=None, auth=None, timeout=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers or {},
                "json": json_body,
                "params": params,
                "auth": auth,
            }
        )
        if url.endswith("/oauth/v1/generate"):
            self.token_requests += 1
            if self.token_responses:
                return self._pop(self.token_responses)
            return FakeResponse(200, {"access_token": f"tok-{self.token_requests}", "expires_in": 3599})
        if url.endswith("/mpesa/stkpush/v1/processrequest"):
            self.stk_requests += 1
            if self.stk_responses:
                return self._pop(self.stk_responses)
            # Unique IDs per call: checkout_request_id is unique-constrained.
            return FakeResponse(
                200,
                {
                    "MerchantRequestID": f"mrq-{self.stk_requests:04d}-aaaa",
                    "CheckoutRequestID": f"ws_CO_{self.stk_requests:04d}",
                    "ResponseCode": "0",
                    "ResponseDescription": "Success. Request accepted for processing",
                    "CustomerMessage": "Success. Request accepted for processing",
                },
            )
        if url.endswith("/mpesa/stkpushquery/v1/query"):
            if self.query_responses:
                return self._pop(self.query_responses)
            raise AssertionError("unscripted query call")
        raise AssertionError(f"unexpected URL {url}")

    @staticmethod
    def _pop(queue):
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, FakeResponse):
            return item
        return FakeResponse(200, item)

    def stk_calls(self):
        return [c for c in self.calls if c["url"].endswith("/processrequest")]

    def query_calls(self):
        return [c for c in self.calls if c["url"].endswith("/query")]


@pytest.fixture(autouse=True)
def mpesa_env(monkeypatch):
    monkeypatch.setattr(settings, "MPESA_ENVIRONMENT", "sandbox")
    monkeypatch.setattr(settings, "MPESA_CONSUMER_KEY", "test-consumer-key")
    monkeypatch.setattr(settings, "MPESA_CONSUMER_SECRET", "test-consumer-secret")
    monkeypatch.setattr(settings, "MPESA_SHORTCODE", SHORTCODE)
    monkeypatch.setattr(settings, "MPESA_PASSKEY", PASSKEY)
    monkeypatch.setattr(settings, "MPESA_CALLBACK_URL", CALLBACK_URL)
    monkeypatch.setattr(settings, "MPESA_TRANSACTION_TYPE", "CustomerPayBillOnline")
    monkeypatch.setattr(settings, "MPESA_ACCOUNT_REFERENCE", "PropNoxa")
    monkeypatch.setattr(settings, "MPESA_TRANSACTION_DESCRIPTION", "Rent Payment")
    monkeypatch.setattr(settings, "MPESA_PRODUCTION_ENABLED", False)
    monkeypatch.setattr(settings, "MPESA_MAX_AMOUNT", 250000)
    monkeypatch.setattr(settings, "MPESA_INITIATE_LIMIT_PER_HOUR", 10)
    monkeypatch.setattr(settings, "MPESA_DUPLICATE_WINDOW_SECONDS", 300)
    monkeypatch.setattr(settings, "REDIS_URL", None)
    mpesa_service._clear_token_cache()
    mpesa_service._rate_state.clear()
    mpesa_service._rate_redis_client = None
    yield
    mpesa_service._clear_token_cache()
    mpesa_service._rate_state.clear()


@pytest.fixture()
def daraja(monkeypatch):
    fake = FakeDaraja()
    monkeypatch.setattr(mpesa_service, "_http_request", fake)
    return fake


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_role(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()
    db_session.refresh(user)
    return user.id


def _register_and_login(client, db_session, tag, role):
    email = f"mpesa_{tag}_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": f"Test {role.title()}"},
    )
    assert resp.status_code in (200, 201), resp.text
    user_id = _set_role(db_session, email, role)
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}, email, user_id


def _setup_payment(client, db_session, tag, amount="1200"):
    """admin + tenant + property + unit + active lease + pending rent obligation."""
    admin_headers, _, _ = _register_and_login(client, db_session, f"{tag}_admin", "admin")
    tenant_headers, tenant_email, tenant_id = _register_and_login(client, db_session, f"{tag}_tenant", "tenant")

    resp = client.post(
        "/api/v1/properties/",
        json={
            "name": f"Mpesa Property {tag}",
            "property_type": "apartment",
            "address": "1 Mpesa St",
            "city": "Nairobi",
            "country": "Kenya",
            "units_count": 1,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    property_id = resp.json()["id"]

    resp = client.post(
        "/api/v1/units/",
        json={
            "property_id": property_id,
            "unit_number": "M1",
            "unit_type": "studio",
            "bedrooms": 0,
            "bathrooms": 1,
            "area": "500 sqft",
            "rent": amount,
            "status": "available",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    unit_id = resp.json()["id"]

    start = datetime.now(timezone.utc)
    resp = client.post(
        "/api/v1/leases/",
        json={
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "property_id": property_id,
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=365)).isoformat(),
            "rent_amount": amount,
            "status": "active",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    lease_id = resp.json()["id"]

    resp = client.post(
        "/api/v1/payments/",
        json={
            "tenant_id": tenant_id,
            "lease_id": lease_id,
            "property_id": property_id,
            "unit_id": unit_id,
            "amount": amount,
            "due_date": (start + timedelta(days=30)).isoformat(),
            "payment_type": "rent",
            "status": "pending",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    return {
        "admin_headers": admin_headers,
        "tenant_headers": tenant_headers,
        "tenant_id": tenant_id,
        "tenant_email": tenant_email,
        "property_id": property_id,
        "payment_id": resp.json()["id"],
    }


def _initiate(client, headers, payment_id, phone="0712345678", amount="1200"):
    return client.post(
        "/api/v1/mpesa/stk-push",
        json={"payment_id": payment_id, "phone_number": phone, "amount": amount},
        headers=headers,
    )


def _callback(checkout_id, *, code=0, desc="Processed", amount=None, receipt=None, phone=254712345678, include_metadata=True):
    stk = {
        "MerchantRequestID": "mrq-0001-aaaa",
        "CheckoutRequestID": checkout_id,
        "ResultCode": code,
        "ResultDesc": desc,
    }
    if include_metadata and (code == 0 or amount is not None):
        items = [{"Name": "TransactionDate", "Value": 20261011103000}, {"Name": "PhoneNumber", "Value": phone}]
        if amount is not None:
            items.append({"Name": "Amount", "Value": amount})
        if receipt is not None:
            items.append({"Name": "MpesaReceiptNumber", "Value": receipt})
        stk["CallbackMetadata"] = {"Item": items}
    return {"Body": {"stkCallback": stk}}


def _post_callback(client, payload):
    return client.post("/api/v1/mpesa/callback", json=payload)


def _txn(db_session, txn_id):
    db_session.expire_all()
    return db_session.query(MpesaTransaction).filter(MpesaTransaction.id == txn_id).first()


def _payment(db_session, payment_id):
    db_session.expire_all()
    return db_session.query(Payment).filter(Payment.id == payment_id).first()


def _audit_actions(db_session):
    db_session.expire_all()
    return [row.action for row in db_session.query(AuditLog).all()]


# ---------------------------------------------------------------------------
# Phone normalization
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0712345678", "254712345678"),
        ("0112345678", "254112345678"),
        ("254712345678", "254712345678"),
        ("254112345678", "254112345678"),
        ("+254712345678", "254712345678"),
        ("+254 712 345 678", "254712345678"),
        ("0712-345-678", "254712345678"),
        ("0712 345 678", "254712345678"),
        ("(0712) 345678", "254712345678"),
        ("712345678", "254712345678"),
        ("112345678", "254112345678"),
        ("00254712345678", "254712345678"),
    ],
)
def test_phone_normalization_accepts_kenyan_formats(raw, expected):
    assert normalize_kenyan_phone(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["0812345678", "254812345678", "12345", "07123456789", "abc", "", None, "+254812345678"],
)
def test_phone_normalization_rejects_invalid(raw):
    with pytest.raises(ValueError):
        normalize_kenyan_phone(raw)


def test_phone_masking():
    assert mask_phone("254712345678") == "2547****678"
    assert mask_phone("123") == "***"


# ---------------------------------------------------------------------------
# Money parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1200", Decimal("1200.00")),
        ("1,200", Decimal("1200.00")),
        ("KSh 45,000/Month", Decimal("45000.00")),
        ("1200.50", Decimal("1200.50")),
        (1200, Decimal("1200.00")),
        ("abc", None),
        ("", None),
        (None, None),
        ("12.3.4", None),
    ],
)
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == expected


# ---------------------------------------------------------------------------
# Configuration gating
# ---------------------------------------------------------------------------

def test_config_endpoint_reports_unconfigured_without_secrets(client, monkeypatch):
    monkeypatch.setattr(settings, "MPESA_CONSUMER_KEY", None)
    monkeypatch.setattr(settings, "MPESA_PASSKEY", None)
    email = f"mpesa_cfg_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp = client.get("/api/v1/mpesa/config", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert "MPESA_CONSUMER_KEY" in data["missing"]
    assert "MPESA_PASSKEY" in data["missing"]
    body = json.dumps(data)
    assert "test-consumer-secret" not in body and "test-passkey" not in body


def test_stk_push_unconfigured_returns_503(client, db_session, monkeypatch):
    ctx = _setup_payment(client, db_session, "unconf")
    monkeypatch.setattr(settings, "MPESA_CONSUMER_KEY", None)

    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 503
    assert "MPESA_CONSUMER_KEY" in resp.json()["detail"]


def test_production_environment_blocked_until_enabled(client, db_session, monkeypatch):
    ctx = _setup_payment(client, db_session, "prodblock")
    monkeypatch.setattr(settings, "MPESA_ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "MPESA_PRODUCTION_ENABLED", False)

    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 503
    assert "MPESA_PRODUCTION_ENABLED" in resp.json()["detail"]

    # Production requires an https callback even when enabled.
    monkeypatch.setattr(settings, "MPESA_PRODUCTION_ENABLED", True)
    monkeypatch.setattr(settings, "MPESA_CALLBACK_URL", "http://insecure.test/cb")
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 503
    assert "https" in resp.json()["detail"]


def test_production_selects_live_base_url(client, db_session, monkeypatch, daraja):
    ctx = _setup_payment(client, db_session, "produrl")
    monkeypatch.setattr(settings, "MPESA_ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "MPESA_PRODUCTION_ENABLED", True)

    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 200, resp.text
    assert daraja.stk_calls()[0]["url"].startswith("https://api.safaricom.co.ke")


def test_health_metrics_includes_mpesa_block(client, monkeypatch):
    monkeypatch.setattr(settings, "MPESA_CONSUMER_KEY", None)
    resp = client.get("/health/metrics")
    assert resp.status_code == 200
    block = resp.json()["mpesa"]
    assert block["configured"] is False
    assert block["environment"] == "sandbox"
    assert "MPESA_CONSUMER_KEY" in block["missing"]
    assert "test-consumer-secret" not in json.dumps(resp.json())


def test_unconfigured_mpesa_does_not_break_other_features(client, monkeypatch):
    monkeypatch.setattr(settings, "MPESA_CONSUMER_KEY", None)
    monkeypatch.setattr(settings, "MPESA_SHORTCODE", None)
    assert client.get("/health/ready").status_code == 200

    # Registration, login, and authenticated unrelated endpoints still work.
    email = f"mpesa_unconf_{uuid.uuid4().hex[:8]}@example.com"
    assert client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD}).status_code in (200, 201)
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    assert client.get("/api/v1/properties/", headers=headers).status_code == 200
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200


# ---------------------------------------------------------------------------
# OAuth token handling
# ---------------------------------------------------------------------------

def test_token_is_cached_across_requests(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "tokcache", amount="2400")
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="500").status_code == 200
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="700").status_code == 409  # duplicate window
    db_session.expire_all()
    txn = db_session.query(MpesaTransaction).first()
    txn.initiated_at = txn.initiated_at - timedelta(seconds=600)
    txn.status = "timed_out"
    txn.completed_at = txn.initiated_at
    db_session.commit()
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="700").status_code == 200
    assert daraja.token_requests == 1  # both pushes shared one cached token


def test_token_refreshes_after_expiry(client, db_session, daraja, monkeypatch):
    ctx = _setup_payment(client, db_session, "tokexp", amount="3000")
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="500").status_code == 200
    # Force expiry, age out the first attempt, try again -> a second OAuth call.
    mpesa_service._token_cache["expires_at"] = 0
    db_session.expire_all()
    txn = db_session.query(MpesaTransaction).first()
    txn.status = "timed_out"
    txn.initiated_at = txn.initiated_at - timedelta(seconds=600)
    db_session.commit()
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="500").status_code == 200
    assert daraja.token_requests == 2


def test_oauth_failure_fails_closed(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "tokfail")
    daraja.token_responses.append(FakeResponse(401, {"error": "bad_credentials"}))

    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 502
    assert "OAuth" in resp.json()["detail"]["message"]
    assert daraja.stk_calls() == []  # never attempted the push
    txn = db_session.query(MpesaTransaction).first()
    assert txn.status == "failed"
    assert "OAuth" in txn.failure_reason


def test_stk_401_refreshes_token_and_retries_once(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "stk401")
    daraja.stk_responses.append(FakeResponse(401, {"errorCode": "401"}))
    daraja.stk_responses.append({"MerchantRequestID": "mrq", "CheckoutRequestID": "ws_CO_401", "ResponseCode": "0"})

    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 200
    assert len(daraja.stk_calls()) == 2
    assert daraja.token_requests == 2  # initial + forced refresh


# ---------------------------------------------------------------------------
# STK request generation
# ---------------------------------------------------------------------------

def test_stk_request_payload_generation(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "payload")
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], phone="0712 345 678", amount="1200")
    assert resp.status_code == 200, resp.text

    call = daraja.stk_calls()[0]
    body = call["json"]
    assert call["url"] == "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    assert call["headers"]["Authorization"].startswith("Bearer tok-")
    assert body["BusinessShortCode"] == SHORTCODE
    assert body["TransactionType"] == "CustomerPayBillOnline"
    assert body["Amount"] == 1200 and isinstance(body["Amount"], int)
    assert body["PartyA"] == "254712345678"
    assert body["PhoneNumber"] == "254712345678"
    assert body["PartyB"] == SHORTCODE
    assert body["CallBackURL"] == CALLBACK_URL
    assert body["AccountReference"] == "PropNoxa"
    assert body["TransactionDesc"] == "Rent Payment"
    expected_password = base64.b64encode(f"{SHORTCODE}{PASSKEY}{body['Timestamp']}".encode()).decode()
    assert body["Password"] == expected_password
    assert len(body["Timestamp"]) == 14  # YYYYMMDDHHMMSS


def test_account_reference_truncated_to_daraja_limit(client, db_session, daraja, monkeypatch):
    monkeypatch.setattr(settings, "MPESA_ACCOUNT_REFERENCE", "AnExtremelyLongReference")
    ctx = _setup_payment(client, db_session, "accref")
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"]).status_code == 200
    assert daraja.stk_calls()[0]["json"]["AccountReference"] == "AnExtremelyL"  # 12 chars


def test_stk_timestamp_uses_nairobi_time():
    when = datetime(2026, 10, 11, 7, 30, 15, tzinfo=timezone.utc)
    assert mpesa_service.stk_timestamp(when) == "20261011103015"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_phone", ["0812345678", "12345", "call-me"])
def test_stk_push_invalid_phone_rejected(client, db_session, bad_phone):
    ctx = _setup_payment(client, db_session, f"badphone{bad_phone[-1]}")
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], phone=bad_phone)
    assert resp.status_code == 422


@pytest.mark.parametrize("bad_amount", ["0", "-5", "1200.50", "not-money"])
def test_stk_push_invalid_amount_rejected(client, db_session, bad_amount):
    tag = f"badamt{uuid.uuid4().hex[:6]}"
    ctx = _setup_payment(client, db_session, tag)
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount=bad_amount)
    assert resp.status_code == 422


def test_stk_push_amount_above_outstanding_rejected(client, db_session):
    ctx = _setup_payment(client, db_session, "over")
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="50000")
    assert resp.status_code == 422
    assert "exceeds the outstanding balance" in resp.json()["detail"]


def test_stk_push_amount_above_max_rejected(client, db_session, monkeypatch):
    ctx = _setup_payment(client, db_session, "maxamt", amount="300000")
    monkeypatch.setattr(settings, "MPESA_MAX_AMOUNT", 250000)
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="260000")
    assert resp.status_code == 422


def test_stk_push_paid_obligation_rejected(client, db_session):
    ctx = _setup_payment(client, db_session, "paid")
    resp = client.put(
        f"/api/v1/payments/{ctx['payment_id']}", json={"status": "paid"}, headers=ctx["admin_headers"]
    )
    assert resp.status_code == 200
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 409
    assert "already fully paid" in resp.json()["detail"]


def test_stk_push_unknown_payment_404(client, db_session):
    _, _, _ = _register_and_login(client, db_session, "unk", "tenant")
    email = f"mpesa_unk2_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp = _initiate(client, headers, 999999)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Authorization / IDOR
# ---------------------------------------------------------------------------

def test_anonymous_cannot_initiate_or_read(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "anon")
    assert client.post(
        "/api/v1/mpesa/stk-push",
        json={"payment_id": ctx["payment_id"], "phone_number": "0712345678", "amount": "100"},
    ).status_code == 401
    assert client.get("/api/v1/mpesa/transactions").status_code == 401
    assert client.get("/api/v1/mpesa/config").status_code == 401


def test_cross_tenant_cannot_pay_or_view(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "idor")
    other_headers, _, _ = _register_and_login(client, db_session, "idor_b", "tenant")

    # Tenant B cannot initiate against tenant A's obligation.
    resp = _initiate(client, other_headers, ctx["payment_id"])
    assert resp.status_code == 403

    # Tenant A initiates; tenant B cannot read the transaction or list it.
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 200
    txn_id = resp.json()["id"]

    assert client.get(f"/api/v1/mpesa/transactions/{txn_id}", headers=other_headers).status_code == 403
    listing = client.get("/api/v1/mpesa/transactions", headers=other_headers)
    assert listing.status_code == 200
    assert listing.json() == []
    assert client.post(f"/api/v1/mpesa/transactions/{txn_id}/reconcile", headers=other_headers).status_code == 403


def test_admin_and_managing_landlord_can_view(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "mgview")
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    txn_id = resp.json()["id"]

    assert client.get(f"/api/v1/mpesa/transactions/{txn_id}", headers=ctx["admin_headers"]).status_code == 200

    manager_headers, _, manager_id = _register_and_login(client, db_session, "mgview_mgr", "manager")
    assert client.get(f"/api/v1/mpesa/transactions/{txn_id}", headers=manager_headers).status_code == 403
    db_session.expire_all()
    from app.models.property import Property

    prop = db_session.query(Property).filter(Property.id == ctx["property_id"]).first()
    prop.manager_id = manager_id
    db_session.commit()
    assert client.get(f"/api/v1/mpesa/transactions/{txn_id}", headers=manager_headers).status_code == 200
    listed = client.get("/api/v1/mpesa/transactions", headers=manager_headers)
    assert len(listed.json()) == 1


def test_tenant_list_is_scoped_to_own_transactions(client, db_session, daraja):
    ctx_a = _setup_payment(client, db_session, "scope_a")
    ctx_b = _setup_payment(client, db_session, "scope_b")
    assert _initiate(client, ctx_a["tenant_headers"], ctx_a["payment_id"]).status_code == 200

    # Tenant B's listing must not contain A's transaction even with tenant_id=A.
    resp = client.get(f"/api/v1/mpesa/transactions?tenant_id={ctx_a['tenant_id']}", headers=ctx_b["tenant_headers"])
    assert resp.status_code == 200
    assert resp.json() == []


def test_tenant_cannot_initiate_for_other_payment_via_param(client, db_session, daraja):
    ctx_a = _setup_payment(client, db_session, "param_a")
    ctx_b = _setup_payment(client, db_session, "param_b")
    resp = _initiate(client, ctx_b["tenant_headers"], ctx_a["payment_id"], phone="0712345678")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Duplicate prevention
# ---------------------------------------------------------------------------

def test_duplicate_initiation_blocked_while_live(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "dup")
    first = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert first.status_code == 200

    second = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail["transaction"]["id"] == first.json()["id"]
    assert len(daraja.stk_calls()) == 1  # only one prompt was ever sent


def test_new_attempt_allowed_after_window(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "dupwin")
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"]).status_code == 200
    db_session.expire_all()
    txn = db_session.query(MpesaTransaction).first()
    # Still live, but initiated longer ago than the duplicate window.
    assert txn.status == "awaiting_callback"
    txn.initiated_at = txn.initiated_at - timedelta(seconds=600)
    db_session.commit()
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"]).status_code == 200


def test_rate_limit_blocks_excessive_initiation(client, db_session, daraja, monkeypatch):
    monkeypatch.setattr(settings, "MPESA_INITIATE_LIMIT_PER_HOUR", 2)
    monkeypatch.setattr(settings, "MPESA_DUPLICATE_WINDOW_SECONDS", 0)
    ctx = _setup_payment(client, db_session, "rate", amount="100000")
    for amount in ("100", "200"):
        assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount=amount).status_code == 200
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="300")
    assert resp.status_code == 429


# ---------------------------------------------------------------------------
# Safaricom rejection / network failures
# ---------------------------------------------------------------------------

def test_safaricom_rejection_records_failed(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "reject")
    daraja.stk_responses.append(
        FakeResponse(200, {"ResponseCode": "1", "ResponseDescription": "Invalid request"})
    )
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 502
    txn = db_session.query(MpesaTransaction).first()
    assert txn.status == "failed"
    assert "Invalid request" in txn.failure_reason
    assert txn.completed_at is not None
    assert "MPESA_STK_PUSH_REJECTED" in _audit_actions(db_session)


def test_http_400_without_checkout_id_is_failure(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "http400")
    daraja.stk_responses.append(FakeResponse(400, {"errorMessage": "Bad Request - Invalid PhoneNumber"}))
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 502
    assert db_session.query(MpesaTransaction).first().status == "failed"


def test_read_timeout_becomes_unknown_without_retry(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "timeout")
    daraja.stk_responses.append(httpx.ReadTimeout("timed out"))
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 502
    assert "Do not resend" in resp.json()["detail"]["message"]
    assert len(daraja.stk_calls()) == 1  # no blind retry
    txn = db_session.query(MpesaTransaction).first()
    assert txn.status == "unknown"  # not failed: outcome indeterminate
    assert "MPESA_STK_PUSH_UNCONFIRMED" in _audit_actions(db_session)


def test_connect_error_becomes_definite_failure(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "connfail")
    daraja.stk_responses.append(httpx.ConnectError("refused"))
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 502
    txn = db_session.query(MpesaTransaction).first()
    assert txn.status == "failed"  # never reached Safaricom


def test_safaricom_5xx_is_ambiguous(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "stk5xx")
    daraja.stk_responses.append(FakeResponse(503, {"detail": "down"}))
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"])
    assert resp.status_code == 502
    assert db_session.query(MpesaTransaction).first().status == "unknown"
    assert len(daraja.stk_calls()) == 1


# ---------------------------------------------------------------------------
# Callback processing
# ---------------------------------------------------------------------------

def _initiate_and_get_ids(client, db_session, ctx, phone="0712345678", amount="1200"):
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], phone=phone, amount=amount)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    return body["id"], body["checkout_request_id"]


def test_callback_success_credits_ledger_exactly_once(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "cbsuccess")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)

    resp = _post_callback(client, _callback(checkout_id, amount=1200, receipt="SJK3X1ABC"))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["matched"] is True and body["applied"] is True and body["status"] == "succeeded"

    txn = _txn(db_session, txn_id)
    assert txn.status == "succeeded"
    assert txn.mpesa_receipt_number == "SJK3X1ABC"
    assert txn.applied_to_payment is True

    payment = _payment(db_session, ctx["payment_id"])
    assert payment.status == "paid"
    assert payment.payment_date is not None
    assert payment.payment_method == "mpesa"
    assert "MPESA_PAYMENT_SUCCEEDED" in _audit_actions(db_session)


def test_callback_replay_does_not_double_credit(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "cbreplay")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)
    payload = _callback(checkout_id, amount=1200, receipt="SJK3X1ABC")

    assert _post_callback(client, payload).json()["applied"] is True
    first_date = _payment(db_session, ctx["payment_id"]).payment_date

    second = _post_callback(client, payload)
    assert second.status_code == 200
    assert second.json()["applied"] is False
    txn = _txn(db_session, txn_id)
    assert txn.callback_attempts == 2  # replay counted for audit
    assert _payment(db_session, ctx["payment_id"]).payment_date == first_date  # untouched


@pytest.mark.parametrize(
    "code,expected",
    [(1032, "cancelled"), (1037, "timed_out"), (1019, "expired"), (1, "failed"), (2001, "failed"), (1001, "failed")],
)
def test_callback_failure_codes_map_to_statuses(client, db_session, daraja, code, expected):
    ctx = _setup_payment(client, db_session, f"cbfail{code}")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)

    resp = _post_callback(client, _callback(checkout_id, code=code, desc="Failure"))
    assert resp.status_code == 200
    assert resp.json()["status"] == expected
    txn = _txn(db_session, txn_id)
    assert txn.status == expected
    assert txn.applied_to_payment is False
    assert _payment(db_session, ctx["payment_id"]).status == "pending"


def test_callback_unknown_checkout_is_acknowledged_but_unmatched(client, db_session, daraja):
    resp = _post_callback(client, _callback("ws_CO_does_not_exist", amount=100, receipt="R1"))
    assert resp.status_code == 200
    assert resp.json()["matched"] is False
    assert "MPESA_CALLBACK_UNMATCHED" in _audit_actions(db_session)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"Body": {}},
        {"Body": {"stkCallback": {}}},
        {"Body": {"stkCallback": {"CheckoutRequestID": "x"}}},
        {"wrong": "shape"},
    ],
)
def test_malformed_callback_rejected(client, payload):
    resp = _post_callback(client, payload)
    assert resp.status_code == 400


def test_callback_amount_mismatch_held_for_review(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "cbmismatch")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)

    resp = _post_callback(client, _callback(checkout_id, amount=999, receipt="SJKMISMATCH"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "unknown"
    assert resp.json()["applied"] is False

    txn = _txn(db_session, txn_id)
    assert txn.status == "unknown"
    assert txn.mpesa_receipt_number == "SJKMISMATCH"  # receipt preserved for refund handling
    assert txn.applied_to_payment is False
    assert _payment(db_session, ctx["payment_id"]).status == "pending"  # ledger untouched
    assert "MPESA_PAYMENT_HELD_FOR_REVIEW" in _audit_actions(db_session)


def test_callback_success_without_receipt_metadata_not_credited(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "cbmsing")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)

    resp = _post_callback(client, _callback(checkout_id, amount=1200, receipt=None))
    assert resp.status_code == 200
    assert resp.json()["status"] == "unknown"
    assert _payment(db_session, ctx["payment_id"]).status == "pending"


def test_late_callback_recovers_timed_out_transaction(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "cblate")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)

    # Network timeout made the transaction 'unknown'; the callback then arrives.
    db_session.expire_all()
    txn = _txn(db_session, txn_id)
    txn.status = "unknown"
    db_session.commit()

    resp = _post_callback(client, _callback(checkout_id, amount=1200, receipt="SJKLATE01"))
    assert resp.status_code == 200
    assert resp.json()["applied"] is True
    assert _payment(db_session, ctx["payment_id"]).status == "paid"


def test_callback_response_does_not_leak_tenant_data(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "cbleak")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)
    resp = _post_callback(client, _callback(checkout_id, amount=1200, receipt="SJK1"))
    body = resp.json()
    assert set(body.keys()) == {"ResultCode", "ResultDesc", "matched", "applied", "enriched", "status"}
    assert ctx["tenant_email"] not in json.dumps(body)


# ---------------------------------------------------------------------------
# Partial payments + overpayment protection
# ---------------------------------------------------------------------------

def test_partial_then_full_payment_flow(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "partial", amount="1200")

    r1 = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="500")
    assert r1.status_code == 200
    checkout1 = "ws_CO_0001"
    assert _post_callback(client, _callback(checkout1, amount=500, receipt="SJKP1")).json()["applied"] is True
    assert _payment(db_session, ctx["payment_id"]).status == "partially_paid"

    # Remaining balance is 700 and the amount validation reflects it.
    resp = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="800")
    assert resp.status_code == 422

    db_session.expire_all()
    txn = db_session.query(MpesaTransaction).filter(MpesaTransaction.status == "succeeded").first()
    txn.initiated_at = txn.initiated_at - timedelta(seconds=600)
    db_session.commit()

    r2 = _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="700")
    assert r2.status_code == 200
    checkout2 = r2.json()["checkout_request_id"]
    assert _post_callback(client, _callback(checkout2, amount=700, receipt="SJKP2")).json()["applied"] is True
    assert _payment(db_session, ctx["payment_id"]).status == "paid"

    # Fully settled: no further initiation.
    assert _initiate(client, ctx["tenant_headers"], ctx["payment_id"], amount="100").status_code == 409


def test_second_success_after_settlement_flagged_not_double_counted(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "overpay", amount="1200")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)
    assert _post_callback(client, _callback(checkout_id, amount=1200, receipt="SJKOK1")).json()["applied"] is True
    payment_date = _payment(db_session, ctx["payment_id"]).payment_date

    # Simulate an old second attempt whose success arrives late.
    db_session.expire_all()
    old = MpesaTransaction(
        reference="MPX-OLDCB01",
        payment_id=ctx["payment_id"],
        tenant_id=ctx["tenant_id"],
        lease_id=_payment(db_session, ctx["payment_id"]).lease_id,
        property_id=ctx["property_id"],
        unit_id=_payment(db_session, ctx["payment_id"]).unit_id,
        amount=Decimal("1200.00"),
        currency="KES",
        channel="mpesa_stk",
        phone_number="254712345678",
        status="awaiting_callback",
        checkout_request_id="ws_CO_old_second",
    )
    db_session.add(old)
    db_session.commit()

    resp = _post_callback(client, _callback("ws_CO_old_second", amount=1200, receipt="SJKDUP02"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "succeeded"
    assert resp.json()["applied"] is False  # real receipt kept, ledger not double-counted

    old = _txn(db_session, old.id)
    assert old.mpesa_receipt_number == "SJKDUP02"
    assert old.applied_to_payment is False
    assert _payment(db_session, ctx["payment_id"]).payment_date == payment_date


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

def _make_stale(db_session, txn_id, status="awaiting_callback"):
    db_session.expire_all()
    txn = _txn(db_session, txn_id)
    txn.status = status
    txn.initiated_at = txn.initiated_at - timedelta(minutes=10)
    db_session.commit()


def test_reconcile_still_processing_keeps_state(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "recstill")
    txn_id, _ = _initiate_and_get_ids(client, db_session, ctx)
    _make_stale(db_session, txn_id)

    daraja.query_responses.append(
        FakeResponse(500, {"errorCode": "500.001.1001", "errorMessage": "The transaction is being processed"})
    )
    resp = client.post(f"/api/v1/mpesa/transactions/{txn_id}/reconcile", headers=ctx["tenant_headers"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "awaiting_callback"
    assert resp.json()["reconciled_at"] is not None


def test_reconcile_success_credits_without_receipt_then_callback_enriches(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "recsuc")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)
    _make_stale(db_session, txn_id)

    daraja.query_responses.append(
        {"ResponseCode": "0", "ResultCode": "0", "ResultDesc": "The service request is processed successfully."}
    )
    resp = client.post(f"/api/v1/mpesa/transactions/{txn_id}/reconcile", headers=ctx["tenant_headers"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "succeeded"
    assert _payment(db_session, ctx["payment_id"]).status == "paid"

    # The late callback then enriches the receipt without re-applying.
    resp = _post_callback(client, _callback(checkout_id, amount=1200, receipt="SJKLATER1"))
    assert resp.json()["applied"] is False
    assert resp.json()["enriched"] is True
    assert _txn(db_session, txn_id).mpesa_receipt_number == "SJKLATER1"


def test_reconcile_failure_code_marks_failed(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "recfail")
    txn_id, _ = _initiate_and_get_ids(client, db_session, ctx)
    _make_stale(db_session, txn_id)

    daraja.query_responses.append({"ResponseCode": "0", "ResultCode": "1032", "ResultDesc": "Request cancelled by user"})
    resp = client.post(f"/api/v1/mpesa/transactions/{txn_id}/reconcile", headers=ctx["tenant_headers"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_reconcile_repairs_unapplied_success(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "recpair")
    txn_id, _ = _initiate_and_get_ids(client, db_session, ctx)
    # Simulate the crash window: success recorded but never credited.
    db_session.expire_all()
    txn = _txn(db_session, txn_id)
    txn.status = "succeeded"
    txn.applied_to_payment = False
    db_session.commit()

    resp = client.post(f"/api/v1/mpesa/transactions/{txn_id}/reconcile", headers=ctx["tenant_headers"])
    assert resp.status_code == 200
    assert _payment(db_session, ctx["payment_id"]).status == "paid"
    assert _txn(db_session, txn_id).applied_to_payment is True
    assert "MPESA_PAYMENT_LEDGER_REPAIRED" in _audit_actions(db_session)


def test_reconcile_without_checkout_id_fails_clearly(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "recnochk")
    txn_id, _ = _initiate_and_get_ids(client, db_session, ctx)
    db_session.expire_all()
    txn = _txn(db_session, txn_id)
    txn.checkout_request_id = None
    txn.status = "unknown"
    txn.initiated_at = txn.initiated_at - timedelta(minutes=10)
    db_session.commit()

    resp = client.post(f"/api/v1/mpesa/transactions/{txn_id}/reconcile", headers=ctx["tenant_headers"])
    assert resp.status_code == 502


def test_bulk_reconcile_admin_only(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "bulk")
    txn_id, _ = _initiate_and_get_ids(client, db_session, ctx)
    _make_stale(db_session, txn_id)

    assert client.post("/api/v1/mpesa/reconcile", headers=ctx["tenant_headers"]).status_code == 403

    daraja.query_responses.append({"ResponseCode": "0", "ResultCode": "0", "ResultDesc": "ok"})
    resp = client.post("/api/v1/mpesa/reconcile", headers=ctx["admin_headers"])
    assert resp.status_code == 200
    counts = resp.json()
    assert counts["checked"] == 1
    assert counts["updated"] == 1


def test_bulk_reconcile_skips_fresh_transactions(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "bulkfresh")
    _initiate_and_get_ids(client, db_session, ctx)
    resp = client.post("/api/v1/mpesa/reconcile", headers=ctx["admin_headers"])
    assert resp.status_code == 200
    assert resp.json()["checked"] == 0  # too new to reconcile


# ---------------------------------------------------------------------------
# Receipts / serialization / privacy
# ---------------------------------------------------------------------------

def test_transaction_serialization_masks_phone_and_formats_amount(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "serial")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)
    _post_callback(client, _callback(checkout_id, amount=1200, receipt="SJKRCPT1"))

    resp = client.get(f"/api/v1/mpesa/transactions/{txn_id}", headers=ctx["tenant_headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone_number"] == "2547****678"
    assert data["amount"] == "1200.00"
    assert data["mpesa_receipt_number"] == "SJKRCPT1"
    assert data["status"] == "succeeded"
    assert data["property_name"]
    assert data["tenant_name"]

    # No secret material anywhere in the payload.
    body = json.dumps(data)
    for secret in ("test-consumer-secret", "test-passkey", PASSKEY):
        assert secret not in body


def test_transaction_list_filters(client, db_session, daraja):
    ctx = _setup_payment(client, db_session, "filt")
    txn_id, checkout_id = _initiate_and_get_ids(client, db_session, ctx)
    _post_callback(client, _callback(checkout_id, amount=1200, receipt="SJKF1"))

    ok = client.get("/api/v1/mpesa/transactions?status=succeeded", headers=ctx["tenant_headers"])
    assert ok.status_code == 200 and len(ok.json()) == 1
    empty = client.get("/api/v1/mpesa/transactions?status=failed", headers=ctx["tenant_headers"])
    assert empty.status_code == 200 and empty.json() == []
    by_payment = client.get(
        f"/api/v1/mpesa/transactions?payment_id={ctx['payment_id']}", headers=ctx["tenant_headers"]
    )
    assert len(by_payment.json()) == 1
