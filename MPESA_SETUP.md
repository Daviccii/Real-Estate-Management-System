# M-Pesa (Safaricom Daraja) Rent Collection — Setup Guide

This guide covers everything needed to enable real M-Pesa rent collection in PropNoxa:
STK Push (the PIN prompt on the tenant's phone), the Safaricom callback, server-side
reconciliation, and the production switch.

The integration is **inert but harmless** until configured: with no credentials set,
every unrelated feature keeps working, the tenant UI hides the M-Pesa controls, and
`/health/metrics` reports what is missing.

---

## 1. How it works (30 seconds)

```
Tenant clicks "Pay with M-Pesa" (tenant portal)
        │
        ▼
POST /api/v1/mpesa/stk-push ──► Daraja: /mpesa/stkpush/v1/processrequest
        │                               │
        │                    (tenant enters PIN on their handset —
        │                     the PIN never touches PropNoxa)
        │                               ▼
        │            Daraja: POST /api/v1/mpesa/callback  (public URL)
        ▼                               │
MpesaTransaction row             validated: must match a live checkout,
(pending → awaiting_callback)    applied exactly once to the payment,
                                 idempotent on replays
```

**Hard rules enforced by the code** (do not weaken):

- A success screen, an STK acceptance response, or the callback URL being reachable
  never marks anything paid. Only a validated server-side result does.
- A collection is applied to its payment **exactly once** — replays and duplicate
  callbacks are idempotent; overpayments are recorded but not double-counted.
- The tenant's PIN is never requested, transmitted, or stored by the application.
- Money is only ever attributed to the payment/lease/property it was initiated for.
- No retries that could create a second charge: an in-flight prompt blocks a new
  one for the same bill (`MPESA_DUPLICATE_WINDOW_SECONDS`), and ambiguous network
  failures are parked as `unknown` for reconciliation — never blindly resent.

---

## 2. Environment variables

All variables live in **`backend/.env`** (gitignored; template with comments in
`backend/.env.example`). The six credential fields are the only values you must enter
by hand:

| Variable | Required | Meaning |
|---|---|---|
| `MPESA_ENVIRONMENT` | yes | `sandbox` (default) or `production` |
| `MPESA_CONSUMER_KEY` | yes | Daraja app Consumer Key (secret) |
| `MPESA_CONSUMER_SECRET` | yes | Daraja app Consumer Secret (secret) |
| `MPESA_SHORTCODE` | yes | PayBill / Till number that receives rent |
| `MPESA_PASSKEY` | yes | Lipa na M-Pesa Online Passkey (secret) |
| `MPESA_CALLBACK_URL` | yes | Public HTTPS URL Safaricom posts results to |
| `MPESA_TRANSACTION_TYPE` | no | `CustomerPayBillOnline` (default) or `CustomerBuyGoodsOnline` for Till |
| `MPESA_ACCOUNT_REFERENCE` | no | Reference shown on the prompt/statement, default `PropNoxa` (max 12 chars) |
| `MPESA_TRANSACTION_DESCRIPTION` | no | Prompt text, default `Rent Payment` (max 13 chars) |
| `MPESA_TIMEOUT_SECONDS` | no | HTTP timeout for Daraja calls, default `30` |
| `MPESA_PRODUCTION_ENABLED` | no | Hard safety switch, default `false` — live endpoints stay blocked until `true` (see §10) |
| `MPESA_MAX_AMOUNT` | no | Per-transaction cap in whole KSh, default `250000` |
| `MPESA_INITIATE_LIMIT_PER_HOUR` | no | STK pushes per tenant per hour, default `10` |
| `MPESA_DUPLICATE_WINDOW_SECONDS` | no | How long an unanswered prompt blocks a resend, default `300` |

Never commit real values. `backend/.env` is ignored by git; production credentials
should come from your secrets manager (see `DEPLOYMENT.md` §4).

---

## 3. What to obtain from Safaricom (Daraja portal)

1. Create a free account at [developer.safaricom.co.ke](https://developer.safaricom.co.ke).
2. Create an **App** — this gives you the **Consumer Key** and **Consumer Secret**.
   For sandbox testing you can enable "Lipa Na M-Pesa Sandbox" on any app.
3. Note the sandbox values used by every test account:
   - **Shortcode**: `174379`
   - **Passkey**: published on the Daraja portal under *Lipa Na M-Pesa Online — sandbox*
     (copy the current value from the portal; Safaricom rotates it occasionally).
4. `MPESA_CALLBACK_URL`: you supply this — it must be a publicly reachable HTTPS URL
   ending in `/api/v1/mpesa/callback` (see §5).

For production you additionally need an approved **M-Pesa Business (PayBill or Buy
Goods) shortcode** with its own **Numeric** "Lipa na M-Pesa Online" passkey and a
**production app** on Daraja — see §11.

---

## 4. Sandbox configuration

Edit `backend/.env`:

```bash
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=<your sandbox consumer key>
MPESA_CONSUMER_SECRET=<your sandbox consumer secret>
MPESA_SHORTCODE=174379
MPESA_PASSKEY=<sandbox passkey from the Daraja portal>
MPESA_CALLBACK_URL=https://<your-tunnel-domain>/api/v1/mpesa/callback
MPESA_TRANSACTION_TYPE=CustomerPayBillOnline
MPESA_ACCOUNT_REFERENCE=PropNoxa
MPESA_TRANSACTION_DESCRIPTION=Rent Payment
MPESA_TIMEOUT_SECONDS=30
```

Then verify the app sees the credentials:

```bash
curl -s http://localhost:8000/health/metrics | python -m json.tool
# → "mpesa": {"configured": true, "environment": "sandbox",
#             "production_enabled": false, "missing": []}
```

`configured: false` with a `missing` list = the named variables are absent or empty.
Missing/invalid credentials never take the app down and never affect unrelated
features; they fail the specific M-Pesa call with a clear 503/502 error instead.

---

## 5. Callback URL (public HTTPS + local tunnel)

Safaricom must be able to POST payment results to your API from the internet.
The URL is always `<public-base-url>/api/v1/mpesa/callback` (no auth header — the
callback is validated by checkout match + idempotency, not by the URL being secret).

For **local sandbox testing**, expose your local API with a tunnel:

```bash
# option A: cloudflared
cloudflared tunnel --url http://localhost:8000
# option B: ngrok
ngrok http 8000
```

Copy the generated HTTPS domain into `MPESA_CALLBACK_URL`, e.g.
`https://random-words.trycloudflare.com/api/v1/mpesa/callback`, and restart the
backend. In production this is your real API domain (HTTPS required).

Note: a callback reaching your URL proves nothing on its own — the payload must
match an existing live checkout and is applied exactly once. Unknown/stale callbacks
are rejected (`mpesa.callback.malformed` / unmatched → 400 or no-op) and logged.

---

## 6. Database migration

The integration adds one table (`mpesa_transactions`) via Alembic revision
`0037_mpesa_transactions`. Run:

```bash
cd backend
.venv/Scripts/python.exe -m alembic upgrade head    # Windows
# or: python -m alembic upgrade head                # Linux/macOS
```

Existing payment records and leases are untouched (the migration only creates the new
table and its indexes; a downgrade drops only that table and restores the previous
head). Verify with `alembic current` → `0037_mpesa_transactions (head)`.

---

## 7. Start the stack (Docker Compose)

```bash
# from the repository root
cp backend/.env.example backend/.env      # then fill in the M-Pesa fields (§4)
docker compose up -d --build              # db/redis/backend/frontend
docker compose exec backend python -m alembic upgrade head   # if not run automatically
curl -s http://localhost:8000/health/ready
```

The API runs at `:8000` (docs at `/docs`), the frontend at `http://localhost:5173`.
`/health/live` = process is alive; `/health/ready` = app + database ready;
`/health/metrics` includes the informational `mpesa` block. **Missing M-Pesa
credentials never degrade health** — they are configuration, not an outage.

---

## 8. Sandbox end-to-end test (STK Push → PIN → callback)

Safaricom's sandbox accepts test MSISDNs such as `254708374149`; on those numbers the
sandbox auto-answers the PIN prompt so the full callback flow completes.

1. Log in as a tenant that has an outstanding rent bill
   (tenant portal → **Rent & Utility Payments**).
2. Click **📱 Pay with M-Pesa** on the bill, enter a Safaricom number (for sandbox
   use `254708374149` in `0…` or `+254…` form) and the amount, submit.
3. Watch the modal: it says the request is awaiting the PIN prompt — it will not
   claim success until the server confirms it.
4. Check the outcome:
   - The **M-Pesa Payment Attempts** table on the same page updates
     (`awaiting_callback` → `succeeded`) and shows the M-Pesa receipt number.
   - The bill flips to **PAID** and a receipt is available from the ledger.
   - Managers see the attempt under **Payments → M-Pesa Collections**; owners see it
     under **Financials → M-Pesa Collections & Allocation** (allocated to property,
     unit and lease).

API-level alternative:

```bash
TOKEN=<tenant access token>
curl -s -X POST http://localhost:8000/api/v1/mpesa/stk-push \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"payment_id": 42, "phone_number": "254708374149", "amount": "1200"}'
```

Never initiate real-money transactions while testing; use sandbox credentials only.

---

## 9. Verifying results, callbacks and reconciliation

- **Callback**: Safaricom posts to `/api/v1/mpesa/callback`. Accepted payloads are
  matched to a live checkout and applied once; the attempt is marked `succeeded`
  only with a valid M-Pesa receipt number. Duplicate/replayed callbacks enrich the
  record but never double-credit.
- **Status timeline**: `pending → awaiting_callback → succeeded | failed | cancelled
  | timed_out | expired`; `unknown` means "outcome indeterminate — verify before
  resending" (used for timeouts/5xx after submission).
- **Per-transaction check** (tenant/manager/owner of that bill): tap **Check status**
  in the modal, or:

  ```bash
  curl -s -X POST http://localhost:8000/api/v1/mpesa/transactions/<id>/reconcile \
    -H "Authorization: Bearer $TOKEN"
  ```

  Reconciliation asks Daraja for the true status of the checkout and applies the
  result through the same exactly-once path.

- **Operations sweep** (admin): periodically reconcile stale live attempts — safe to
  run on a schedule (e.g. cron every 5 minutes):

  ```bash
  curl -s -X POST "http://localhost:8000/api/v1/mpesa/reconcile?older_than_minutes=5&limit=50" \
    -H "Authorization: Bearer $ADMIN_TOKEN"
  # → {"checked": n, "updated": n, "still_processing": n, "errors": n}
  ```

- **Audit trail**: initiation, rejection, unconfirmed, callback-applied and
  reconciliation events are written to `audit_logs` (actions
  `MPESA_STK_PUSH_*`, `MPESA_PAYMENT_*`) and covered by the tamper-evident chain.

---

## 10. Switching to production

Prerequisites: everything in §11 done, and the sandbox flow verified end-to-end.

1. Obtain the **production** Daraja app Consumer Key/Secret and the production
   shortcode's **passkey** (from the M-Pesa Business portal — the sandbox passkey
   will not work).
2. Update `backend/.env` (or the secrets manager):

   ```bash
   MPESA_ENVIRONMENT=production
   MPESA_CONSUMER_KEY=<production consumer key>
   MPESA_CONSUMER_SECRET=<production consumer secret>
   MPESA_SHORTCODE=<your approved PayBill or Till number>
   MPESA_PASSKEY=<production passkey>
   MPESA_CALLBACK_URL=https://api.your-domain.com/api/v1/mpesa/callback
   MPESA_TRANSACTION_TYPE=CustomerPayBillOnline   # CustomerBuyGoodsOnline for Till
   MPESA_PRODUCTION_ENABLED=true
   ```

3. Restart the backend and confirm `/health/metrics` → `"environment": "production"`,
   `"production_enabled": true`.
4. Run one small real transaction from a staff handset and verify the callback
   (`succeeded` + receipt in the tenant ledger) before announcing availability.

The `MPESA_PRODUCTION_ENABLED=false` default is a deliberate two-key switch: even if
`MPESA_ENVIRONMENT` is flipped, the service refuses to call live endpoints until the
flag is explicitly set, preventing accidental real charges from a stray env change.

---

## 11. Safaricom onboarding requirements (non-technical, mandatory)

These steps happen with Safaricom Business / your M-Pesa account manager and cannot
be automated from the codebase:

- **M-Pesa Business account** on a PayBill or Buy Goods (Till) shortcode, with the
  business registered (business permit / certificate of incorporation, KRA PIN,
  bank account for settlement).
- **Lipa na M-Pesa Online (STK Push)** enabled on that shortcode, giving you the
  shortcode-specific **production Passkey**.
- **Daraja production app**: promote/create an app under the M-Pesa Business account
  and request **Go-Live** (Safaricom reviews the org details; sandbox apps cannot
  hit production endpoints).
- **Callback URL registered/allowed** — some accounts require whitelisting the
  callback domain during go-live review.
- **Landlord/settlement questions**: rent collected on a single PayBill lands in the
  owner of that shortcode's settlement account. PropNoxa records each collection
  allocated to the correct property/unit/lease/landlord in its own ledger, but the
  money flow (how a landlord gets their share) is handled **outside** PropNoxa —
  via your own settlement/remittance process. Per-landlord sub-accounts or
  split-settlement arrangements must be agreed with Safaricom directly; the
  integration deliberately implements **no B2C payouts or automatic transfers**.
- **Dispute/statement process**: keep the M-Pesa Statement / portal access for the
  shortcode — it is the source of truth for operator-level reconciliation alongside
  PropNoxa's own ledger.

---

## 12. Troubleshooting

| Symptom | Meaning | Action |
|---|---|---|
| UI hides M-Pesa buttons | integration not configured | fill §4 fields, restart backend |
| `503` "M-Pesa is not configured" | same as above (API level) | check the `missing` list in `/health/metrics` |
| `502` "Safaricom rejected the OAuth credentials (HTTP 400/401)" | wrong Consumer Key/Secret for the environment | re-copy credentials; sandbox keys ≠ production keys |
| `502` "HTTP 500/503 … outcome must be confirmed" | Safaricom-side error after submission | do **not** resend; use Check status / reconcile |
| Attempt stuck `awaiting_callback` | tenant didn't enter PIN, or callback unreachable | tenant checks their phone; verify the tunnel/URL; reconcile after `MPESA_DUPLICATE_WINDOW_SECONDS` |
| Attempt `unknown` | timeout/5xx after submission | reconcile — it resolves to the true state |
| `409` duplicate | a live prompt already exists | the UI adopts the existing attempt and watches it |
| Callback 400 | malformed/unmatched payload | check the tunnel forwards POSTs unchanged; look for `mpesa.callback.malformed` in logs |

All errors are intentionally honest: **no path ever reports a payment as successful
without a validated server-side result.**
