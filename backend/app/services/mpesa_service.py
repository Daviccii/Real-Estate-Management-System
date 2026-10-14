"""
Safaricom M-Pesa (Daraja) rent collection for PropNoxa.

Implements the official STK Push (M-Pesa Express) collection flow against the
documented Daraja endpoints:

    sandbox    https://sandbox.safaricom.co.ke
    production https://api.safaricom.co.ke   (blocked until
               MPESA_PRODUCTION_ENABLED=true after sandbox validation)

Design rules this module enforces:

- The integration is inert until every MPESA_* credential is configured;
  unrelated application features keep working (MpesaConfigError only fires
  when an M-Pesa operation is actually attempted).
- OAuth tokens are cached in-process until shortly before expiry.
- The STK password/timestamp are generated per request on Africa/Nairobi time.
- Phone numbers are normalized to the Daraja 2547XXXXXXXX/2541XXXXXXXX form.
- No blind retries. A retry happens only on a 401 (the request was rejected,
  never accepted), so a second STK prompt can never be created unknowingly.
  Read timeouts / 5xx are recorded as `unknown` for reconciliation instead.
- Callbacks are matched to the pending checkout, validated, and applied
  exactly once via an atomic status claim; replays only enrich audit data.
  The ledger (Payment) is credited only from a verified ResultCode 0 and only
  when the callback amount matches the initiated amount.
- A late/duplicate success that arrives after the obligation is settled is
  never silently dropped: it is recorded (receipt intact) and flagged for
  manual review — collections are never auto-refunded or auto-payouted.
- No secrets (consumer secret, passkey, OAuth token, STK password) are ever
  logged or returned; failure details are sanitized and truncated.

All Safaricom HTTP calls funnel through _http_request so automated tests can
replace the transport without touching real endpoints.
"""
import base64
import logging
import re
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

import httpx
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.mpesa_refund import MpesaRefund
from app.models.mpesa_transaction import MpesaTransaction
from app.models.payment import Payment
from app.schemas.mpesa import StkCallbackPayload
from app.services.audit_service import log_audit_event
from app.services.security_events import emit_security_event
from app.utils.money import format_amount, parse_amount
from app.utils.phone import normalize_kenyan_phone
from app.utils.time import utc_now

logger = logging.getLogger(__name__)

BASE_URLS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}

# Statuses that still expect a Safaricom outcome.
LIVE_STATUSES = ("pending", "awaiting_callback", "unknown")
TERMINAL_STATUSES = ("succeeded", "failed", "cancelled", "timed_out", "expired")

# Safaricom STK result codes we translate into distinct statuses.
RESULT_CANCELLED = 1032
RESULT_TIMEOUT = 1037
RESULT_EXPIRED = 1019
QUERY_STILL_PROCESSING = "500.001.1001"


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------

class MpesaError(Exception):
    """Base class for every M-Pesa failure surfaced to routers."""


class MpesaConfigError(MpesaError):
    """Credentials missing/incomplete or production mode not enabled."""


class MpesaValidationError(MpesaError):
    """Invalid phone number / amount supplied by the caller."""


class MpesaPaymentNotEligible(MpesaError):
    """The obligation is already settled or otherwise not payable."""


class MpesaDuplicateRequest(MpesaError):
    """A live STK request already exists for this obligation."""

    def __init__(self, message: str, transaction: MpesaTransaction):
        super().__init__(message)
        self.transaction = transaction


class MpesaRequestError(MpesaError):
    """Safaricom definitively rejected the request; nothing was charged."""

    def __init__(self, message: str, transaction: Optional[MpesaTransaction] = None):
        super().__init__(message)
        self.transaction = transaction


class MpesaUnconfirmed(MpesaError):
    """Outcome unknown (timeout/5xx after submission); reconcile to confirm."""

    def __init__(self, message: str, transaction: MpesaTransaction):
        super().__init__(message)
        self.transaction = transaction


class MpesaCallbackError(MpesaError):
    """Callback payload failed structural validation."""


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

_REQUIRED_CONFIG_FIELDS = (
    "MPESA_CONSUMER_KEY",
    "MPESA_CONSUMER_SECRET",
    "MPESA_SHORTCODE",
    "MPESA_PASSKEY",
    "MPESA_CALLBACK_URL",
)


def mpesa_config_status() -> Dict[str, Any]:
    """Non-secret configuration status for health/metrics and the frontend."""
    missing = [name for name in _REQUIRED_CONFIG_FIELDS if not getattr(settings, name)]
    env = settings.MPESA_ENVIRONMENT
    production_blocked = env == "production" and not settings.MPESA_PRODUCTION_ENABLED
    callback = settings.MPESA_CALLBACK_URL or ""
    callback_valid = callback.startswith("https://") if env == "production" else bool(callback)
    return {
        "configured": not missing and not production_blocked and callback_valid,
        "environment": env,
        "production_enabled": settings.MPESA_PRODUCTION_ENABLED,
        "missing": missing,
    }


def base_url() -> str:
    return BASE_URLS[settings.MPESA_ENVIRONMENT]


def ensure_mpesa_configured() -> None:
    """Raise MpesaConfigError with an actionable message when unusable."""
    status = mpesa_config_status()
    if status["configured"]:
        return
    if status["missing"]:
        raise MpesaConfigError(
            "M-Pesa is not configured. Set "
            + ", ".join(status["missing"])
            + " in backend/.env (see MPESA_SETUP.md). Unrelated features are unaffected."
        )
    if settings.MPESA_ENVIRONMENT == "production" and not settings.MPESA_PRODUCTION_ENABLED:
        raise MpesaConfigError(
            "MPESA_ENVIRONMENT=production is blocked until sandbox validation "
            "completes. Set MPESA_PRODUCTION_ENABLED=true deliberately to go live."
        )
    raise MpesaConfigError(
        "MPESA_CALLBACK_URL must be an https:// URL when MPESA_ENVIRONMENT=production "
        "so Safaricom can deliver callbacks securely."
    )


def account_reference() -> str:
    """Daraja caps the account reference at 12 characters."""
    return (settings.MPESA_ACCOUNT_REFERENCE or "PropNoxa").strip()[:12]


# --------------------------------------------------------------------------
# Transport (single choke point for tests)
# --------------------------------------------------------------------------

def _http_request(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
    auth: Optional[httpx.Auth] = None,
    timeout: Optional[float] = None,
) -> httpx.Response:
    return httpx.request(
        method,
        url,
        headers=headers,
        json=json_body,
        params=params,
        auth=auth,
        timeout=timeout or float(settings.MPESA_TIMEOUT_SECONDS),
        follow_redirects=False,
    )


def _sanitize(value: Any, limit: int = 255) -> Optional[str]:
    """Strip control characters and truncate; never store raw payloads."""
    if value is None:
        return None
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value)).strip()
    return text[:limit] or None


# --------------------------------------------------------------------------
# OAuth token cache
# --------------------------------------------------------------------------

_token_lock = threading.Lock()
_token_cache: Dict[str, Any] = {"access_token": None, "expires_at": 0.0}


def _clear_token_cache() -> None:
    with _token_lock:
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = 0.0


def get_access_token(*, force_refresh: bool = False) -> str:
    """Return a cached Daraja OAuth token, refreshing shortly before expiry."""
    with _token_lock:
        cached = _token_cache["access_token"]
        if not force_refresh and cached and time.time() < _token_cache["expires_at"] - 30:
            return cached

        if not settings.MPESA_CONSUMER_KEY or not settings.MPESA_CONSUMER_SECRET:
            raise MpesaConfigError(
                "MPESA_CONSUMER_KEY / MPESA_CONSUMER_SECRET are not set (see MPESA_SETUP.md)"
            )

        url = f"{base_url()}/oauth/v1/generate"
        try:
            response = _http_request(
                "GET",
                url,
                params={"grant_type": "client_credentials"},
                auth=httpx.BasicAuth(
                    settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET
                ),
            )
        except httpx.ConnectError as exc:
            raise MpesaRequestError(
                "Could not reach Safaricom to obtain an access token; nothing was charged"
            ) from exc
        except httpx.TimeoutException as exc:
            raise MpesaRequestError(
                "Safaricom did not answer the OAuth request in time; nothing was charged"
            ) from exc
        except httpx.HTTPError as exc:
            raise MpesaRequestError(
                "The Safaricom OAuth request failed; nothing was charged"
            ) from exc

        if response.status_code != 200:
            raise MpesaRequestError(
                f"Safaricom rejected the OAuth credentials (HTTP {response.status_code}); "
                "verify MPESA_CONSUMER_KEY / MPESA_CONSUMER_SECRET"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise MpesaRequestError("Safaricom returned an unreadable OAuth response") from exc

        token = data.get("access_token")
        if not token:
            raise MpesaRequestError("Safaricom OAuth response did not include an access token")
        try:
            expires_in = int(data.get("expires_in", 3599))
        except (TypeError, ValueError):
            expires_in = 3599

        _token_cache["access_token"] = token
        _token_cache["expires_at"] = time.time() + max(60, expires_in)
        return token


# --------------------------------------------------------------------------
# STK password / timestamp (Africa/Nairobi, UTC+3, no DST)
# --------------------------------------------------------------------------

EAT = timezone(timedelta(hours=3))


def stk_timestamp(when: Optional[datetime] = None) -> str:
    """YYYYMMDDHHMMSS in Kenya local time, as Daraja expects."""
    moment = when.astimezone(EAT) if when is not None else datetime.now(EAT)
    return moment.strftime("%Y%m%d%H%M%S")


def stk_password(shortcode: str, passkey: str, timestamp: str) -> str:
    return base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()


# --------------------------------------------------------------------------
# Amount / obligation helpers
# --------------------------------------------------------------------------

def applied_sum_for_payment(db: Session, payment_id: int) -> Decimal:
    """Total already credited to an obligation by applied M-Pesa transactions."""
    rows = (
        db.query(MpesaTransaction)
        .filter(
            MpesaTransaction.payment_id == payment_id,
            MpesaTransaction.applied_to_payment.is_(True),
        )
        .all()
    )
    total = Decimal("0")
    for row in rows:
        value = parse_amount(row.amount)
        if value is not None:
            total += value
    return total


def refunded_sum_for_payment(db: Session, payment_id: int) -> Decimal:
    """Total refunded against an obligation via recorded M-Pesa refunds."""
    total = (
        db.query(func.sum(MpesaRefund.amount))
        .filter(MpesaRefund.payment_id == payment_id)
        .scalar()
    )
    return Decimal(total) if total is not None else Decimal("0")


def net_credited_for_payment(db: Session, payment_id: int) -> Decimal:
    """Collected minus refunded: what the obligation has truly received."""
    return applied_sum_for_payment(db, payment_id) - refunded_sum_for_payment(db, payment_id)


def record_refund(
    db: Session,
    mpesa_transaction_id: int,
    amount: Decimal,
    reason: str,
    reversal_reference: Optional[str] = None,
    recorded_by: Optional[int] = None,
) -> MpesaRefund:
    """
    Record a refund issued against a succeeded M-Pesa collection.

    The app does not move money (no Daraja B2C): the landlord performs the
    reversal through their own M-Pesa channel and records it here.

    Args:
        db: Database session
        mpesa_transaction_id: The succeeded collection to refund against
        amount: Whole Kenyan shillings to refund
        reason: Why the refund was issued
        reversal_reference: M-Pesa transaction code of the landlord-side reversal
        recorded_by: User ID who recorded this refund

    Returns:
        The created MpesaRefund record

    Raises:
        MpesaValidationError: If amount validation fails
        MpesaPaymentNotEligible: If the transaction is not eligible for refund
    """
    # Validate amount
    normalized = parse_amount(amount)
    if normalized is None or normalized != normalized.to_integral_value():
        raise MpesaValidationError("Enter a whole-shilling amount (no cents)")
    if normalized < Decimal("1"):
        raise MpesaValidationError("The amount must be at least KSh 1")

    # Fetch the transaction
    txn = db.query(MpesaTransaction).filter(MpesaTransaction.id == mpesa_transaction_id).first()
    if not txn:
        raise MpesaValidationError("M-Pesa transaction not found")

    # Must be a succeeded transaction
    if txn.status != "succeeded":
        raise MpesaPaymentNotEligible(
            f"Refunds can only be recorded against succeeded transactions. Current status: {txn.status}"
        )

    # Check that refund amount doesn't exceed collected amount
    collected = applied_sum_for_payment(db, txn.payment_id) if txn.payment_id else Decimal("0")
    already_refunded = refunded_sum_for_payment(db, txn.payment_id) if txn.payment_id else Decimal("0")
    remaining = collected - already_refunded
    if normalized > remaining:
        raise MpesaValidationError(
            f"Refund amount exceeds remaining collected balance. Collected: KSh {collected}, "
            f"Already refunded: KSh {already_refunded}, Remaining: KSh {remaining}"
        )

    # Create the refund record
    refund = MpesaRefund(
        mpesa_transaction_id=mpesa_transaction_id,
        payment_id=txn.payment_id,
        amount=normalized,
        currency="KES",
        reason=reason[:500],  # Truncate if too long
        reversal_reference=reversal_reference[:64] if reversal_reference else None,
        status="recorded",
        recorded_by=recorded_by,
    )
    db.add(refund)
    db.commit()
    db.refresh(refund)

    # Log audit event
    log_audit_event(
        db,
        recorded_by,
        "MPESA_REFUND_RECORDED",
        entity_type="mpesa_refund",
        entity_id=refund.id,
        details={
            "mpesa_transaction_id": mpesa_transaction_id,
            "payment_id": txn.payment_id,
            "amount": format_amount(normalized),
            "reason": reason,
            "reversal_reference": reversal_reference,
        },
    )

    return refund


def outstanding_for_payment(db: Session, payment: Payment) -> Decimal:
    obligation = parse_amount(payment.amount)
    if obligation is None:
        return Decimal("0")
    outstanding = obligation - net_credited_for_payment(db, payment.id)
    return max(Decimal("0"), outstanding)


def validate_stk_amount(amount: Decimal, outstanding: Decimal) -> Decimal:
    """Whole shillings, >= 1, within the M-Pesa cap and the outstanding balance."""
    normalized = parse_amount(amount)
    if normalized is None or normalized != normalized.to_integral_value():
        raise MpesaValidationError("Enter a whole-shilling amount (no cents)")
    if normalized < Decimal("1"):
        raise MpesaValidationError("The amount must be at least KSh 1")
    maximum = Decimal(str(settings.MPESA_MAX_AMOUNT))
    if normalized > maximum:
        raise MpesaValidationError(
            f"Single payments are limited to KSh {int(maximum):,}"
        )
    if normalized > outstanding:
        raise MpesaValidationError(
            f"The amount exceeds the outstanding balance of KSh {outstanding:,.2f}"
        )
    return normalized


# --------------------------------------------------------------------------
# Rate limiting (payment initiation / reconciliation)
# --------------------------------------------------------------------------

_rate_lock = threading.Lock()
_rate_state: Dict[str, Tuple[int, int]] = {}
_rate_redis_client = None


def allow_mpesa_action(user_id: int, bucket: str, limit: int, window_seconds: int = 3600) -> bool:
    """
    Fixed-window limiter for abuse-prone M-Pesa endpoints.

    Uses Redis when configured (shared across workers); otherwise falls back
    to a bounded in-process window. Failure to reach Redis degrades to the
    in-process limiter instead of blocking payments outright.
    """
    if limit <= 0:
        return True
    window = int(time.time()) // window_seconds
    key = f"mpesa-rate:{bucket}:{user_id}:{window}"

    global _rate_redis_client
    if settings.REDIS_URL:
        try:
            if _rate_redis_client is None:
                import redis as redis_lib

                _rate_redis_client = redis_lib.Redis.from_url(
                    settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1
                )
            count = _rate_redis_client.incr(key)
            if count == 1:
                _rate_redis_client.expire(key, window_seconds + 60)
            return count <= limit
        except Exception:
            logger.warning("Redis unavailable for M-Pesa rate limiting; using in-process limiter")

    with _rate_lock:
        if len(_rate_state) > 10000:  # bound memory; stale windows are useless
            _rate_state.clear()
        current = _rate_state.get(key, 0)
        _rate_state[key] = current + 1
        return _rate_state[key] <= limit


# --------------------------------------------------------------------------
# STK Push initiation
# --------------------------------------------------------------------------

def _new_reference() -> str:
    return f"MPX-{uuid.uuid4().hex[:8].upper()}"


class _AmbiguousTransport(Exception):
    """Internal: the request may have reached Safaricom; outcome unknown."""


def _stk_push_request(amount_kes: int, phone: str) -> Dict[str, Any]:
    """
    POST the STK Push to Daraja. Raises MpesaRequestError (definite, nothing
    charged) or _AmbiguousTransport (outcome unknown) — never anything else.
    """
    # One timestamp for both fields: the password must encode exactly the
    # Timestamp that is sent, or Daraja rejects the request.
    timestamp = stk_timestamp()
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": stk_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY or "", timestamp),
        "Timestamp": timestamp,
        "TransactionType": settings.MPESA_TRANSACTION_TYPE,
        "Amount": amount_kes,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference(),
        "TransactionDesc": (settings.MPESA_TRANSACTION_DESCRIPTION or "Rent Payment")[:13],
    }
    url = f"{base_url()}/mpesa/stkpush/v1/processrequest"

    def _post(token: str):
        return _http_request(
            "POST", url, headers={"Authorization": f"Bearer {token}"}, json_body=payload
        )

    token = get_access_token()
    try:
        response = _post(token)
    except httpx.ConnectError as exc:
        raise MpesaRequestError("Could not reach Safaricom; the request was not submitted") from exc
    except httpx.TimeoutException as exc:
        raise _AmbiguousTransport(
            "Timed out waiting for Safaricom after submitting; the outcome must be confirmed"
        ) from exc
    except httpx.HTTPError as exc:
        raise _AmbiguousTransport("The connection to Safaricom failed mid-request") from exc

    # 401 = request rejected, never accepted; a fresh-token retry is safe.
    if response.status_code == 401:
        token = get_access_token(force_refresh=True)
        try:
            response = _post(token)
        except httpx.ConnectError as exc:
            raise MpesaRequestError("Could not reach Safaricom; the request was not submitted") from exc
        except httpx.TimeoutException as exc:
            raise _AmbiguousTransport(
                "Timed out waiting for Safaricom after submitting; the outcome must be confirmed"
            ) from exc
        except httpx.HTTPError as exc:
            raise _AmbiguousTransport("The connection to Safaricom failed mid-request") from exc

    if response.status_code >= 500:
        raise _AmbiguousTransport(
            f"Safaricom returned HTTP {response.status_code}; the outcome must be confirmed"
        )
    if response.status_code == 401:
        raise MpesaRequestError("Safaricom rejected the access token after a refresh")
    if response.status_code != 200:
        raise MpesaRequestError(
            f"Safaricom rejected the STK request (HTTP {response.status_code}); no payment was taken"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise MpesaRequestError("Safaricom returned an unreadable STK response") from exc

    response_code = str(data.get("ResponseCode", ""))
    if response_code != "0" or not data.get("CheckoutRequestID"):
        reason = data.get("ResponseDescription") or data.get("errorMessage") or "request rejected"
        raise MpesaRequestError(_sanitize(reason, 255) or "STK request rejected")
    return data


def initiate_stk_push(
    db: Session,
    *,
    payment: Payment,
    tenant_id: int,
    phone_number: str,
    amount: Decimal,
    actor_id: Optional[int] = None,
) -> MpesaTransaction:
    """
    Create the collection attempt and push the STK prompt.

    The transaction row is committed before the network call so a crash or
    timeout can never lose track of a possibly-charged request.
    """
    ensure_mpesa_configured()

    if payment.status == "paid":
        raise MpesaPaymentNotEligible("This rent obligation is already fully paid")
    if payment.status not in ("pending", "partially_paid"):
        raise MpesaPaymentNotEligible(
            f"This rent obligation cannot be paid online (status: {payment.status})"
        )

    outstanding = outstanding_for_payment(db, payment)
    if outstanding <= 0:
        raise MpesaPaymentNotEligible("This rent obligation is already fully settled")

    validated_amount = validate_stk_amount(amount, outstanding)

    try:
        normalized_phone = normalize_kenyan_phone(phone_number)
    except ValueError as exc:
        raise MpesaValidationError(str(exc)) from exc

    # One live STK request per obligation at a time: an old prompt the user
    # may still be answering must never be duplicated (double PIN prompts).
    window_start = utc_now() - timedelta(seconds=settings.MPESA_DUPLICATE_WINDOW_SECONDS)
    existing = (
        db.query(MpesaTransaction)
        .filter(
            MpesaTransaction.payment_id == payment.id,
            MpesaTransaction.status.in_(LIVE_STATUSES),
            MpesaTransaction.initiated_at >= window_start,
        )
        .order_by(MpesaTransaction.id.desc())
        .first()
    )
    if existing is not None:
        raise MpesaDuplicateRequest(
            "A payment request for this obligation is already in progress", existing
        )

    property_obj = payment.property

    txn = MpesaTransaction(
        reference=_new_reference(),
        payment_id=payment.id,
        tenant_id=tenant_id,
        lease_id=payment.lease_id,
        property_id=payment.property_id,
        unit_id=payment.unit_id,
        landlord_id=getattr(property_obj, "owner_id", None),
        company_id=getattr(property_obj, "company_id", None),
        amount=validated_amount,
        currency="KES",
        channel="mpesa_stk",
        phone_number=normalized_phone,
        status="pending",
        initiated_at=utc_now(),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    try:
        data = _stk_push_request(int(validated_amount), normalized_phone)
    except _AmbiguousTransport as exc:
        txn.status = "unknown"
        txn.failure_reason = _sanitize(str(exc), 255)
        db.commit()
        log_audit_event(
            db,
            actor_id or tenant_id,
            "MPESA_STK_PUSH_UNCONFIRMED",
            entity_type="mpesa_transaction",
            entity_id=txn.id,
            details={
                "payment_id": payment.id,
                "amount": format_amount(validated_amount),
                "initiated_by": actor_id or tenant_id,
            },
        )
        raise MpesaUnconfirmed(
            "We could not confirm whether the M-Pesa prompt was delivered. "
            "Do not resend immediately — check the status in a moment.",
            txn,
        ) from exc
    except MpesaRequestError as exc:
        txn.status = "failed"
        txn.failure_reason = _sanitize(str(exc), 255)
        txn.completed_at = utc_now()
        db.commit()
        log_audit_event(
            db,
            actor_id or tenant_id,
            "MPESA_STK_PUSH_REJECTED",
            entity_type="mpesa_transaction",
            entity_id=txn.id,
            details={
                "payment_id": payment.id,
                "reason": txn.failure_reason,
                "initiated_by": actor_id or tenant_id,
            },
        )
        raise MpesaRequestError(str(exc), transaction=txn) from exc

    txn.status = "awaiting_callback"
    txn.merchant_request_id = _sanitize(data.get("MerchantRequestID"), 64)
    txn.checkout_request_id = _sanitize(data.get("CheckoutRequestID"), 64)
    db.commit()
    db.refresh(txn)

    log_audit_event(
        db,
        actor_id or tenant_id,
        "MPESA_STK_PUSH_INITIATED",
        entity_type="mpesa_transaction",
        entity_id=txn.id,
        details={
            "payment_id": payment.id,
            "amount": format_amount(validated_amount),
            "checkout_request_id": txn.checkout_request_id,
            "initiated_by": actor_id or tenant_id,
        },
    )
    return txn


# --------------------------------------------------------------------------
# Callback processing (exactly-once application)
# --------------------------------------------------------------------------

def _status_for_result_code(code: Optional[int]) -> str:
    if code == 0:
        return "succeeded"
    if code == RESULT_CANCELLED:
        return "cancelled"
    if code == RESULT_TIMEOUT:
        return "timed_out"
    if code == RESULT_EXPIRED:
        return "expired"
    return "failed"


def _claim(db: Session, txn_id: int, values: Dict[str, Any]) -> int:
    """
    Atomically move a live transaction to its new state.

    Returns 1 for the single winner, 0 when another writer already finalized
    the row (replay / concurrent callback). Guarantees exactly-once crediting.
    """
    claimed = (
        db.query(MpesaTransaction)
        .filter(MpesaTransaction.id == txn_id, MpesaTransaction.status.in_(LIVE_STATUSES))
        .update(values, synchronize_session=False)
    )
    return int(claimed or 0)


def _lock_payment(db: Session, payment_id: int) -> Optional[Payment]:
    """Fetch the obligation for updating; row-locked on Postgres to serialize credit."""
    query = db.query(Payment).filter(Payment.id == payment_id)
    if db.bind.dialect.name != "sqlite":
        query = query.with_for_update()
    return query.first()


def _apply_credit(db: Session, txn: MpesaTransaction, amount: Decimal) -> bool:
    """
    Credit the rent obligation from a verified success. Must run inside the
    same transaction as the status claim. Returns True when the ledger moved.
    """
    payment = _lock_payment(db, txn.payment_id)
    if payment is None:  # obligation deleted mid-flight; receipt kept, nothing to credit
        return False

    obligation = parse_amount(payment.amount)
    # Net of refunds: money sent back to the tenant reopens that part of the
    # obligation, so it must not count towards what has been settled.
    already = net_credited_for_payment(db, payment.id)
    if obligation is None or payment.status == "paid" or already >= obligation:
        # Real money arrived for an already-settled obligation: never drop the
        # receipt, never double-count the ledger — flag for manual review.
        emit_security_event(
            "mpesa.overpayment_review",
            user_id=txn.tenant_id,
            outcome="denied",
            severity="high",
            details={
                "transaction_id": txn.id,
                "payment_id": payment.id,
                "amount": format_amount(amount),
                "reference": txn.reference,
            },
        )
        return False

    new_total = already + amount
    if new_total >= obligation:
        payment.status = "paid"
        payment.payment_date = utc_now()
    else:
        payment.status = "partially_paid"
    payment.payment_method = "mpesa"
    return True


def process_callback(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and apply one Daraja STK callback. Idempotent: replays and
    concurrent deliveries can only enrich audit fields, never re-credit.

    Returns {"received", "matched", "applied", "status", "enriched"}.
    Raises MpesaCallbackError for structurally invalid payloads only.
    """
    try:
        parsed = StkCallbackPayload.model_validate(payload)
    except ValidationError as exc:
        raise MpesaCallbackError("Malformed callback payload") from exc

    callback = parsed.Body.stkCallback
    now = utc_now()

    txn = (
        db.query(MpesaTransaction)
        .filter(MpesaTransaction.checkout_request_id == callback.CheckoutRequestID)
        .first()
    )
    if txn is None:
        # Never trust the URL: an unmatchable checkout is not from a request
        # we made. Acknowledge (so Safaricom stops retrying) and record it.
        log_audit_event(
            db,
            None,
            "MPESA_CALLBACK_UNMATCHED",
            entity_type="mpesa_transaction",
            details={"checkout_request_id": _sanitize(callback.CheckoutRequestID, 64)},
        )
        emit_security_event(
            "mpesa.callback.unknown_checkout",
            outcome="denied",
            severity="warning",
            details={"checkout_request_id": _sanitize(callback.CheckoutRequestID, 64)},
        )
        return {"received": True, "matched": False, "applied": False, "status": None, "enriched": False}

    items = {}
    if callback.CallbackMetadata is not None:
        items = {item.Name: item.Value for item in callback.CallbackMetadata.Item}
    receipt = _sanitize(items.get("MpesaReceiptNumber"), 64)
    received_amount = parse_amount(items.get("Amount"))

    if txn.status not in LIVE_STATUSES:
        # Replay, late duplicate, or receipt enrichment after reconciliation.
        enriched = False
        updates: Dict[str, Any] = {
            "callback_attempts": txn.callback_attempts + 1,
            "callback_received_at": now,
        }
        if callback.ResultCode == 0 and receipt and not txn.mpesa_receipt_number:
            updates["mpesa_receipt_number"] = receipt
            enriched = True
        db.query(MpesaTransaction).filter(MpesaTransaction.id == txn.id).update(
            updates, synchronize_session=False
        )
        db.commit()
        log_audit_event(
            db,
            None,
            "MPESA_CALLBACK_REPLAY",
            entity_type="mpesa_transaction",
            entity_id=txn.id,
            details={"status": txn.status, "enriched_receipt": enriched},
        )
        return {
            "received": True,
            "matched": True,
            "applied": False,
            "status": txn.status,
            "enriched": enriched,
        }

    values: Dict[str, Any] = {
        "result_code": callback.ResultCode,
        "result_description": _sanitize(callback.ResultDesc, 500),
        "callback_received_at": now,
        "callback_attempts": txn.callback_attempts + 1,
    }

    if callback.ResultCode == 0:
        if receipt is None or received_amount is None:
            values.update(
                status="unknown",
                failure_reason="Success callback missing receipt metadata; reconcile before crediting",
            )
            _claim(db, txn.id, values)
            db.commit()
            emit_security_event(
                "mpesa.callback.malformed_success",
                outcome="denied",
                severity="high",
                details={"transaction_id": txn.id},
            )
            return {"received": True, "matched": True, "applied": False, "status": "unknown", "enriched": False}

        if received_amount != parse_amount(txn.amount):
            values.update(
                status="unknown",
                mpesa_receipt_number=receipt,
                failure_reason=(
                    f"Amount mismatch: callback KSh {received_amount} vs "
                    f"requested KSh {format_amount(txn.amount)}; held for manual review"
                ),
            )
            claimed = _claim(db, txn.id, values)
            db.commit()
            if claimed:
                emit_security_event(
                    "mpesa.callback.amount_mismatch",
                    outcome="denied",
                    severity="high",
                    details={
                        "transaction_id": txn.id,
                        "received": format_amount(received_amount),
                        "expected": format_amount(txn.amount),
                    },
                )
                log_audit_event(
                    db,
                    None,
                    "MPESA_PAYMENT_HELD_FOR_REVIEW",
                    entity_type="mpesa_transaction",
                    entity_id=txn.id,
                    details={"reason": values["failure_reason"]},
                )
            return {"received": True, "matched": True, "applied": False, "status": "unknown", "enriched": False}

        values.update(
            status="succeeded",
            mpesa_receipt_number=receipt,
            completed_at=now,
        )
        claimed = _claim(db, txn.id, values)
        if not claimed:
            # Lost the race against a concurrent delivery: treat as replay.
            db.rollback()
            db.expire(txn)
            return {"received": True, "matched": True, "applied": False, "status": txn.status, "enriched": False}
        applied = _apply_credit(db, txn, received_amount)
        if applied:
            db.query(MpesaTransaction).filter(MpesaTransaction.id == txn.id).update(
                {"applied_to_payment": True}, synchronize_session=False
            )
        db.commit()
        log_audit_event(
            db,
            None,
            "MPESA_PAYMENT_SUCCEEDED",
            entity_type="mpesa_transaction",
            entity_id=txn.id,
            details={
                "payment_id": txn.payment_id,
                "receipt": receipt,
                "amount": format_amount(received_amount),
                "applied_to_payment": applied,
            },
        )
        return {
            "received": True,
            "matched": True,
            "applied": applied,
            "status": "succeeded",
            "enriched": False,
        }

    status = _status_for_result_code(callback.ResultCode)
    values.update(status=status, completed_at=now)
    claimed = _claim(db, txn.id, values)
    db.commit()
    if claimed:
        log_audit_event(
            db,
            None,
            "MPESA_PAYMENT_FAILED",
            entity_type="mpesa_transaction",
            entity_id=txn.id,
            details={"result_code": callback.ResultCode, "status": status},
        )
    return {"received": True, "matched": True, "applied": False, "status": status, "enriched": False}


# --------------------------------------------------------------------------
# Reconciliation (STK Push Query)
# --------------------------------------------------------------------------

def _stk_query_request(checkout_request_id: str) -> Dict[str, Any]:
    """Query Daraja for the status of a submitted STK request."""
    timestamp = stk_timestamp()
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": stk_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY or "", timestamp),
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }
    url = f"{base_url()}/mpesa/stkpushquery/v1/query"

    def _post(token: str):
        return _http_request(
            "POST", url, headers={"Authorization": f"Bearer {token}"}, json_body=payload
        )

    token = get_access_token()
    try:
        response = _post(token)
        if response.status_code == 401:
            response = _post(get_access_token(force_refresh=True))
    except httpx.TimeoutException as exc:
        raise MpesaRequestError("Safaricom did not answer the status query in time") from exc
    except httpx.HTTPError as exc:
        raise MpesaRequestError("The Safaricom status query could not be delivered") from exc

    try:
        data = response.json()
    except ValueError:
        data = {}

    if response.status_code >= 500:
        error_code = str(data.get("errorCode") or data.get("ResponseCode") or "")
        if error_code.startswith(QUERY_STILL_PROCESSING) or "being processed" in str(data.get("errorMessage", "")).lower():
            return {"still_processing": True}
        raise MpesaRequestError(
            f"Safaricom could not process the status query (HTTP {response.status_code})"
        )
    if response.status_code != 200:
        raise MpesaRequestError(f"Safaricom rejected the status query (HTTP {response.status_code})")
    return data


def reconcile_transaction(
    db: Session, txn: MpesaTransaction, *, actor_id: Optional[int] = None
) -> str:
    """
    Confirm one transaction's true status with Daraja.

    Returns "confirmed" when the status changed, otherwise a descriptive
    marker ("still_processing", "already_terminal", "repaired").
    """
    ensure_mpesa_configured()

    if txn.status in TERMINAL_STATUSES:
        # Repair the narrow crash window: success recorded but never credited.
        if txn.status == "succeeded" and not txn.applied_to_payment:
            amount = parse_amount(txn.amount)
            if amount is not None:
                applied = _apply_credit(db, txn, amount)
                if applied:
                    db.query(MpesaTransaction).filter(MpesaTransaction.id == txn.id).update(
                        {"applied_to_payment": True}, synchronize_session=False
                    )
                db.commit()
                if applied:
                    log_audit_event(
                        db,
                        actor_id,
                        "MPESA_PAYMENT_LEDGER_REPAIRED",
                        entity_type="mpesa_transaction",
                        entity_id=txn.id,
                        details={"payment_id": txn.payment_id},
                    )
                    return "repaired"
        return "already_terminal"

    if not txn.checkout_request_id:
        raise MpesaRequestError(
            "No checkout request id was recorded for this attempt; it cannot be queried"
        )

    data = _stk_query_request(txn.checkout_request_id)
    now = utc_now()

    if data.get("still_processing"):
        txn.reconciled_at = now
        db.commit()
        return "still_processing"

    result_code_raw = data.get("ResultCode")
    result_code = None
    try:
        result_code = int(str(result_code_raw))
    except (TypeError, ValueError):
        pass
    result_description = _sanitize(data.get("ResultDesc"), 500)

    values: Dict[str, Any] = {
        "result_code": result_code,
        "result_description": result_description,
        "reconciled_at": now,
    }

    if result_code == 0:
        values.update(status="succeeded", completed_at=now)
        claimed = _claim(db, txn.id, values)
        if not claimed:
            db.rollback()
            return "already_terminal"
        amount = parse_amount(txn.amount)
        applied = _apply_credit(db, txn, amount) if amount is not None else False
        if applied:
            db.query(MpesaTransaction).filter(MpesaTransaction.id == txn.id).update(
                {"applied_to_payment": True}, synchronize_session=False
            )
        db.commit()
        log_audit_event(
            db,
            actor_id,
            "MPESA_TRANSACTION_RECONCILED",
            entity_type="mpesa_transaction",
            entity_id=txn.id,
            details={"status": "succeeded", "applied_to_payment": applied, "via": "stk_query"},
        )
        return "confirmed"

    status = _status_for_result_code(result_code)
    values.update(status=status, completed_at=now)
    claimed = _claim(db, txn.id, values)
    db.commit()
    if claimed:
        log_audit_event(
            db,
            actor_id,
            "MPESA_TRANSACTION_RECONCILED",
            entity_type="mpesa_transaction",
            entity_id=txn.id,
            details={"status": status, "result_code": result_code, "via": "stk_query"},
        )
        return "confirmed"
    return "already_terminal"


def reconcile_stale_transactions(
    db: Session, *, older_than_minutes: int = 2, limit: int = 50
) -> Dict[str, int]:
    """Query Daraja for every live transaction older than the cutoff."""
    cutoff = utc_now() - timedelta(minutes=max(1, older_than_minutes))
    stale = (
        db.query(MpesaTransaction)
        .filter(
            MpesaTransaction.status.in_(LIVE_STATUSES),
            MpesaTransaction.initiated_at <= cutoff,
            MpesaTransaction.checkout_request_id.isnot(None),
        )
        .order_by(MpesaTransaction.initiated_at.asc())
        .limit(max(1, limit))
        .all()
    )
    counts = {"checked": 0, "updated": 0, "still_processing": 0, "errors": 0}
    for txn in stale:
        counts["checked"] += 1
        try:
            outcome = reconcile_transaction(db, txn)
        except MpesaError:
            counts["errors"] += 1
            continue
        if outcome == "confirmed":
            counts["updated"] += 1
        elif outcome == "still_processing":
            counts["still_processing"] += 1
    return counts


# --------------------------------------------------------------------------
# Serialization
# --------------------------------------------------------------------------

def serialize_transaction(txn: MpesaTransaction, *, include_names: bool = True) -> Dict[str, Any]:
    """API representation: masked phone, formatted amount, optional join names.

    Datetimes are emitted as ISO strings because this dict is sometimes placed
    inside an HTTPException detail, which bypasses FastAPI's jsonable_encoder.
    """
    from app.utils.phone import mask_phone

    def _iso(value):
        return value.isoformat() if value is not None else None

    data: Dict[str, Any] = {
        "id": txn.id,
        "reference": txn.reference,
        "payment_id": txn.payment_id,
        "tenant_id": txn.tenant_id,
        "lease_id": txn.lease_id,
        "property_id": txn.property_id,
        "unit_id": txn.unit_id,
        "landlord_id": txn.landlord_id,
        "company_id": txn.company_id,
        "amount": format_amount(txn.amount),
        "currency": txn.currency,
        "channel": txn.channel,
        "phone_number": mask_phone(txn.phone_number),
        "status": txn.status,
        "result_code": txn.result_code,
        "result_description": txn.result_description,
        "failure_reason": txn.failure_reason,
        "merchant_request_id": txn.merchant_request_id,
        "checkout_request_id": txn.checkout_request_id,
        "mpesa_receipt_number": txn.mpesa_receipt_number,
        "applied_to_payment": txn.applied_to_payment,
        "callback_attempts": txn.callback_attempts,
        "initiated_at": _iso(txn.initiated_at),
        "callback_received_at": _iso(txn.callback_received_at),
        "completed_at": _iso(txn.completed_at),
        "reconciled_at": _iso(txn.reconciled_at),
        "created_at": _iso(txn.created_at),
        "updated_at": _iso(txn.updated_at),
    }
    if include_names:
        data["property_name"] = txn.property.name if txn.property else None
        data["unit_number"] = txn.unit.unit_number if txn.unit else None
        data["tenant_name"] = txn.tenant.full_name if txn.tenant else None
    return data


def serialize_refund(refund: MpesaRefund) -> Dict[str, Any]:
    """API representation for a refund record."""
    return {
        "id": refund.id,
        "mpesa_transaction_id": refund.mpesa_transaction_id,
        "payment_id": refund.payment_id,
        "amount": format_amount(refund.amount),
        "currency": refund.currency,
        "reason": refund.reason,
        "reversal_reference": refund.reversal_reference,
        "status": refund.status,
        "recorded_by": refund.recorded_by,
        "created_at": refund.created_at.isoformat() if refund.created_at else None,
        "updated_at": refund.updated_at.isoformat() if refund.updated_at else None,
    }
