"""
Payment gateway abstraction.

The mock gateway is fully functional in-process (development/tests): charges
are tracked in memory and webhook events are HMAC-signed JSON. Real providers
(Stripe, PayPal, M-Pesa) require credentials from a secrets manager; selecting
one without credentials fails closed with PaymentGatewayError.
"""
import hashlib
import hmac
import uuid
from typing import Callable, Dict, Optional

from app.config.settings import settings


class PaymentGatewayError(Exception):
    """Raised when a gateway operation cannot be completed."""


def sign_payload(raw_body: bytes, secret: str) -> str:
    """Signature format shared by the mock gateway and webhook verification."""
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


class MockGateway:
    """
    In-process mock gateway.

    Webhook contract: JSON body
        {"id": "evt_...", "type": "payment.succeeded" | "payment.failed",
         "data": {"provider_txn_id": "..."}}
    signed with PAYMENT_WEBHOOK_SECRET in the X-Webhook-Signature header.
    """

    def __init__(self) -> None:
        self.charges: Dict[str, str] = {}

    @property
    def name(self) -> str:
        return "mock"

    def create_charge(self, amount: str, currency: str, reference: str) -> Dict[str, str]:
        txn_id = f"mock_{uuid.uuid4().hex}"
        self.charges[txn_id] = "processing"
        return {"provider_txn_id": txn_id, "status": "processing"}

    def verify_signature(self, raw_body: bytes, signature: Optional[str]) -> bool:
        secret = settings.PAYMENT_WEBHOOK_SECRET
        if not secret or not signature:
            return False
        return hmac.compare_digest(sign_payload(raw_body, secret), signature)

    def parse_event(self, payload: Dict) -> Dict[str, Optional[str]]:
        data = payload.get("data") or {}
        return {
            "event_id": payload.get("id"),
            "type": payload.get("type"),
            "provider_txn_id": data.get("provider_txn_id"),
        }

    def fetch_transaction_status(self, provider_txn_id: str) -> str:
        return self.charges.get(provider_txn_id, "unknown")


class UnconfiguredGateway:
    """Placeholder for a provider whose credentials are not configured."""

    def __init__(self, name: str, required_setting: str) -> None:
        self._name = name
        self._required_setting = required_setting

    @property
    def name(self) -> str:
        return self._name

    def _fail(self) -> None:
        raise PaymentGatewayError(
            f"{self._name} gateway is not configured; set {self._required_setting} "
            "(from a secrets manager) to enable it"
        )

    def create_charge(self, amount: str, currency: str, reference: str) -> Dict[str, str]:
        self._fail()

    def verify_signature(self, raw_body: bytes, signature: Optional[str]) -> bool:
        self._fail()

    def parse_event(self, payload: Dict) -> Dict[str, Optional[str]]:
        self._fail()

    def fetch_transaction_status(self, provider_txn_id: str) -> str:
        self._fail()


def _unconfigured(name: str, required: str) -> Callable[[], UnconfiguredGateway]:
    return lambda: UnconfiguredGateway(name, required)


# The mock keeps state across calls within a process so webhooks and
# reconciliation observe the charges created earlier in the same run.
mock_gateway = MockGateway()


def _mock() -> MockGateway:
    return mock_gateway


_registry: Dict[str, Callable] = {
    "mock": _mock,
    "stripe": _unconfigured("stripe", "STRIPE_SECRET_KEY"),
    "paypal": _unconfigured("paypal", "PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET"),
    "mpesa": _unconfigured("mpesa", "MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET"),
}


def get_gateway():
    provider = settings.PAYMENT_GATEWAY
    factory = _registry.get(provider)
    if factory is None:
        raise PaymentGatewayError(f"Unknown PAYMENT_GATEWAY '{provider}'")
    if provider == "mock" and settings.is_production:
        raise PaymentGatewayError("mock payment gateway is not allowed in production")
    return factory()
