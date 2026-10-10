# Security Improvements Documentation

This document details all security improvements made to the Real Estate Management System.

## Overview

Date: October 9, 2026
Scope: Priority 1 and Priority 2 security improvements
Status: 9/10 Priority 1 items complete (CSRF deliberately skipped). All Priority 2 items complete:
email verification, password reset, file upload security, API versioning, monitoring, MFA,
automated backups, CI/CD, frontend tests, and this documentation pass.

---

## Priority 1 Improvements (CRITICAL - COMPLETED)

### 1. ✅ Database Credentials Removed from .env.example

**Files Changed:**
- `backend/.env.example`

**Changes:**
- Replaced actual database password `Muthoni` with placeholder `your-strong-password`
- Replaced SECRET_KEY placeholder with instruction to generate using Python secrets module

**Impact:** Prevents accidental exposure of credentials in version control.

**Deployment Note:** In production, use AWS Secrets Manager, Azure Key Vault, or similar.

---

### 2. ✅ Password Policy Strengthened

**Files Changed:**
- `backend/app/utils/security.py`
- `backend/app/routers/auth.py` (all registration endpoints)

**New Requirements:**
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character
- No common passwords (password, 123456, qwerty, etc.)
- No sequential characters (111, 222, etc.)

**Functions Added:**
- `validate_password_strength(password: str) -> tuple[bool, str]`
- Applied to all registration endpoints (tenant, owner, agent, provider, generic)

**Impact:** Prevents weak passwords that are vulnerable to brute force attacks.

---

### 3. ✅ Rate Limiting Enabled

**Files Changed:**
- `.env`
- `docker-compose.yml`
- `backend/.env.example`
- `backend/app/services/rate_limiter.py`

**Configuration:**
- `RATE_LIMIT_ENABLED=true` (was false)
- `RATE_LIMIT_PER_MINUTE=120` (unchanged)

**Enhanced Rate Limiting:**
- IP-based rate limiting (always applied)
- User-based rate limiting (for authenticated users, 2x the IP limit)
- Uses Redis for distributed rate limiting across API workers

**Impact:** Protects against brute force attacks and API abuse.

**Requirements:** Redis must be running (configured in docker-compose.yml).

---

### 4. ✅ Security Headers Middleware

**Files Changed:**
- `backend/app/middleware/security_headers.py` (new file)
- `backend/app/middleware/__init__.py` (new file)
- `backend/app/main.py`

**Headers Added:**
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` (production) / `SAMEORIGIN` (dev) - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Enables XSS filtering
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer info
- `Permissions-Policy` - Disables geolocation, camera, microphone
- `Strict-Transport-Security` (production only) - Enforces HTTPS
- `Content-Security-Policy` - Controls resource loading
  - Development: Allows inline scripts for debugging
  - Production: Strict policy, no inline scripts

**Impact:** Protects against XSS, clickjacking, and other browser-based attacks.

---

### 5. ✅ Account Lockout After Failed Login Attempts

**Files Changed:**
- `backend/app/services/account_lockout.py` (new file)
- `backend/app/routers/auth.py` (login endpoint)
- `backend/app/routers/admin.py` (admin unlock endpoint)

**Progressive Lockout Strategy:**
- 3 failed attempts: 1 minute lockout
- 5 failed attempts: 5 minute lockout
- 10 failed attempts: 30 minute lockout
- 15 failed attempts: 1 hour lockout
- 20 failed attempts: 24 hour lockout (admin unlock required)

**Features:**
- Tracks failed attempts per email using Redis
- Automatic lockout with countdown message
- Admin endpoint to unlock accounts: `POST /admin/unlock-account`
- Clear failed attempts on successful login

**Impact:** Prevents brute force attacks on user accounts.

**Requirements:** Redis must be running.

---

### 6. ✅ Token Revocation Mechanism

**Files Changed:**
- `backend/app/services/token_revocation.py` (new file)
- `backend/app/auth/jwt.py`
- `backend/app/auth/deps.py`
- `backend/app/routers/auth.py`

**Features:**
- JWT tokens now include JTI (JWT ID) for unique identification
- Token blacklist using Redis
- User-level revocation (logout from all devices)
- Token issued-at timestamp tracking
- Automatic token validation against blacklist

**New Endpoints:**
- `POST /auth/logout-all` - Logout from all devices

**Impact:** Prevents stolen token abuse and allows forced logout.

**Requirements:** Redis must be running.

---

### 7. ✅ Input Sanitization

**Files Changed:**
- `backend/app/utils/sanitization.py` (new file)
- `backend/app/utils/validators.py` (new file)
- `backend/app/schemas/user.py`
- `backend/requirements.txt` (added bleach>=6.0)

**Sanitization Functions:**
- `sanitize_html()` - Escapes HTML to prevent XSS
- `sanitize_string()` - Removes null bytes, limits length
- `sanitize_filename()` - Prevents path traversal
- `sanitize_url()` - Ensures http/https protocol
- `sanitize_email()` - Validates email format
- `detect_xss_attack()` - Detects common XSS patterns
- `sanitize_user_input()` - Comprehensive sanitization

**Applied To:**
- User registration (full_name field)
- Can be extended to other string fields via validators

**Impact:** Prevents XSS attacks and injection vulnerabilities.

---

### 8. ✅ CORS Configuration Secured

**Files Changed:**
- `.env`
- `backend/.env.example`

**Changes:**
- Removed duplicate localhost origins
- Added clear security warnings in comments
- Added production deployment instructions
- Reduced localhost origins for development

**Production Instructions:**
```bash
# Replace with your actual frontend domain
CORS_ORIGINS=https://your-app.com,https://www.your-app.com
```

**Impact:** Prevents CSRF attacks and unauthorized cross-origin requests.

---

### 9. ✅ Production Secrets Generated

**Files Changed:**
- `.env`
- `backend/scripts/generate_secrets.py` (new file)

**Generated Secrets:**
- POSTGRES_PASSWORD: 32-character random string
- SECRET_KEY: 32-character random string

**Secret Generation Script:**
```bash
python backend/scripts/generate_secrets.py
```

**Production Note:** In production, use secrets manager (AWS Secrets Manager, Azure Key Vault, etc.) instead of .env files.

**Impact:** Prevents use of default/placeholder secrets in production.

---

### 10. ⏸️ CSRF Protection (SKIPPED)

**Reason:** CSRF protection is less critical for JWT-based APIs with:
- HttpOnly cookies for refresh tokens
- SameSite cookie attribute set to "lax"
- Security headers middleware
- Token-based authentication

**Decision:** Current implementation provides sufficient CSRF protection.

---

## Priority 2 Improvements (HIGH - COMPLETED)

### 1. ✅ Email Verification Flow

**Files Changed:**
- `backend/app/models/email_verification.py` (new)
- `backend/app/models/user.py` (added relationship)
- `backend/app/models/__init__.py` (import)
- `backend/app/main.py` (import, router)
- `backend/app/services/email_service.py` (new)
- `backend/app/services/email_verification_service.py` (new)
- `backend/app/routers/email_verification.py` (new)
- `backend/app/routers/auth.py` (all registration endpoints)
- `backend/migrations/versions/0029_add_email_verification.py` (new)

**Features:**
- Email verification tokens with 24-hour expiration
- Automatic email sending on registration
- Resend verification email endpoint
- Verification status check endpoint
- Email verification API endpoints

**New Endpoints:**
- `POST /api/email-verification/verify` - Verify email with token
- `POST /api/email-verification/resend` - Resend verification email
- `GET /api/email-verification/status` - Check verification status

**Registration Flow:**
1. User registers
2. Account created with `is_verified=False`
3. Verification email sent automatically
4. User clicks verification link
5. Email verified, `is_verified=True`

**Development Mode:** Emails logged to console (check logs)
**Production Mode:** TODO - Integrate with SendGrid/AWS SES/SMTP

**Migration Required:**
```bash
docker compose run --rm migrate
```

**Impact:** Prevents fake accounts and ensures users have access to their email.

---

## Completed Priority 2 Improvements (continued)

### 2. ✅ Password Reset Flow (COMPLETED)

**Files Changed:**
- `backend/app/models/password_reset.py` (new: PasswordResetToken + PasswordHistory)
- `backend/app/services/password_reset_service.py` (new)
- `backend/app/routers/password_reset.py` (new)
- `backend/app/main.py` (router mount, model imports)
- `backend/app/config/settings.py` (PASSWORD_RESET_TOKEN_EXPIRE_MINUTES, PASSWORD_HISTORY_LIMIT)
- `backend/migrations/versions/0030_password_reset_history.py` (new)
- `backend/tests/test_password_reset.py` (new - 9 tests)

**Features:**
- Forgot-password emails a secure reset link (`email_service.send_password_reset_email`)
- Enumeration-safe: same response whether or not the account exists
- Tokens are single-use and expire after 30 minutes (`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`)
- Only the SHA-256 hash of the token is stored - a DB leak cannot be used to reset passwords
- Password history check: reuse of any of the last 5 passwords (`PASSWORD_HISTORY_LIMIT`) or the current password is rejected on reset AND change
- Authenticated change-password endpoint with the same strength/history rules
- All sessions revoked and failed-login lockout cleared after a successful reset

**New Endpoints:**
- `POST /api/v1/auth/forgot-password` - Request reset email (public)
- `POST /api/v1/auth/reset-password` - Consume token, set new password (public)
- `POST /api/v1/auth/change-password` - Change password while authenticated

**Migration Required:**
```bash
docker compose run --rm migrate   # or: cd backend && alembic upgrade head
```

### 3. ✅ File Upload Security (COMPLETED)

**Files Changed:**
- `backend/app/utils/file_validation.py` (new)
- `backend/app/routers/property_media.py` (upload endpoint)
- `backend/app/main.py` (file serving route, FileResponse import)
- `backend/app/config/settings.py` (UPLOAD_DIR, MAX_UPLOAD_FILE_BYTES, upload_root)
- `backend/requirements.txt` (python-multipart)
- `backend/.gitignore` (uploads/)

**Features:**
- Magic-byte file type validation - client filename and Content-Type are never trusted
- Allowed types: JPEG, PNG, GIF, WebP, PDF; explicit rejection of HTML/XML/SVG/executables
- File size limit enforced (default 10 MB, `MAX_UPLOAD_FILE_BYTES`)
- Random UUID-based storage names (prevents path traversal and filename info leaks)
- Files served back with fixed Content-Type and `nosniff` header

**New Endpoints:**
- `POST /api/v1/properties/{property_id}/media/upload` - Multipart upload (staff only)
- `GET /media/uploads/{stored_name}` - Serve validated upload inline

**Not implemented (documented gaps):**
- Virus scanning (recommend ClamAV integration in production)
- S3/cloud storage and signed URLs (currently local disk; UPLOAD_DIR is swappable)

### 4. ✅ API Versioning (COMPLETED)

**Files Changed:**
- `backend/app/main.py` (all routers mounted under `/api/v1`; versioning middleware)

**Features:**
- Canonical prefix is `/api/v1/`
- Legacy `/api/*` and un-prefixed requests are transparently rewritten to `/api/v1` (no client breakage)
- Legacy responses carry `Deprecation: true`, `Sunset`, and `X-API-Version` headers
- Health, docs, media, and root endpoints are exempt from rewriting/deprecation headers

**Deprecation Policy:**
1. New endpoints are added only under `/api/v1/`.
2. Breaking changes ship as a new version prefix (`/api/v2/`) with both versions live in parallel.
3. Breaking changes are documented in the changelog with migration notes at least 6 months before sunset.
4. Legacy `/api/*` access is scheduled to be removed on **September 1, 2027** (`Sunset` header).

### 5. ✅ Basic Monitoring Setup (COMPLETED)

**Files Changed:**
- `backend/app/observability/metrics.py` (uptime, aggregated counters, error rates, system info)
- `backend/app/main.py` (`/health/metrics` exposes the enriched snapshot)

**Features:**
- Uptime tracking (`uptime_seconds` since process start)
- Aggregate request counter, 4xx/5xx error counters, error-rate percentage
- Per-route/per-status counters and latency duration buckets
- Process memory (RSS) and PID (psutil), app/Python/platform versions
- Structured JSON logs to stdout (12-factor) for log aggregation (CloudWatch/ELK)
- Liveness (`/health/live`) and readiness (`/health/ready`) probes for uptime monitoring
- Upload accept/reject counters wired into file upload security

**New Response Shape (`GET /health/metrics`):**
```json
{
  "counters": { "requests_total": 120, "errors_5xx_total": 0, ... },
  "request_duration_buckets": { ... },
  "process": { "rss_bytes": 94371840, "pid": 2920 },
  "summary": { "uptime_seconds": 312.5, "total_requests": 120, "errors_4xx": 8, "errors_5xx": 0, "error_rate_percent": 0.0 },
  "system": { "app_version": "1.0.0", "python_version": "3.14.6", "platform": "windows" }
}
```

**Production recommendations (external services):**
- APM: Datadog/New Relic can scrape `/health/metrics` or use their Python agents
- Error tracking: add Sentry SDK (`sentry-sdk[fastapi]`) with `SENTRY_DSN`
- Alerting: alert on `error_rate_percent`, readiness probe failures, and uptime checks

### 6. ✅ Multi-Factor Authentication (COMPLETED)

**Files Changed:**
- `backend/app/utils/totp.py` (new: dependency-free RFC 6238 TOTP)
- `backend/app/services/mfa_service.py` (new)
- `backend/app/services/sms_service.py` (new)
- `backend/app/routers/mfa.py` (new)
- `backend/app/models/mfa.py` (new: RecoveryCode + SmsChallenge)
- `backend/app/models/user.py` (`mfa_enabled`, `mfa_secret` + relationships)
- `backend/app/routers/auth.py` (login returns an MFA challenge when enrolled)
- `backend/app/schemas/role_profiles.py` (`AuthLoginResponse` MFA fields)
- `backend/app/main.py` (router mount, model imports)
- `backend/app/config/settings.py` (`MFA_*` settings)
- `backend/migrations/versions/0031_add_mfa.py` (new)
- `backend/tests/test_mfa.py` (new - 8 tests)

**Features:**
- TOTP authenticator apps (Google Authenticator, Authy, 1Password) - `otpauth://` QR provisioning URI
- Implemented from the RFC 6238 spec with the standard library only (HMAC-SHA1, 30s step, ±1 step window, constant-time comparison) - no new dependency
- SMS one-time-code as a backup factor for users with a verified `phone`
- 10 single-use recovery codes (`XXXXX-XXXXX`) generated at enrolment, hashed with SHA-256 before storage
- Two-step login: `POST /api/v1/auth/login` returns `mfa_required` + a short-lived `mfa_token` (`MFA_TOKEN_EXPIRE_MINUTES`, default 5 min) instead of session tokens
- `mfa_token` proves the password only - it is rejected by every normal API endpoint (`get_current_user` accepts only `type == "access"`)
- Optionally enforce MFA for admins: `MFA_MANDATORY_FOR_ADMIN=true` makes admins pass through the challenge (and prompts enrolment if they have no factor yet). Default `false` so existing deployments are not locked out - **enable in production**
- Self-service disable/re-enrol requires a second factor (TOTP code or recovery code); recovery codes can be regenerated

**New Endpoints:**
- `GET  /api/v1/auth/mfa/status` - enrolment state, SMS availability, remaining recovery codes
- `POST /api/v1/auth/mfa/setup` - generate a secret + `otpauth://` URI (not yet enabled)
- `POST /api/v1/auth/mfa/enable` - confirm TOTP code, enable MFA, return recovery codes once
- `POST /api/v1/auth/mfa/disable` - disable with a current TOTP or recovery code
- `POST /api/v1/auth/mfa/recovery-codes/regenerate`
- `POST /api/v1/auth/mfa/send-sms` - issue an SMS challenge (`dev_code` returned in development)
- `POST /api/v1/auth/mfa/verify` - complete the challenge, returns real access + refresh tokens

**Development Mode:** SMS codes are logged to the console. **Production:** TODO - integrate Twilio/Vonage in `sms_service.py`.

**Migration Required:** `docker compose run --rm migrate`

**Impact:** Password compromise alone no longer grants account access.

---

### 7. ✅ Automated Database Backups (COMPLETED)

**Files Changed:**
- `backend/app/services/backup_service.py` (new)
- `backend/scripts/backup_database.py` (new CLI, `--once` / `--daemon` / `--list` / `--verify` / `--prune` / `--status` / `--pitr-plan`)
- `backend/scripts/restore_database.py` (new CLI, dry-run by default)
- `backend/app/config/settings.py` (`BACKUP_*` settings, `backup_root`/`backup_secondary_root`/`backup_wal_archive_root`)
- `docker-compose.yml` (`db-backup` service, WAL archiving on PostgreSQL, `db_backups` + `pg_wal_archive` volumes)
- `backend/Dockerfile` (version-matched `postgresql-client-16`)
- `backend/.gitignore` (`backups/`), `backend/.env.example`
- `backend/tests/test_backup_service.py` (new - 10 tests)

**Features:**
- Daily logical dumps: `pg_dump` on PostgreSQL, SQLite online-backup API on the dev database, gzip-compressed
- **Verification after every write**: SHA-256 checksum sidecar, then the archive is opened and proved
  readable (`PRAGMA integrity_check` + schema/version for SQLite, `pg_restore --list` for Postgres).
  A backup that fails verification raises, so the job is reported as failed instead of quietly kept.
- Retention: `BACKUP_RETENTION_DAYS=30` with a `BACKUP_KEEP_MINIMUM=7` floor so a misconfigured
  clock cannot delete the only recent copies
- Cross-location copy: `BACKUP_SECONDARY_DIR` mirrors each artefact (plus its checksum) to a second
  mount/bucket
- Point-in-time recovery: PostgreSQL runs with `wal_level=replica` + `archive_command` into the
  `pg_wal_archive` volume, physical `pg_basebackup` anchors (`BACKUP_PHYSICAL_ENABLED`) are retained
  (`BACKUP_PHYSICAL_KEEP_COUNT`), and `--pitr-plan <UTC timestamp>` emits the exact
  `restore_command` / `recovery_target_time` configuration to replay up to that instant
- Metrics: `backup_created_total`, `backup_failed_total`, `backup_mirrored_total`, `backup_pruned_total`
  on `/health/metrics`
- Restore is dry-run unless `--confirm`, and always keeps the previous file as `<name>.pre-restore-<stamp>`

**Example (development database):**
```
python scripts/backup_database.py --once
{ "logical": { "name": "propnoxa-20261009T164159Z-logical.sqlite.gz",
               "verified": true,
               "verification_detail": "integrity ok, schema 0031_add_mfa, 1339 user rows" } }
```

**Production checklist:**
- [ ] Set `BACKUP_PHYSICAL_ENABLED=true` (PITR needs base backups, not just logical dumps)
- [ ] Point `BACKUP_SECONDARY_DIR` at a genuinely different failure domain (cross-region bucket/NFS)
- [ ] Ship `/pg_wal_archive` off-host too - WAL on the same disk as the cluster is not a backup
- [ ] Schedule a periodic restore drill into a scratch environment

---

### 8. ✅ CI/CD Pipeline (COMPLETED)

**Files Changed:**
- `.github/workflows/ci.yml` (new)
- `.github/workflows/deploy.yml` (new)
- `scripts/consolidate-backend-git.sh` (new)
- `backend/app/config/settings.py` (`# nosec B104` justification on the intentional 12-factor `HOST` default)

**CI pipeline (GitHub Actions, push/PR to `main`):**
- **Frontend job:** `npm ci` → `tsc --noEmit` → Vitest with coverage (thresholds enforced: 70% lines / 65% functions / 70% branches) → production build → Playwright e2e (Chromium, dev server auto-started by the Playwright config). Coverage, `dist/`, and Playwright failure reports are uploaded as artifacts.
- **Backend job:** Python 3.14, `pip install -r requirements.txt`, `pytest tests -q` (in-memory SQLite via `tests/conftest.py` — no services needed), **bandit at medium+ severity (blocking)**, **pip-audit (advisory)** until requirements are fully pinned.
- **Frontend audit job:** `npm audit --omit=dev --audit-level=high` is **blocking** (production dependencies, currently green); the full dev-inclusive audit runs as **advisory** because the remaining advisories sit in the Vitest/esbuild toolchain and only clear with breaking major upgrades.
- **Docker job:** builds the backend image (no push — no registry configured yet).
- The backend and Docker jobs are gated behind a "backend sources tracked" check (`backend/requirements.txt` present); since the 2026-10-10 consolidation (below) that is always the case, and the gate now only acts as a safety net.

**Deploy workflow (`workflow_dispatch`):** re-runs the full CI via `workflow_call`, then promotes to the chosen GitHub Environment (`staging` or `production`). Protect `production` with required reviewers in *Repo settings → Environments* so a dispatch cannot ship without human approval. The deploy steps themselves are placeholders for the hosting command.

**Backend consolidation (done 2026-10-10):**
The root repository previously tracked `backend/` as a bare gitlink (nested `.git`, no `.gitmodules`), so GitHub saw **no backend files at all** and backend tests, bandit, and Docker builds could not run. This was consolidated by running:
```bash
scripts/consolidate-backend-git.sh   # renames backend/.git aside (history preserved), stages backend/ as normal files, aborts if backend/.env would not stay ignored
git commit -m "Consolidate backend sources into root repository"
git push
```
The nested repository (history + uncommitted state at the time) is preserved as `backend/.git.pre-consolidation`; exact rollback steps are printed by the script.

### 9. ✅ Frontend Tests (COMPLETED)

**Tooling:**
- Vitest + jsdom + Testing Library for unit/component tests (`npm run test`, `npm run test:coverage`)
- Playwright (Chromium) for e2e (`npm run test:e2e`); `playwright.config.ts` starts the Vite dev server itself and honours `E2E_BASE_URL` to reuse a running server
- `vitest.config.ts`: coverage counts only files a test actually loads (`all: false`) so the percentage is meaningful, with enforced thresholds

**Suites (new):**
- Services: `api.test.ts`, `auth.test.ts` (incl. MFA-challenge handling), `mfa.test.ts`
- Contexts: `AuthContext.test.tsx` (role/dashboard mapping, session restore, MFA challenge, logout), `FavoriteContext.test.tsx`
- Components: `MfaPanel.test.tsx` (full enrolment walk, disable gating, recovery codes), `PropertyCard.test.tsx` (formatting, favourites, role gating), `StatCard.test.tsx`, `Pagination.test.tsx`
- Utils: `propertyImages.test.ts` (Pexels fallbacks/caching), `propertyLocation.test.ts`, `validation.test.ts`
- E2E: `e2e/smoke.spec.ts` (home, local login validation before any network call, password toggle, admin-route guard); `e2e/mfa-login.spec.ts` (opt-in real TOTP journey via `E2E_MFA_EMAIL` / `E2E_MFA_PASSWORD` / `E2E_MFA_SECRET`, with `e2e/support/totp.ts` mirroring the backend's RFC 6238 implementation)

**Results:** 88 unit/component tests passing; coverage 85.5% lines / 80.1% branches / 76.4% functions (thresholds 70/65/70); 4 smoke e2e tests passing.

**Real bugs the tests surfaced and fixed:**
- `PropertyCard`'s media container was `aria-hidden="true"`, which removed the Save/favourite button from the accessibility tree — removed (the photo is a CSS background, nothing needed hiding).
- `Login.tsx` never rendered the email-field validation error (only the password one) — fixed.

---

## Security Documentation

### 10. ✅ Comprehensive Security Documentation (COMPLETED)

**Status:** Complete — this document now covers every Priority 1 and Priority 2 item, environment
variables, testing checklist, known limitations, and changelog.

---

## Environment Variables

### New Variables
```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=120

# File uploads
UPLOAD_DIR=uploads/property_media   # relative to backend/, or absolute path
MAX_UPLOAD_FILE_BYTES=10485760       # 10 MB per file
DOCUMENTS_DIR=uploads/documents      # generated lease/invoice PDFs (gitignored)

# Password reset
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
PASSWORD_HISTORY_LIMIT=5

# Multi-factor authentication
MFA_ISSUER_NAME=PropNoxa              # shown in the authenticator app
MFA_TOKEN_EXPIRE_MINUTES=5            # lifetime of the login challenge token
MFA_SMS_CODE_EXPIRE_MINUTES=5
MFA_RECOVERY_CODE_COUNT=10
MFA_MANDATORY_FOR_ADMIN=false         # set TRUE in production to enforce admin MFA

# Database backups
BACKUP_DIR=backups/database
BACKUP_RETENTION_DAYS=30
BACKUP_KEEP_MINIMUM=7
BACKUP_INTERVAL_HOURS=24
BACKUP_VERIFY_AFTER_CREATE=true
BACKUP_PHYSICAL_ENABLED=false         # set TRUE in production (PITR base backups)
BACKUP_PHYSICAL_KEEP_COUNT=4
BACKUP_SECONDARY_DIR=                 # mirror target, e.g. a mounted cross-region bucket
BACKUP_WAL_ARCHIVE_DIR=               # WAL archive used by point-in-time recovery

# CORS (updated with security warnings)
CORS_ORIGINS=http://localhost:5173

# Frontend E2E (optional - opts the MFA login journey into Playwright runs)
E2E_BASE_URL=            # reuse an already-running dev server instead of auto-starting one
E2E_MFA_EMAIL=           # account with TOTP enrolled
E2E_MFA_PASSWORD=
E2E_MFA_SECRET=          # base32 TOTP secret for the account

# Data retention (GDPR storage limitation)
LEGAL_HOLD_ENABLED=false             # true suspends purges of business records (litigation hold)
RETENTION_TOKEN_GRACE_DAYS=30        # purge expired/used one-time tokens after this many days
RETENTION_AUDIT_LOG_DAYS=365         # prune audit logs older than this (0 = keep forever)
RETENTION_NOTIFICATIONS_DAYS=180     # prune read notifications; unread get 2x the window
```

### Required for Production
```bash
# Secrets (use secrets manager)
POSTGRES_PASSWORD=<strong-random-password>
SECRET_KEY=<strong-random-secret-min-32-chars>
AUDIT_CHAIN_SECRET=<strong-random-secret>  # optional; defaults to SECRET_KEY; write-once (rotating breaks chain verification)

# CORS (production domains only)
CORS_ORIGINS=https://your-app.com,https://www.your-app.com

# Redis (for rate limiting, account lockout, token revocation)
REDIS_URL=redis://redis:6379/0
```

---

## Dependencies Added

```txt
bleach>=6.0  # HTML sanitization
python-multipart  # Multipart file uploads
psutil>=5.9  # Process memory metrics (also now actually installed in the venv)
fpdf2>=2.8  # PDF generation (leases, invoices)
```

Frontend dev tooling (package.json devDependencies): `vitest`, `@vitest/coverage-v8`, `jsdom`,
`@testing-library/react`/`jest-dom`/`user-event`, `@playwright/test`. CI-only scanners: `bandit`,
`pip-audit` (installed per-run in the workflow, not added to requirements.txt).

---

## Migration Required

New migrations: `0029_add_email_verification`, `0030_password_reset_history`, `0031_add_mfa`.

```bash
# Apply migration
docker compose run --rm migrate

# Or manually
cd backend
alembic upgrade head
```

---

## Testing Checklist

Before deploying to production:

- [ ] Test password policy with weak passwords (should fail)
- [ ] Test password policy with strong passwords (should succeed)
- [ ] Test rate limiting (should block after 120 requests/minute)
- [ ] Test account lockout (should lock after 3 failed attempts)
- [ ] Test admin account unlock endpoint
- [ ] Test token revocation (logout from all devices)
- [ ] Test security headers (check response headers in browser dev tools)
- [ ] Test email verification flow
- [ ] Test XSS attack prevention (try malicious input)
- [ ] Verify Redis is running for distributed features
- [ ] Verify all security headers are present
- [ ] Test CORS with production domain

---

## Security Headers Verification

Use browser DevTools to verify security headers:

```bash
# In Network tab, check response headers for:
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()
Content-Security-Policy: ...
```

---

## Monitoring Recommendations

### Log Events to Monitor

Structured security events are emitted on the dedicated `security` logger — filter on `logger == "security"` and query the `security.event` field. Fields per event: `event`, `outcome`, `ip`, `user_id`, `actor` (attempted email), `path`, `request_id`, `details`. Passwords, tokens, and codes are never logged.

| Event | Meaning |
|---|---|
| `auth.login_failed` | Wrong credentials for an existing or unknown account |
| `auth.login_locked` | Login attempt against a lockout-suspended account |
| `auth.login_suspended` | Valid credentials on a deactivated account |
| `auth.login_success` | Full session issued (severity info) |
| `auth.mfa_challenge_issued` | Password accepted, second factor now required (info) |
| `auth.mfa_failed` | Second factor rejected or mfa_token invalid |
| `auth.password_reset_requested` | Forgot-password endpoint hit (info; no enumeration signal in the response) |
| `auth.password_reset_delivery_failed` | Reset email could not be sent (type only, no relay data) |
| `auth.password_reset_rejected` | Reset token invalid/expired/reused |
| `auth.password_reset_completed` | Password actually changed (info) |

HTTP-layer signals (from the request log, same JSON stream): every 4xx logs at warning and every 5xx at error with `method`, `path`, `client`, `status`, `duration_ms`, and `request_id` — which covers authorization-denied spikes and error budgets without per-endpoint code.

### Metrics to Track
- Failed login rate per IP
- Account lockout rate
- Token revocation rate
- XSS attempt rate
- Rate limit violations
- Email verification success rate

---

## Best Practices

### For Development
1. Use the generated secrets in `.env`
2. Keep `RATE_LIMIT_ENABLED=true` for testing
3. Check console logs for verification emails
4. Test security features before committing

### For Production
1. Use secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
2. Set `CORS_ORIGINS` to actual production domains only
3. Enable HTTPS with reverse proxy (nginx/traefik)
4. Integrate actual email service (SendGrid, AWS SES)
5. Enable monitoring and alerting
6. Regularly rotate secrets (every 90 days)
7. Review security logs regularly
8. Keep dependencies updated

### Secrets Rotation
```bash
# Generate new secrets
python backend/scripts/generate_secrets.py

# Update .env with new secrets
# Restart services
docker compose restart
```

---

## Email Notifications (COMPLETED)

Priority 3 item #22 — SMTP transport, templates, transactional emails, per-user preferences.

### Transport (`EMAIL_BACKEND` setting, no new dependencies)

- `console` (default): logs the email instead of delivering it — safe for dev/tests, keeps 12-factor dev/prod parity (same code, different env).
- `smtp`: delivers via stdlib `smtplib` with STARTTLS, optional login, configurable host/port/timeout — works with SES/Mailgun SMTP relays, Mailhog, or Gmail. Startup fails fast if `EMAIL_BACKEND=smtp` is set without `SMTP_HOST`. Delivery failures are logged and return `False`; callers never crash.
- Credentials documented in `.env.example`; production must inject `SMTP_PASSWORD` from a secrets manager.

### Templates (`app/services/email_templates.py`)

- Stdlib `string.Template` rendering (no jinja dependency): every template has subject + HTML (branded multipart layout with call-to-action button) + plain-text alternative.
- User-derived values (names, messages) are HTML-escaped in the HTML part only; the text part keeps raw values. Unknown template names raise immediately.
- Templates: `verify_email`, `password_reset`, `notification`. Verification and password-reset flows now render real emails through the same pipeline.

### Per-user email preferences (migration 0033)

- `GET/PUT /api/v1/notifications/email-preferences` — single `notifications_enabled` opt-out toggle; no row means opted in.
- **Only in-app notification fan-out is gated.** Security/account emails (verification, password reset, deletion receipts) are always sent.
- Fan-out lives in `create_notification`: every in-app notification (payments, leases, maintenance, inquiries, ...) also emails the recipient when opted in. Best-effort — delivery errors never lose the in-app notification.
- UI: toggle on the tenant Profile page ("Email Notifications" card).

### Tests

- 12 backend tests (`tests/test_email.py`): template rendering + XSS escaping, unknown-template raise, console transport logging, SMTP delivery (multipart parsed, TLS + login asserted), SMTP failure returns False, preferences API (401 / default opt-in / opt-out persists), fan-out respects opt-out, fan-out swallows delivery errors. Live API verified: default true → PUT false → GET false → 401 unauthenticated.

---

## GDPR Compliance (COMPLETED)

Priority 3 item #26 — cookie consent, data export, right to erasure, privacy policy.

### Consent log (`consent_records`, migration 0032)

- `POST /api/v1/privacy/consent` records **both grants and refusals** for `cookie_analytics`, `cookie_marketing`, and `tos` — the log must prove consent was *asked*, not just given (GDPR Art. 7(1)).
- Works for anonymous visitors (via a random `client_id` in localStorage) and authenticated users (`user_id` FK, SET NULL on erasure).
- Append-only: every answer is a new row with policy version, IP, and user agent; nothing is updated in place.
- Frontend: `CookieConsent` banner (accept all / essential only / per-category customise), re-openable from `/privacy` via the `pn-open-consent` window event; footer "Privacy" placeholder replaced with a real policy page.

### Data export (Art. 15 / 20)

- `GET /api/v1/privacy/export` returns a JSON attachment with the user's profile (secrets like `hashed_password` / `mfa_secret` replaced by `[REDACTED]`) plus favorites, notifications, and consent records.

### Right to erasure (Art. 17)

- Self-service: `POST /privacy/delete-request` (idempotent, 202), `GET` to view status, `DELETE` to cancel while pending.
- Admin workflow: queue at `GET /privacy/admin/deletion-requests`, then `execute` or `decline` (with notes) — **no user is erased without admin approval**.
- Execution is **anonymize-not-delete** (Art. 17(3)(b): legal obligation to keep financial/lease/audit records): identity fields are replaced (`Deleted User`, `deleted+{id}@anonymized.invalid`), credentials/MFA/auth tokens/password history/recovery data are destroyed, favorites and notifications are removed, and the account is deactivated — while lease, payment, application, and audit rows keep their referential integrity.
- Deleting the user row entirely (e.g. by an admin direct DB action) no longer breaks the audit trail: `data_deletion_requests.user_id` is nullable with ON DELETE SET NULL, and executing such an orphaned request is declined gracefully.

### Admin UI & tenant UI

- Admin portal: "Deletion Requests" page (approve/decline with notes, confirm dialogs).
- Tenant profile: "Privacy & Your Data" card — export download, deletion request/cancel with pending notice.

### Tests

- 9 backend tests (`tests/test_privacy.py`): auth required, redaction, consent anonymous+authenticated, unknown consent type 422, deletion lifecycle + idempotency + cancel, non-admin 403, full admin execution (anonymized fields verified, old password no longer logs in), decline with notes, orphaned-request handling.
- 6 frontend tests for the consent banner (persistence, refusal recording, per-category customise, re-open event). Note: under Node 24 + vitest, `window.localStorage` is undefined in jsdom, so the tests install an in-memory Storage mock.

### Migration note (pre-existing debt, not caused by 0032)

The pre-existing chain contains a **Postgres-only migration** (`ALTER TABLE leases ALTER COLUMN notes TYPE VARCHAR(500)`) that fails on SQLite, so `alembic upgrade head` cannot run end-to-end on a SQLite dev DB. New migrations are validated in isolation: on a fresh scratch DB, `alembic stamp 0031_add_mfa` followed by `upgrade head` / `downgrade -1`.

---

## Document Generation (COMPLETED)

Priority 3 item #24 — PDF lease agreements and payment invoices, cached storage, authenticated delivery.

### PDF builders (`app/services/document_service.py`)

- `fpdf2` (new dependency, pure Python) renders a branded lease agreement (`generate_lease_pdf`) and a payment invoice (`generate_invoice_pdf`): teal header rule, per-page footer, label/value tables, standard-terms paragraph, and a landlord/tenant signature block.
- All text passes through a latin-1 sanitizer (core PDF fonts cannot encode beyond latin-1; anything else is substituted, never crashes).
- The signature block carries an explicit disclaimer that the PDF is **not electronically signed** — PropNoxa records intent via platform events; legally binding e-signature requires a qualified provider (e.g. DocuSign).

### Storage & caching

- Generated PDFs are written under `DOCUMENTS_DIR` (default `uploads/documents`, gitignored, resolved against the backend root like `UPLOAD_DIR`).
- `cached_pdf()` keys files by `{kind}-{entity_id}-{updated_at stamp}`: unchanged entities are served from cache, edits regenerate the file, and stale artifacts for the same entity are pruned.
- Documents are **served only through authenticated endpoints** — never from a static mount.

### Endpoints (mirror the existing read authz)

- `GET /api/v1/leases/{lease_id}/document` — tenant (own lease), admin, or property owner/manager (`can_manage_lease`).
- `GET /api/v1/payments/{payment_id}/invoice` — tenant (own payment), admin, or property owner/manager (`can_manage_payment`).
- Both return `application/pdf` with an `attachment` Content-Disposition; unknown ids 404; everyone else 403.

### Tests

- 11 backend tests (`tests/test_documents.py`): both PDF builders (incl. non-latin text), cache reuse per stamp, cache regeneration + stale pruning, unauthenticated 401, tenant downloads own lease, other tenant 403, admin invoice download, other tenant invoice 403, missing document 404. Full suite: 105 passed / 1 skipped.

---

## Data Retention (COMPLETED)

Storage limitation per GDPR Art. 5(1)(e): expired artifacts are deleted on a schedule instead of accumulating forever.

### Retention jobs (`app/services/retention_service.py`)

| Data class | Rule | Gate |
|---|---|---|
| Ephemeral auth tokens (password resets, email verifications, SMS challenges) | Purged `RETENTION_TOKEN_GRACE_DAYS` (30) after expiry or use | Always runs — no evidentiary value, keeping them is a liability |
| Audit logs | Pruned after `RETENTION_AUDIT_LOG_DAYS` (365); `0` disables pruning | Suspended by legal hold |
| Notifications | Read ones after `RETENTION_NOTIFICATIONS_DAYS` (180); unread after 2× the window | Suspended by legal hold |

- `LEGAL_HOLD_ENABLED=true` suspends destructive purges of business records (litigation hold); ephemeral token cleanup still runs.
- Consent records are never auto-deleted — they are the Art. 7 proof of lawful processing. Leases/payments are never auto-deleted either; GDPR erasure anonymizes the user record instead (see GDPR section).

### Triggering

- `POST /api/v1/admin/retention/run` (admin only) — runs all jobs, returns the report, and writes a `RETENTION_RUN` audit entry with counts.
- `python scripts/run_retention.py` — standalone CLI for cron/scheduler in production; exits non-zero on failure.

No schema change: the jobs operate on existing tables, so no new Alembic migration is required.

### Tests

- 10 backend tests (`tests/test_retention.py`): expired + stale-used token purging with grace window (fresh tokens survive), purging under legal hold, audit-log pruning and `0`-disable, notification read/unread windows, legal hold suspending business-record purges, `RETENTION_RUN` audit trail, endpoint 401/403/admin-report. Full suite: 115 passed / 1 skipped.

---

## Comprehensive Logging (COMPLETED)

Priority 3 item #27 — the structured JSON stream now covers security events, request correlation, and bounded file output.

### Security event stream (`app/services/security_events.py`)

- `emit_security_event(name, request=..., user_id=..., actor=..., outcome=..., severity=..., details=...)` writes to the dedicated `security` logger as one JSON object: `event`, `outcome`, `ip` (honours `X-Forwarded-For` first hop), `user_id`, `actor`, `path`, `request_id`, `details`. Never logs secrets; exception types only, never exception text.
- Wired into: login (failed / locked / suspended / success), MFA challenge issued and MFA verification failures, password reset (requested / delivery failed / rejected / completed). See "Log Events to Monitor" above for the catalogue.

### Request correlation (`app/main.py`)

- Every request gets a `request_id` (incoming `X-Request-ID` echoed when it matches `^[A-Za-z0-9_-]{8,64}$`, otherwise generated) and returns it via the `X-Request-ID` response header — ties a browser report, a log line, and a security event to one request.
- Request log lines now carry `status` and `duration_ms`; 4xx logs at warning, 5xx at error, everything else stays debug.

### Log retention & output

- Production: 12-factor stdout captured by the platform (Docker/K8s/cloud logging), which owns retention — see the `LOG_*` variables in `.env.example`.
- Non-container dev: `LOG_TO_FILE=true` + `LOG_FILE_PATH=...` mirrors the stream to a size-rotated file (5 × 10 MB) so retention stays bounded.
- In-database security records follow the retention policy from the Data Retention section (audit logs 365 days, `LEGAL_HOLD_ENABLED` suspends).

### Tests

- 11 backend tests (`tests/test_security_logging.py`): event payload structure (and no secrets in it), JSON formatter passthrough of `security` and request fields, failed/successful login events, MFA failure event, password-reset requested/rejected events, `X-Request-ID` generated, echoed, malformed-input rejection.

---

## Performance Optimization (COMPLETED)

Priority 3 item #25 — Redis cache-aside, optional read-replica routing, and immutable media caching.

### Redis cache-aside (`app/services/cache_service.py`)

- Public property endpoints (`GET /properties` list, public detail, market insights) are served from Redis when warm; every mutating property/media operation calls `invalidate_property_cache()` so stale entries never survive a write.
- Absent or broken Redis degrades to passthrough — every request hits the database exactly as before, no errors surfaced to clients. Latency-wise Redis is a bonus, never a dependency.
- Keys are versioned (`props:v1:...`) so a format change invalidates everything by bumping the version, and JSON payloads share the settings-driven `REDIS_URL`.

### Read replica routing (`DATABASE_REPLICA_URL`, `get_read_db`)

- `app/database/database.py` builds a separate replica engine when `DATABASE_REPLICA_URL` is set; unset, reads fall back to the primary and nothing changes.
- Public read endpoints (property list/detail/meta/insights) use the `get_read_db` dependency; writes keep using the primary session.

### Immutable media caching

- Property media responses send `Cache-Control: public, max-age=31536000, immutable` — filenames are content-addressed, so browsers and CDNs cache assets forever with zero revalidation requests.

### Notes

- Connection-pool tuning (`DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_STATEMENT_TIMEOUT_MS`) was already in place via `.env.example`.
- Image thumbnailing is intentionally deferred (would add a Pillow dependency); immutable caching gives most of the browser-side win.

### Tests

- 7 backend tests (`tests/test_cache.py`): key generation shape, in-memory fake-Redis cache-aside flow, broken-Redis passthrough, invalidation clearing list/detail/insight keys, and an end-to-end admin test asserting the list endpoint populates and serves the cache.

---

## Payment Gateway (COMPLETED)

Priority 3 item #21 — pluggable gateway abstraction with a fully working in-process mock for development/tests, HMAC-verified webhooks, and admin reconciliation. Real providers (Stripe/PayPal/M-Pesa) slot in behind the same interface without schema or flow changes.

### Gateway abstraction (`app/services/payment_gateway_service.py`)

- `get_gateway()` resolves `settings.PAYMENT_GATEWAY` through a registry: `mock` (fully working) or `stripe`/`paypal`/`mpesa` (fail-closed stubs that raise until provider credentials are configured — from a secrets manager, never `.env` in production).
- The mock gateway is rejected outright in production (`is_production` check) so dev convenience can never handle real money.
- Webhook signatures use HMAC-SHA256 (`X-Webhook-Signature: sha256=<hex>`) verified with `hmac.compare_digest`; verification reads `PAYMENT_WEBHOOK_SECRET` at call time so tests can monkeypatch it.

### Charge + webhook endpoints (`app/routers/payments.py`)

- `POST /payments/{id}/gateway/charge` (admin/manager with `can_manage_payment` on the property): creates a gateway charge and stores the provider transaction ID in `payment.reference` + provider name in `payment_method` — reuses existing columns, no migration needed. 409 if the payment is already paid.
- `POST /payments/webhooks/{provider}`: fails closed (400 + security event `payment.webhook.bad_signature`) on invalid signatures; never errors after successful verification (providers stop retrying on 5xx, so post-verification errors are swallowed and logged); idempotent status transitions (a replayed `payment.succeeded` never double-applies); unmatched transaction IDs return `{"matched": false}` with 200.

### Reconciliation (`POST /admin/payments/reconcile`)

- Admin-only job that re-checks pending payments carrying a gateway reference against the provider and promotes them to paid/failed — never downgrades already-paid payments. Audited as `PAYMENT_RECONCILIATION_RUN`.
- The real dev flow "charge → mock stays processing → webhook/reconcile resolves it" mirrors exactly how Stripe's async payments settle, so swapping providers is a settings change.

### Tests

- 10 backend tests (`tests/test_payment_gateway.py`): charge reference persistence, tenant 403 on charge, 409 on double-charge, webhook marks paid + idempotent replay, bad-signature 400 with status unchanged, unknown transaction ignored, failure event marks failed, reconciliation syncs stale pending payments, reconciliation requires admin, and unconfigured stripe fails closed.

---

## SMS Notifications (COMPLETED)

Priority 3 item #23 — pluggable SMS transport behind `SMS_BACKEND`, wired into the notification fan-out for high-priority events and reused by MFA backup codes.

### Transport selection (`app/services/sms_service.py`)

- `console` (default): logs the message instead of delivering — safe for dev/tests, mirrors the email backend's console mode. `twilio`: fails closed with an actionable error until `TWILIO_ACCOUNT_SID`/`TWILIO_AUTH_TOKEN`/`TWILIO_FROM_NUMBER` are configured (from a secrets manager, never `.env` in production). Unknown backends also fail closed, and settings validation rejects them at startup.
- `send_message(phone, message)` never raises and truncates bodies at 1600 chars (Twilio's hard limit); the existing `sms_service.send_otp` signature is preserved, so MFA SMS challenges work unchanged through the new transport.

### High-priority fan-out (`app/repositories/notification_repo.py`)

- Notifications with `HIGH`/`CRITICAL` priority are fanned out to the recipient's phone when one is on file (`users.phone`, no migration needed) — ordinary in-app traffic never pages a phone, keeping per-message costs bounded.
- Best-effort like the email fan-out: delivery failures log a warning and never break notification creation.

### Tests

- 10 backend tests (`tests/test_sms.py`): console logging, OTP message format (code + expiry), missing phone/body rejection, twilio fail-closed, unknown backend fail-closed, message truncation, HIGH-priority SMS fan-out, NORMAL priority skip, no-phone skip, and fan-out failure never breaking notification creation.

---

## Permission Granularity (COMPLETED)

Priority 3 item #28 — a fine-grained permission vocabulary layered on top of the existing role system, without a migration or a rip-up of the working `verify_role` checks.

### Registry (`app/auth/permissions.py`)

- `PERMISSION_CATALOG` defines the `domain:action` vocabulary (12 permissions from `properties:read` to `admin:system`); `ROLE_PERMISSIONS` maps each of the 7 roles to its default grants. Admin always holds everything — including via `roles_csv` delegation.
- `user_permissions(user)` unions grants across the primary role and `roles_csv` (multi-role users work today, no schema change); `user_can(user, permission)` is the single check; `unknown_permissions()` is a drift guard asserting nothing references a permission outside the catalog.
- Resource-level scoping (company match, ownership, tenant-owns-record) is unchanged — this layer answers "may this user class do this kind of action at all", the existing helpers in `app/auth/roles.py` still answer "and is it *this* record".

### Enforcement + introspection

- `require_permission("payments:write")` dependency factory in `app/auth/roles.py` mirrors `require_role` (re-checks the DB user, rejects suspended accounts, 403 with the missing permission named).
- `GET /auth/me/permissions` returns the caller's effective roles + permissions so the frontend can gate UI without hardcoding role logic.
- `GET /admin/permissions/catalog` (gated by `require_permission("users:manage")` — the first endpoint using the new dependency) returns the full vocabulary and per-role grants for admin tooling.

### Tests

- 12 backend tests (`tests/test_permissions.py`): admin catalog completeness, manager/tenant/fresh-user grant sets, `roles_csv` union and delegated admin, unknown-role safety, roles listing, catalog drift guard, the self-service endpoint, auth requirement, and the admin catalog endpoint's permission gate (200 for admin, 403 for tenant).

---

## Mobile Responsiveness Audit (COMPLETED)

Priority 3 item #29 — audit of the hand-rolled utility CSS against the Tailwind-style classes the components actually use, plus targeted fixes for every gap found.

### Findings

- Solid foundations already in place: viewport meta tag present, portal sidebars hidden below 800px, all wide data tables wrapped in `overflow-x: auto` scroll containers (`.table-container`, `.admin-table-container`), modals width-capped with overlay padding, admin tables/cards/filters with their own breakpoints, `prefers-reduced-motion` respected.
- Real gap: components use Tailwind mobile-first idioms (`grid-cols-1 sm:grid-cols-2 md:grid-cols-3`, `flex-col sm:flex-row sm:items-center`, `md:col-span-2`, `md:self-auto`, `sm:p-8`) but 8 of those breakpoint utilities had **no CSS definition at all** — silently no-op: `sm:grid-cols-3` (3 uses), `md:grid-cols-3` (5), `md:col-span-2` (2), `sm:items-center` (20), `sm:items-end`, `sm:flex-col`, `md:self-auto` (2 each), `sm:p-8` (2). Multi-column grids that were supposed to be 3-up rendered 1-up, and page-header rows lost their alignment.

### Fixes (`src/styles.css`)

- Added the missing base utilities (desktop values), following the file's existing convention, and extended the single `max-width: 900px` collapse block so each behaves mobile-first at small widths: 3-col grids collapse to stacked, `md:col-span-2` resets to span 1, `sm:items-center` returns to stretch (full-width stacked headers), `md:self-auto` returns to `flex-start`, `sm:p-8` returns to the 1.5rem phone padding, and `sm:flex-col`/`sm:items-end` restore their row/center mobile pairing.
- Verified in-browser via CSSOM inspection and computed-style probes: every new selector resolves with the correct desktop value above 900px and the correct collapsed value at or below it.

### Out of scope (noted, not fixed)

- A handful of `hover:bg-*`/`focus:ring-2` variants used by components are undefined — hover/focus styling is progressive enhancement and irrelevant on touch devices, so they were left for a future polish pass.

### Tests

- Frontend suite re-run after the CSS changes: 94 tests across 13 files, all passing (CSS is not unit-tested; the suite confirms no component regressions).

---

## Dark Mode Across All Portals (COMPLETED)

Priority 4 item #31 — full dark theme for the public site and all six role portals, with light/dark/system preference, OS-preference following, persistence, and no flash of the wrong theme on load.

### Theme system (`src/contexts/ThemeContext.tsx`, `src/components/ThemeToggle.tsx`)

- `ThemeProvider` (mounted in `main.tsx` around the router): preference is `light | dark | system`, persisted to `localStorage` under `propnoxa-theme`; `system` resolves via `matchMedia('(prefers-color-scheme: dark)')` and live-updates when the OS changes (the change listener is attached only while in system mode). The resolved theme is applied as `data-theme` on `<html>`.
- `ThemeToggle` cycles light → dark → system with distinct icons, an accessible name that describes the next state, and a `data-theme-preference` attribute for styling/tests; placed in the public navbar and all six portal headers.
- Anti-FOUC: an inline script in `index.html` reads the stored preference before first paint, resolves the system preference, and sets `data-theme` immediately; two `theme-color` metas (light/dark) keep mobile browser chrome in sync.

### CSS strategy (`src/styles.css`, `Home.css` variables)

- Every hardcoded color in the app shell was converted to semantic custom properties so the light theme renders pixel-identical; the dark palette is layered exclusively via `html[data-theme="dark"]`-prefixed rules, whose specificity beats both `:root` and the utility classes regardless of stylesheet bundle order (styles.css vs Home.css vs component CSS).
- Dark overrides cover: the base palette and `--pn-*` marketplace variables, body/page gradients, the full Tailwind-style utility layer used by portal JSX (background/text/border/hover/divide/shadow variants), status and priority chips, portal page chrome, public nav/footer, property cards, forms/inputs, skeletons, and marketplace grid states. The role sidebars keep their dark gradients in both themes.
- `color-scheme` is declared per theme so native controls (scrollbars, form widgets, date pickers) match.

### Verification

- Browser sweep on the dev server: home page top-to-bottom in dark (hero, highlights, featured cards, locations, intelligence, how-it-works, CTA, footer), cookie consent banner, `/login`, and the admin portal (dashboard stats + users table). Computed styles on the users table confirmed dark table headers `#182236`, inputs `#0f1728`, cards `#131c2e`, and body text `#e2e8f0`.
- Live toggle cycling dark → system → light → dark with no reload; light theme verified identical to the pre-change design.

### Tests

- 15 new frontend tests in 2 files: `ThemeContext.test.tsx` (12) — system resolution both ways, live OS-change following with listener attach/detach when leaving and re-entering system mode, stored-preference restore including invalid values, persistence of explicit choices, missing-`matchMedia` fallback, storage access throwing, `useTheme` outside provider; `ThemeToggle.test.tsx` (3) — full cycle incl. accessible names, `data-theme` application, stored-dark boot, className merge.
- Full frontend suite: 109 tests across 15 files green; `npm run typecheck` and `npm run build` clean.

---

## AI Property Matching Engine (COMPLETED)

Priority 4 item #35 — a deterministic, fully explainable matchmaker: every score can be traced to the criteria that produced it, no black-box model, no external ML dependency.

### Scoring engine (`app/services/matching_service.py`)

- Weighted factor model (100 points): Budget 25, Location 20, Size 15, Type 10, Amenities 10, Quality 10, Furnishing 5, Freshness 5. Factors whose criteria are absent are removed from **both earned and available points**, so blank fields never penalize a listing — the final score is `earned / available × 100`.
- Budget: free-text prices ("KSh 45,000/Month", "45k", "1.2M") parsed via regex; ratio to `max_budget` grades 1.0 / 0.6 / 0.25 at the 1.15× soft cap, and listings **above 1.3× are excluded from results entirely** — a hard cap so "match" never means "unaffordable".
- Location: city exact match full credit; county/sub_location/address/landmark overlap partial (0.6).
- Size: `min_bedrooms` and/or `household_size` fraction (household ≤2→1 bed, ≤4→2, else 3), ratio-capped at 1.0.
- Type: synonym groups (apartment: flat/studio/penthouse/loft; house: villa/bungalow/townhouse/maisonette/duplex; commercial: office/shop/retail/warehouse/godown; land: plot/acre) matched by token intersection or substring.
- Amenities: `require_parking` / `require_security` / `require_balcony` flags plus a free-text amenity list (all-words-in-tokens match, capped at 6); fraction = met/total. Furnishing: exact / contains (0.5) / none. Quality: verified 0.6 + image 0.2 + description ≥80 chars 0.2. Freshness: ≤14d / ≤45d / ≤90d / older graded against `as_utc()`-normalized timestamps.
- Labels at ≥85 "Excellent match", ≥70 "Strong match", ≥55 "Good match", else "Possible match". Human-readable reasons are generated per met factor (e.g. "Within your budget (KES 85,000/month)", "✓ Verified listing").

### Explainability payload

- Every result carries `match_label` and `score_breakdown` — the per-factor point contribution, rounded with drift adjustment on the largest factor so the breakdown **sums exactly to the score** (verified live: 63 = Budget 26 + Size 16 + Type 11 + Quality 6 + Freshness 4).
- Ranking is `(score, is_verified, created_at)` descending, so ties break deterministically toward verified, fresher listings.

### Bug fix found along the way

- `PropertyMatchRequest` silently dropped `city`, `max_price` and `amenities` (Pydantic ignores extras by default), so legacy callers were matching on accidental criteria only. Fixed with `validation_alias=AliasChoices(...)` — `max_budget`/`max_price` and `preferred_city`/`city`/`location` are now equivalent, and free-text `amenities` is accepted.

### Endpoint

- `POST /properties/match` + `/public/match` rebuilt on the engine with a bounded `limit` query parameter (1–50, default 20; 100 → 422). Replaces the old ad-hoc inline calculator in the router.

### Frontend (`SmartMatchModal`)

- Results now show the label chip, the top-4 positive score factors as chips ("Budget +25"), and the generated reasons; zero-value factors are filtered from the UI.

### Tests

- 18 new backend tests (`tests/test_property_matching.py`): price parsing (5 formats), label thresholds, perfect-match ≥90 with breakdown summing to score, breakdown sums for all results + descending order, 1.3× exclusion, soft-cap "Slightly over budget" reasoning, legacy alias fields, bedroom shortfall grading, type synonyms, amenity ratios, limit bounds, empty criteria, freshness decay, purpose filter.
- 5 new frontend tests (`SmartMatchModal.test.tsx`): closed-state, snake_case criteria submission, score/label/top-factor rendering with the 5th factor correctly omitted, empty state, error alert.
- Full suites green: backend **183 passed, 1 skipped**; frontend **114 tests / 16 files**; `tsc --noEmit` and `vite build` clean. Browser-verified end-to-end against the live demo dataset (5 ranked results, scores 63/63/63/52/17, breakdowns summing exactly, unaffordable listing excluded to "Above budget" reasoning at 1M budget).

---

## Voice Assistant Search (COMPLETED)

Priority 4 item #38 — voice search as a deterministic, explainable pipeline: speech in, the same `PropertyMatchCriteria` vocabulary the match engine consumes out, with every extracted field echoed back to the user as a chip. Like the matching engine, deliberately rule-based — no external AI service, works offline, fully unit-testable, and nothing the user said is silently dropped.

### Parser (`src/utils/voiceQueryParser.ts`)

- Budget from cue phrases ("under / below / less than / not more than / max / up to / budget of"), currency forms ("KSh 80k"), "shillings/bob" amounts, and bare magnitudes ("45 million", "80 thousand") — digits and word-numbers both supported; k/thousand/grand → ×1,000, m/million/mn → ×1,000,000.
- Bedrooms from digits ("3 bedroom"), word numbers ("three bed"), and studio/bedsitter → 1.
- Locality matched longest-first against the full `LOCATION_SUGGESTIONS` catalog (47 counties + Nairobi areas) with a `cbd → CBD` alias; an uncatalogued locality is still captured from "in/near/around <phrase>", but generic phrases ("in a good area", "in a commercial property") are rejected via a stop-token list so a city is never fabricated.
- Purpose (rent/buy cues), property type (apartment/house/commercial synonym groups), furnishing, and amenities (parking, security, balcony, pool, gym) complete the parse.
- Returns `{ criteria, understood, heard }` — the `understood` chips are the user-facing explainability mirror of exactly what the matcher will weigh.

### Hook + button (`src/hooks/useVoiceSearch.ts`, `src/components/VoiceSearchButton.tsx`)

- Web Speech API wrapper with local minimal typings (the API is absent from lib.dom), `SpeechRecognition ?? webkitSpeechRecognition` detection, final-results-only delivery to `onResult`, interim transcript tracking, friendly mapped errors (permission blocked, no speech, no microphone, offline), 'aborted' suppression, and recognition abort on unmount.
- `VoiceSearchButton` renders nothing when unsupported — no dead control on Firefox — with `aria-pressed` and a dynamic aria-label while listening, plus a reduced-motion-safe pulse.

### Integration

- Public search (`/properties`): the mic feeds the transcript into the search query (URL sync + refetch), alongside the existing typed search.
- AI Smart Matchmaker modal: the transcript prefills the whole brief — purpose, budget, city, bedrooms (clamped 1–4), type, furnishing, requirement toggles, and free-text amenities (pool/gym) — under a "Heard: “…”" echo with understanding chips; everything stays editable before calculating.

### Fixed along the way

- `BUDGET_CUE` capture-group bug: the shared amount regex was non-capturing, so the suffix group landed at index 1 and suffix-less budgets ("under 25,000 shillings") crashed `parseAmount` — silently masked by a fallback branch that only happened to work for "80k" style input.
- `??`/`||` precedence compile error in the hook's language default.

### Tests

- 22 new frontend tests in 3 files: `voiceQueryParser.test.ts` (13) — full rental brief end-to-end, word-number bedrooms + millions, studio + multi-word locality, unfurnished/balcony, furnished + pool/gym + CBD alias, commercial + county, gibberish → empty, fallback locality, generic-phrase rejection, sale + maisonette; `VoiceSearchButton.test.tsx` (6) — unsupported → null, listening state + language, final-results-only, interim ignored, permission error mapping, unmount abort; `SmartMatchModal.test.tsx` voice block (3) — transcript prefills fields and amenity criteria into the submit payload, error surfaced as `role="alert"`, absent mic when unsupported. Shared `FakeRecognition` test double in `src/test/speechRecognitionFake.ts`.
- Full frontend suite: **136 tests / 18 files** green; `npm run typecheck` and `npm run build` clean. Browser-verified end-to-end with an injected speech stub: `/properties` mic filters listings and syncs the URL; SmartMatchmaker modal mic prefills fields, echoes "Heard", and submitting hits the live backend returning 3 ranked results with explainable factor chips.

---

## Advanced Reporting Exports (COMPLETED)

Priority 4 item #39 — downloadable reports built on a single report envelope that serves both the on-screen JSON preview and the CSV download, so what a manager sees and what they export can never drift apart. All computation happens server-side under the caller's role scope; the frontend never re-aggregates.

### Report types (`app/services/reports_service.py`)

- **Occupancy** — point-in-time snapshot per property (units, occupied, vacant, rate, active leases), mirroring the owner-portal convention (occupied = `Unit.status == "occupied"`).
- **Payments** — monthly expected / collected / outstanding / overdue-count with a collection rate, bucketed by `due_date → payment_date → created_at` so unpaid rows without a payment date still land in the right month.
- **Maintenance** — per-category requests / open / resolved / average resolution days / total cost, with open = `pending|in_progress` and resolved = `resolved|closed`.
- **Financial** — monthly income (paid payments) minus expenses (resolved maintenance) = net.
- Money fields are free text in the database ("KSh 45,000/Month", "45k"), so amounts are parsed in Python via the shared `parse_price` helper — a SQL `CAST` would have silently turned them into 0.
- `scope_property_ids` enforces role scoping: admin sees all; manager sees `manager_id`-owned; owner sees `owner_id`-owned; **any other role gets an empty scope** (fail closed).

### Endpoint (`app/routers/reports.py`)

- `GET /api/v1/reports/{report_type}` for manager/owner/admin, `format=json|csv`, optional `date_from`/`date_to`/`property_id`.
- Validation: unknown report type → 404; inverted date range → 400; a `property_id` outside the caller's scope → **404 (not 403)** so scope membership is not leaked.
- CSV response carries `Content-Disposition: attachment` with a dated filename (`propnoxa_<type>_report_YYYYMMDD.csv`); every export emits a `report.exported` security event.
- CSV text cells starting with `=`, `+`, `-`, `@`, tab or CR get a `'` prefix (spreadsheet formula-injection guard); numeric cells are exempt and format cleanly (`45000`, `1,200.5`).

### Frontend (`src/pages/manager/Reports.tsx`, `src/services/reports.ts`)

- The manager Reports page was a disabled placeholder (four dead buttons); it is now a working preview: report-type tabs, from/to date and property filters, summary stat cards, a table built from the envelope's own `columns`/`rows`, a row/generated-at footer, and a per-type hint (occupancy ignores date filters, by design).
- CSV download uses a raw authenticated `fetch` (the shared JSON `api.request` helper cannot read attachments), mirroring the GDPR privacy export pattern; download failures surface as an error banner without losing the on-screen preview.
- Styled entirely with existing management-container/table/stat-card classes, including dark-mode variants.

### Fixed along the way

- The dev SQLite database was stuck at revision `0031_add_mfa` while the code expects the newer tables — surfaced when deleting a test user failed with `no such table: email_preferences`. Backed up (`backend/database.db.bak-20261010-pre-0033`) and applied the two additive pending migrations (0032 privacy consent, 0033 email preferences) to head.

### Tests

- 11 backend tests in `tests/test_reports.py`: role scoping per report type (manager only own property, owner both, manager B isolated, admin all), auth gate (anonymous and tenant → 403), payments month bucketing with free-text amounts ("KSh 45,000" → collected 45,000; "45k" + "120000" outstanding 165,000 with one overdue), maintenance averages ("5,000" cost, 6.0-day resolution) and financial net (60,000 − 10,000; pending/unresolved rows excluded), CSV headers/attachment filename/quoting, the formula-injection guard (`'=SUM(A1:A9)`), property filter scoping incl. 404 for out-of-scope, and validation (404/400/422). Full backend suite: **194 passed, 1 skipped**.
- 11 frontend tests: `src/services/reports.test.ts` (5 — query building, bearer-header CSV fetch with anchor download naming, failure path) and `src/pages/manager/Reports.test.tsx` (6 — mount load, tab switching, filters forwarded to API and CSV, empty state, error surfacing, download failure keeps preview). Full frontend suite: **147 tests / 20 files** green; `npm run typecheck` and `npm run build` clean.
- Browser-verified live against the dev dataset: all four tabs render real aggregated data (occupancy 17 properties/957 units, payments monthly, maintenance categories, financial empty state), filters render, the Download CSV click issues `GET /reports/financial?format=csv → 200 text/csv`, dark mode styled, no console errors. Manager role scoping additionally verified end-to-end through the live API with a throwaway manager account (only their own property visible; scratch rows removed afterwards).

---

## Analytics Dashboards (COMPLETED)

Priority 4 item #34 — a role-scoped analytics dashboard shared by the admin, manager and owner portals, backed by a single aggregation endpoint and a dependency-free in-house SVG chart kit.

### Backend (`app/routers/analytics.py`, `app/services/analytics_service.py`)

- `GET /api/v1/analytics/dashboard?months=N` (3–24, default 6) for manager/owner/admin; every aggregation is filtered through the same `scope_property_ids` helper as reports (admin all / manager own / owner own / anything else fail-closed empty), so one endpoint serves all three portals without leaking cross-scope data.
- Zero-filled month series: every requested month appears in financial, payments and maintenance series even with no data, so charts never silently skip periods.
- KPI block (properties, units, occupancy, active leases incl. expiring-within-30-days, open maintenance, overdue payments, period collected/net), property leaderboard (collected + outstanding per property), city and maintenance-category distributions — all computed server-side; the frontend never re-aggregates.
- 10 backend tests (`tests/test_analytics.py`) covering scoping, zero-fill, KPIs, distributions, range validation and auth. Full backend suite: **204 passed, 1 skipped**.

### Frontend

- **No new dependencies** — deliberate. The production dependency list (and the blocking `npm audit --omit=dev --audit-level=high` gate) stays untouched; instead a small in-house SVG chart kit (`src/components/charts/`): `LineChart` (multi-series, hover tooltip with nearest-point lookup), `BarChart` (stacked or grouped, per-segment tooltips), `DonutChart` (units-by-status with center total + legend). All three are viewBox-responsive with `role="img"` labels, use the `--chart-1..6` CSS variables (so dark mode works for free), and render honest "No data for this period" empty states instead of fake axes.
- Shared page `src/pages/AnalyticsDashboard.tsx` mounted on all three portals (`/admin/analytics`, `/manager/analytics`, `/owner/analytics`) with role-specific headings (Platform / Operations / Portfolio Analytics), a 3M/6M/12M range switch, 8 stat cards, 4 charts, city/category bar rows and a top-properties table. Nav entries added to all three layouts.
- Analytics series types are flat **type aliases** (not interfaces) — TypeScript grants implicit index signatures only to object-literal aliases, which is what lets the chart components accept `Record<string, number | string>` points without casts.
- 39 new frontend tests in 6 files (chart math 18, LineChart 5, BarChart 5, DonutChart 4, service 2, page 5) including hover-tooltip geometry via a stubbed `getBoundingClientRect` and a zero-width guard test. Full frontend suite: **186 tests / 26 files** green; `npm run typecheck` and `npm run build` clean.

### Verification

- Browser-verified end-to-end on `/admin/analytics` against the live dev dataset: 8 KPI cards with correct values (16 properties, 956 units, 0.1% occupancy, 1 active lease, 3 open maintenance), 3 SVG charts rendered, 1 honest empty state (financial series is all-zero in dev), 11 distribution rows, 5 leaderboard rows, generated-at footer. Range switch 6M → 12M issued `GET /analytics/dashboard?months=12 → 200`, updated `aria-pressed` and the footer timestamp; console clean.

---

## Service Marketplace Expansion (COMPLETED)

Priority 4 item #40 — the contractor marketplace grew from a bare provider directory into a full quote → dispatch → execution → review round trip. Migration `0034_marketplace_expansion`.

### Backend (`app/routers/service_marketplace.py`, migration `0034_marketplace_expansion`)

- **Provider directory search**: `GET /providers` gains `q` (company name), `category`, `city` (service-area match), `available_only`, and `sort` (rating / jobs / newest / name) plus paging; the provider payload exposes the enriched profile (rating_avg rounded to 2dp, reviews_count, completed_jobs_count, service_areas list, insurance_verified).
- **Public review pages**: `GET /providers/{id}/reviews` returns paged reviews with masked reviewer names ("Mary W."), the linked maintenance title, and aggregate rating/count — directory visitors can inspect a contractor's history without exposing tenant identities.
- **Open job board**: `GET /open-requests` lists maintenance tickets still in flight (status not in resolved/closed) with quotes_count plus the calling provider's own bid state (`my_quote_id` / `my_quote_status` / `my_quote_amount`), so a provider sees at a glance which tickets they already bid on.
- **Quote lifecycle**: `POST /quotes` (one live quote per provider per ticket), `GET /quotes/request/{id}` for the ticket-owner view; accepting a quote (`POST /quotes/{id}/accept`) marks it accepted, rejects competing pending quotes, and creates the work order in one step.
- **Work orders**: `GET /work-orders` (status / maintenance filters; provider sees own), `PATCH /work-orders/{id}/status` for the assigned provider (assigned → in_progress → completed, completion notes captured), manager-only completion verification, and `POST /work-orders/{id}/review` writing a 1–5 provider rating that recomputes the profile's rating_avg / reviews_count / completed_jobs_count.
- 19 backend tests (`tests/test_marketplace.py`). Full backend suite: **223 passed, 1 skipped**. Dev database migrated to head (backup: `backend/database.db.bak-20261010-pre-0034`).

### Frontend

- Shared role-aware directory `src/pages/Marketplace.tsx` mounted on `/admin/marketplace`, `/manager/marketplace`, `/owner/marketplace` (nav entries in all three layouts) with search/city/specialty/sort/availability filters, provider cards (verified badge, rating stars, completed jobs, hourly rate, coverage areas) and a paged reviews modal.
- Provider portal: `OpenJobs` job board (ticket cards with priority / quotes-so-far / own-bid pill, quote submission modal, paging). Manager `Maintenance` page gains a Quotes & Work Orders modal — bid comparison table (Accept & Dispatch), work order tracking, and an inline rate-provider form (1–5 stars + comment, only after completion).
- Accessibility fix found while writing tests: the quote modal inputs had labels without htmlFor/id pairs.

### Verification

- 17 new frontend tests across 3 suites (Marketplace 7, provider OpenJobs 5, manager Maintenance 5). Full frontend suite: **203 tests / 29 files** green; `npm run typecheck` and `npm run build` clean.
- Browser-verified end-to-end against the live dev pair (frontend :5173, backend :8000) with real per-role sessions: provider "Kelvin Kiprono" bid KSh 18,000 on ticket #262 from the job board → manager "Sarah Mwangi" saw the bid in Quotes & Work Orders and accepted it (work order created, competing pending bids rejected) → provider advanced assigned → in_progress → completed with completion notes → manager rated 4★ with a comment → directory and reviews modal then showed the recomputed 4.5 avg over 2 reviews and 1 completed job. DB state verified after each step.

---

## 360° Virtual Tours (COMPLETED)

Priority 4 item #36 — properties now carry an ordered list of virtual-tour links (360° / 3D walkthroughs) with a strict provider allowlist, an embeddable viewer and a graceful external-link fallback. Migration `0035_property_tours`.

### Backend (`app/routers/property_tours.py`, `app/services/tour_service.py`, migration `0035_property_tours`)

- `PropertyTour` model (table `property_tours`, FK → properties with cascade delete) and CRUD under `/api/v1/properties/{id}/tours`: public list ordered by `sort_order`; POST/PATCH/DELETE restricted to the property owner or an admin (same `_ensure_can_manage` pattern as property update/delete). All mutations invalidate the public property cache.
- **Allowlist-first URL parsing** (`tour_service.parse_tour_url`): only Matterport, Kuula, RoundMe, Sketchfab and YouTube are recognized as embeddable; every other valid `https://` link is stored as provider `link` with `embed_url=None`. Embed URLs are always **rebuilt from the extracted id** against a fixed canonical template — the raw user-supplied URL is never echoed into the iframe; hostname matching is suffix-exact, so userinfo spoofs (`https://my.matterport.com@evil.example/…`) and malformed ids fall through to `link`. Non-https, spaces/control characters and empty URLs are rejected with 422 (plus a client-side https check as defence in depth).

### Frontend

- `VirtualTourViewer` modal (zero new dependencies): sandboxed iframe (`allow-scripts allow-same-origin allow-presentation allow-popups allow-fullscreen` + fullscreen/XR/gyroscope permissions), provider-labelled header, tour switcher chips when a property has several tours, an always-present "Open in new tab" link, and a 360°/thumbnail fallback panel for non-embeddable `link` tours. Escape and overlay-click close the dialog; clicks inside it don't bubble out.
- `TourEditor` on the property edit page: paste-a-link form with provider badges (`· embedded` / `· external`), inline https validation, and a two-step delete ("Confirm delete?").
- PropertyDetails public page lists one button per tour ("Play 360° tour · {title}" / "Open tour · {title}") and mounts the viewer.

### Verification

- 19 backend tests (`tests/test_property_tours.py`): URL parsing (embed rebuilds, userinfo spoof, bad ids, 422s) and CRUD authz (401/403/404 incl. cross-property, ordering, property-cascade delete). Full backend suite: **242 passed, 1 skipped**.
- 14 frontend tests (`VirtualTourViewer` 8, `TourEditor` 6). Full frontend suite: **217 tests / 31 files** green; `npm run typecheck` and `npm run build` clean.
- Browser-verified end-to-end on the live dev pair: added Matterport `show/?m=SxQL3iGyoDo` and an unknown-host link via TourEditor (badges `Matterport 3D · embedded` / `External link · external`; DB rows showed the parsed provider and the rebuilt embed URL vs `NULL`), public page showed both buttons, the viewer iframe `src` matched the canonical Matterport embed URL with the sandbox attributes, the chip switch swapped to the external fallback panel (no iframe, `target="_blank"` link), Escape closed the modal, and the two-step delete removed the link tour (DB left with the single genuine Matterport row). Dev DB migrated to head (backup: `backend/database.db.bak-20261010-pre-0035`).

---

## Multi-Language Support (EN + SW) (COMPLETED)

Priority 4 item #32 — full internationalization of the platform chrome into English and Kiswahili, Kenya's two primary languages, with a zero-dependency implementation: no i18n library was added, so the production dependency set and the blocking `npm audit` gate are untouched.

### Translation system (`src/i18n/`)

- `translations.ts`: flat dotted-key dictionaries (`en` + `sw`) in a single typed module; `Language = 'en' | 'sw'`, `SUPPORTED_LANGUAGES`, `LANGUAGE_LABELS` (native names for the switcher), and `LANGUAGE_CODES` (EN/SW chip text). English is the fallback language.
- `LanguageContext.tsx`: `LanguageProvider` (mounted in `main.tsx` inside `ThemeProvider`) with the `useTranslation()` / `useLanguage()` hooks. Lookup chain is `translations[language][key] ?? translations.en[key] ?? key`, so an untranslated string degrades to English, never to a blank or a crash. `{placeholder}` interpolation (`interpolate()`) covers dynamic strings (listing counts, the footer year, MFA dev codes, chosen signup role) and leaves unknown placeholders untouched. The chosen language persists to `localStorage` under `propnoxa-language` (read/write guarded — private-mode webviews fall back to English in memory only) and `<html lang>` is kept in sync for screen readers and hyphenation.
- `LanguageToggle` (public navbar + all seven portal layouts, beside the existing theme toggle): single button cycling EN ↔ SW with an accessible name describing the next state; `data-language` attribute for styling/tests.
- Marketing copy is data-driven: `src/data/publicHomeContent.ts` stores translation keys (purpose copy, location notes, intelligence cards, how-it-works steps) instead of literals, so the homepage composes from dictionaries rather than hardcoded English.

### Converted surfaces

- Public site: navbar, footer (incl. interpolated year), the full homepage (hero, purpose selector, featured listings with live-count interpolation, locations, intelligence, steps), Login (incl. MFA challenge strings), and the register RoleSelector (key-driven role cards).
- All seven portal layouts: Manager, Admin, Owner, Tenant, Agent, Provider sidebars and headers (menu items, workspace labels, role badges, nav aria-labels, greetings, sync status, logout), plus the shared `MainLayout` covering all six role sidebar variants via `getSidebarItems()` returning `[path, labelKey]` pairs.
- Deliberately left EN-only (documented extension surface): property search option labels (type/budget/bedroom buckets are data values), client-side validation messages, and deep page bodies beyond chrome and menus — the dictionaries and hooks are in place for those to be translated incrementally without any structural change.

### Verification

- Key-parity test: `translations.test.ts` fails if `en` and `sw` key sets drift apart, if any dictionary value is empty, or if a homepage content key referenced by `publicHomeContent.ts` is missing from either language — so a future feature that adds an English string is caught at test time until its Kiswahili counterpart lands.
- 18 new frontend tests in 3 files: `LanguageContext.test.tsx` (10 — default/stored/invalid-value resolution, persistence, `<html lang>` sync, interpolation incl. unknown placeholders, sw→en fallback, missing-key passthrough, storage-throwing resilience, hook-outside-provider error); `LanguageToggle.test.tsx` (3 — full cycle with accessible names, stored-language boot, className merge); `translations.test.ts` (5 — dictionary coverage, parity, non-empty values, homepage key resolution).
- Full frontend suite: **235 tests / 34 files** green; `npm run typecheck` and `npm run build` clean.
- Browser-verified end-to-end on the live dev pair: home page EN→SW (nav `Nyumbani / Nunua / Kodisha / Wekeza / Chunguza`, hero `Pata Mali Inayofaa Maisha Yako.`, `lang="sw"` on `<html>`), reload persistence, `/login` in Kiswahili (`Ingia kwenye PropNoxa`, `Nenosiri`, `Onyesha`), back to English, and an authenticated admin session (brand `PropNoxa Msimamizi`, workspace `KITUO CHA UDHIBITI`, nav items `Dashibodi / Uchambuzi / Mali …`, greeting `Habari za asubuhi, Gabriel Onsomu`, logout `Toka`). Session state restored afterwards (language back to EN, refresh cookie cleared).

---

## PWA Mobile Experience (COMPLETED)

Priority 4 item #33 — installable, offline-capable mobile experience, implemented as a PWA (per the approved reframe from React Native) with zero new dependencies: a hand-written service worker, a hand-rolled build step, and the browser's own install flow.

### App identity (`public/manifest.webmanifest`, `index.html`)

- Manifest: standalone display, `PropNoxa` short name, `/` start URL and scope, `#102a43` theme/background (splash + browser chrome), 192/512 `any` icons plus a maskable 512, and shortcuts to `/properties` + `/dashboard`.
- `index.html` head: manifest link, apple-touch-icon, iOS/Android install metas, and per-scheme `theme-color` (light/dark) alongside the existing anti-FOUC theme bootstrap.

### Service worker (`public/sw.js`, `public/offline.html`)

- Navigations: network-first with the last good shell cached under `/`, falling back to `offline.html`; other same-origin GETs: stale-while-revalidate; `/api/*`, non-GET and cross-origin requests are never intercepted (live financial/personal data must never be served from cache).
- Versioned caches (`propnoxa-static-*` / `propnoxa-runtime-*`); `install` warms the precache then `skipWaiting()`, `activate` deletes every previous `propnoxa-*` cache then claims clients.
- Build-time injection (`src/pwa/swBuild.ts` + `createPwaPrecachePlugin` in `vite.config.ts`): after `vite build`, the plugin rewrites the marker regions in `dist/sw.js` — the precache list becomes every built file (22 entries; `sw.js` excluded) and the cache version becomes a 12-hex-char hash of that list (`d30b49a874b3` for this build). One online visit is therefore enough to run the entire app offline, and every deploy activates fresh cache names so the previous deploy's caches are evicted automatically.
- Registration (`src/pwa/registerServiceWorker.ts`): production-only, after window `load`; in dev the app actively unregisters any leftover worker so `vite dev` never serves stale cached assets.
- Install prompt: `useInstallPrompt` (defers `beforeinstallprompt`, clears on `appinstalled`, detects iOS Safari for a manual "Add to Home Screen" hint) + `InstallPromptBanner` with persisted dismissal under `propnoxa-install-dismissed`, fully translated EN/SW.

### Two real service-worker bugs found by browser E2E (and fixed)

1. **Cache writes killed on worker shutdown:** the stale-while-revalidate handler fired `cache.put` without awaiting it, so the worker could terminate before the response body was buffered — entries silently never persisted. Fixed by awaiting the put inside a promise that the fetch event's `waitUntil` keeps the worker alive for.
2. **`Vary: Origin` cache mismatch (production-breaking):** Vite serves assets with `Vary: Origin`, and SPA subresources (`<script crossorigin>`, `<link crossorigin>`) send an Origin header, while SW-internal stores (`cache.add`, manual `fetch`) do not — so stored entries were never matched offline. Result: with the server down, every build asset failed with `net::ERR_FAILED` and the app booted blank. Fixed by passing `ignoreVary: true` to every `caches.match` call plus the full-precache build injection above (which also removes any reliance on the runtime cache for first-visit assets).

### Tests

- 15 tests in `src/pwa/` across 3 files: `manifest.test.ts` (7 — identity, theme colors, icons on disk, shortcuts, offline shell + worker pairing, build-injection markers present, every `caches.match` call carries `ignoreVary`), `swBuild.test.ts` (5 — dist→URL mapping incl. backslash normalization and `sw.js` exclusion, deterministic 12-hex build id that changes with content, marker injection + build-id stamping, idempotence across rebuilds, loud failure when markers/token are missing), `registerServiceWorker.test.ts` (3).
- Full frontend suite: **263 tests / 39 files** green; typecheck and build clean.

### Browser verification (vite preview, then server killed)

- Online visit on the fresh build: the new worker activated and `caches.keys()` showed exactly one cache — `propnoxa-static-d30b49a874b3` (old `v1` caches evicted) holding all 22 precached files.
- With the preview server force-killed: a plain offline navigation booted the full landing page (5,142 chars, hero h1, 9 nav links, all 9 build assets `status 200` in the resource timeline, zero failures) and an offline reload did the same — previously both produced a blank page with `net::ERR_FAILED` on every asset.
- Install flow: synthetic `beforeinstallprompt` → banner in English (`Install PropNoxa` / `Install`) and Kiswahili (`Sakinisha PropNoxa` / `Sakinisha`, screenshot-verified); clicking Install invoked `prompt()`, and accepting dismissed the banner (dismissal flag persisted).

---

## Tamper-Evident Audit Chain (COMPLETED)

Priority 4 item #37 — the append-only `audit_logs` table becomes a hash-chained, tamper-evident ledger (the approved reframe from a literal blockchain): every entry carries `prev_hash` + `entry_hash`, and any edit, deletion, reorder or forged re-hash is detected by re-walking the chain.

### Chain design (`app/utils/audit_hash.py`, `app/models/audit_log.py`, `app/models/audit_chain_state.py`)

- Each entry stores `prev_hash` (the previous entry's `entry_hash`) and `entry_hash = HMAC-SHA256(key, f"{prev_hash}:{canonical_payload}")`. The key is `AUDIT_CHAIN_SECRET`, falling back to `SECRET_KEY` (write-once — rotating the key breaks verification of all existing entries). The canonical payload is fixed-schema JSON (`sort_keys`, no whitespace, `ensure_ascii`, `v:1`) over actor/action/entity/ip/user-agent/details/created_at, so hashes are deterministic across SQLite and Postgres.
- Writing is enforced in a SQLAlchemy `before_insert` hook, so *every* writer (services, scripts, admin API, migration backfill) produces chained rows — nothing bypasses it short of raw SQL.
- `created_at` is coerced to naive UTC at write time so verification recomputes byte-identical payloads from what the database returns.
- **Flush-ordering hazard (found in design, regression-guarded by test):** all `before_insert` events in one flush run *before* any INSERT executes, so a "read the newest row" hook would fork the chain on batched writes. Fix: a single-row tip table (`audit_chain_state.last_entry_hash`) — the hook reads the tip, computes the hash, and advances the tip immediately via a Core statement on the same connection. Statements run in order even inside one flush, entries chained together in a batch stay linear, and a rolled-back transaction rolls the tip back with it. On Postgres the tip read takes `SELECT ... FOR UPDATE` to serialize concurrent writers; SQLite omits it (single-writer).

### Retention-prune anchors (`app/services/retention_service.py`, `app/services/audit_chain.py`)

Pruning aged entries would otherwise look like tampering. Instead, `prune_audit_logs` records an `AUDIT_CHAIN_ANCHOR` entry (itself a normal chained row) whose `details_json.links` list vouches, for each fully-pruned run, the exact `{predecessor_id, predecessor_hash, successor_id}`. Verification accepts a broken link **only** when an anchor vouches for that exact predecessor hash, so an entry deleted after the fact is still flagged. Handled cases:

- **Prefix prune** (oldest entries): verification accepts the chain root `{"kind": "anchor"}` naming the surviving first entry.
- **Middle prune**: broken link accepted only via the anchor's vouched predecessor hash.
- **Tail prune** (newest entries aged out, e.g. clock skew): the tip row is moved down to the last survivor; the anchor records `tail_pruned_from_id`.
- **Full prune**: tip cleared to NULL; the chain restarts from genesis on the next entry.
- **Anchor self-expiry**: an anchor ages out in the same run as its vouched successor (provable from the retention window), so anchors are ordinary prunable rows — covered by a dedicated test.

### Verification surfaces

- `verify_audit_chain(db)` walks the chain in id order, checks the root (genesis or anchor), per-row `prev_hash` linkage (anchor-vouched breaks allowed), re-computes every `entry_hash`, then cross-checks the tip table. Returns `{verified, entries_checked, root, first_entry_id, last_entry_id, tip_hash, first_broken, checked_at}`.
- `GET /api/v1/audit-logs/chain/verify` (admin-only) returns that report; the audit log list now also exposes `prev_hash`/`entry_hash` per entry.
- `scripts/verify_audit_chain.py` — read-only, cron-friendly CLI (exit 0/1); pair with `scripts/run_retention.py` after pruning.
- Migration `0036_audit_chain` adds the two columns + tip table and backfills existing rows into a chain (chunked, dialect-agnostic; online-only, no `--sql` support).

### Tests (22 in `tests/test_audit_chain.py`)

Chained writes incl. batched flush; empty chain; edited / deleted-middle / deleted-tail / deleted-prefix detection; forged re-hash without the key detected; missing-hash flagged; timestamp round-trip; prefix / middle / tail / full prune all verify with anchors; edit-after-prune still detected; deletion-after-prune not vouched; legal hold; endpoint auth (401 anon / 403 non-admin / 200 admin) and chain fields in the listing.

### Dev database

Migrated to `0036_audit_chain` (backup: `backend/database.db.bak-20261010-pre-0036`); the 12 pre-existing audit entries were backfilled and `scripts/verify_audit_chain.py` reports `verified: true` (genesis root, tip recorded). A live insert against a DB copy was confirmed to chain onto the backfilled tip.

### Documented limitation

The chain is tamper-**evident**, not tamper-**proof**: an attacker with both database write access **and** the HMAC key (or `SECRET_KEY`) can recompute a fully consistent chain. Without the key, DB-only tampering is detected. Key material stays in the secrets manager.

---

## Known Limitations

1. **Email Service:** Implemented — SMTP transport with branded HTML/text templates, preference-gated notification fan-out, and console fallback for dev. Production only needs `EMAIL_BACKEND=smtp` + relay credentials from a secrets manager. (SendGrid HTTP API integration remains optional future work; SMTP covers SES/Mailgun relays.)
2. **CSRF Protection:** Skipped as JWT-based API has sufficient protection.
3. **Password Reset:** Implemented (token-based, history-checked). Email delivery needs the production provider above.
4. **File Upload:** Implemented with local storage; virus scanning and S3/signed URLs pending.
5. **Monitoring:** Basic metrics/health/logging in place; Sentry/APM/alerting integrations pending.
6. ~~Backend repo consolidation pending~~ — **resolved 2026-10-10:** backend sources are tracked as ordinary files in the root repo, so backend CI (pytest, bandit, pip-audit) and the Docker image build now run. The nested repo remains available at `backend/.git.pre-consolidation` for rollback.
7. **Dependency advisories:** Production `npm audit` is green at high+ severity. Remaining advisories are dev-tooling only (Vitest 5 / esbuild / tinypool chain) plus react-router, whose fix requires the breaking react-router 7 major upgrade. `pip-audit` runs in advisory mode until `requirements.txt` is fully pinned.
8. **Deploy steps are placeholders:** The promotion workflow verifies the path end to end (CI re-run + environment gates), but the actual deploy commands await a hosting decision. The Docker image build job has not been executed yet — no Docker daemon was available on the dev machine; first CI run on GitHub will validate it.
9. **Postgres-only migration in chain:** A pre-existing migration uses `ALTER TABLE leases ALTER COLUMN ... TYPE`, which SQLite cannot execute, so the full Alembic chain cannot be replayed on SQLite dev databases. New migrations are validated by stamping the previous head first (see GDPR section).

---

## Support

For questions or issues:
1. Check this documentation
2. Review code comments in service files
3. Check FastAPI docs at `/docs` endpoint
4. Review logs for error messages

---

## Changelog

### October 11, 2026
- Added `DEPLOYMENT.md` — deployment runbook mapping the launch checklist to the repo state (CI/CD gates, backup/PITR tooling, health + metrics endpoints, secret inventory, compose reference stack), the recommended CDN → ALB → API → RDS/Redis architecture with per-component gaps, a rollback procedure (image swap, migration downgrade, restore + audit-chain re-verify), and an incident-response quick guide; outstanding manual actions tracked (admin password rotation, secrets manager, hosting choice, payment gateway, SMTP, upload volumes, alerting, pen/load testing)

### October 10, 2026
- Implemented tamper-evident audit chain (#37): `audit_logs` entries now carry HMAC-SHA256 `prev_hash`/`entry_hash` stamped by an insert hook (every writer chained, no bypass), with a single-row tip table that keeps batched-flush inserts linear (regression-tested), naive-UTC `created_at` normalization for cross-DB hash stability, retention-prune `AUDIT_CHAIN_ANCHOR` vouchers covering prefix/middle/tail/full prunes (edit-after-prune still detected, anchor self-expiry proven safe), admin `GET /api/v1/audit-logs/chain/verify` endpoint + `scripts/verify_audit_chain.py` CLI, migration `0036_audit_chain` backfilling all existing rows (dev DB migrated; 12 entries verified `true` with a live insert chaining onto the backfilled tip; backup `backend/database.db.bak-20261010-pre-0036`); 22 backend tests (264 total); documented limitation — withstands DB-only tampering, not an attacker holding both DB write access and the HMAC key
- Implemented PWA mobile experience (#33): zero-dependency installable PWA — web manifest (standalone PropNoxa identity, icon set incl. maskable, `/properties` + `/dashboard` shortcuts), hand-written service worker (network-first shell with `offline.html` fallback, stale-while-revalidate assets, `/api/*` never cached), build-time injection that precaches the full 22-file dist under a content-hashed cache version and evicts prior deployments on activate, prod-only registration, and an EN/SW install banner with persisted dismissal; browser E2E exposed and fixed two real SW bugs — a fire-and-forget `cache.put` killed on worker shutdown and cached assets failing to match offline because Vite's `Vary: Origin` header rejects Origin-less SW cache lookups (fixed with `ignoreVary` + full precache) — with the preview server killed, the app now boots fully offline (hero + nav + all 9 assets, was blank with `net::ERR_FAILED`); 15 frontend tests (263 total), typecheck/build clean
- Implemented multi-language support EN + SW (#32): zero-dependency i18n (no new packages, audit gate untouched) — flat-key `en`/`sw` dictionaries with an `en` fallback chain, `{placeholder}` interpolation, guarded `localStorage` persistence under `propnoxa-language`, in-sync `<html lang>`, and a header `LanguageToggle` on the public site and all seven portal layouts; marketing copy moved to translation keys in `publicHomeContent.ts`; converted surfaces: public navbar/footer/home/login/register, all portal menus/greetings/workspaces/sync/logout and the six-role `MainLayout` sidebar map; 18 new frontend tests incl. an en/sw key-parity drift gate, full suite **235 tests / 34 files** green, typecheck/build clean, browser-verified EN↔SW on home/login/admin incl. reload persistence
- Implemented 360° virtual tours (#36): ordered per-property tour links on migration `0035_property_tours` with an allowlist-first URL parser (Matterport/Kuula/RoundMe/Sketchfab/YouTube get id-rebuilt canonical embed URLs; any other valid https link stores as external `link` with `embed_url=None`; userinfo-spoof and bad-id URLs fall through safely), public list + owner-or-admin mutations, zero-dependency `VirtualTourViewer` modal (sandboxed iframe, switcher chips, external fallback panel) and `TourEditor` on the property edit page with two-step delete; 19 backend + 14 frontend tests, browser-verified end-to-end (add → embed modal → fallback chip → Escape → delete); dev DB at 0035 (backup: `backend/database.db.bak-20261010-pre-0035`)
- Implemented service marketplace expansion (#40): full contractor round trip on top of migration `0034_marketplace_expansion` — searchable provider directory (q/category/city/availability/sort + paging), masked-name review pages, open job board with per-provider bid state, one-live-quote-per-ticket lifecycle where accepting a bid rejects competing pending quotes and creates the work order, provider status execution with completion notes, and manager 1–5★ reviews that recompute avg rating / review count / completed jobs; shared Marketplace page on admin/manager/owner portals plus provider OpenJobs and manager Quotes & Work Orders UIs; 19 backend + 17 frontend tests, browser-verified full loop with real provider/manager sessions (KSh 18,000 bid → accept → execute → 4★ review → profile at 4.5 / 2 reviews in the directory); dev DB migrated (backup: `backend/database.db.bak-20261010-pre-0034`)
- Implemented analytics dashboards (#34): role-scoped `GET /analytics/dashboard` (admin/manager/owner via shared `scope_property_ids`, zero-filled month series, KPIs + leaderboard + city/category distributions), shared AnalyticsDashboard page on all three portals with 3M/6M/12M range switch, and a dependency-free in-house SVG chart kit (LineChart/BarChart/DonutChart — viewBox-responsive, CSS-variable colors so dark mode is native, jsdom-tested incl. hover geometry) chosen deliberately to keep the production dependency set and the blocking npm audit gate untouched; 10 backend + 39 frontend tests, browser-verified live incl. range-switch refetch
- Implemented advanced reporting exports (#39): four report types (occupancy, payments, maintenance, financial) from one envelope shared by the JSON preview and the CSV download — free-text amounts parsed in Python instead of silent-zero SQL CAST, monthly bucketing with date fallbacks, `scope_property_ids` role scoping (admin all / manager own / owner own / others fail-closed), out-of-scope `property_id` → 404 to avoid existence leaks, spreadsheet formula-injection guard on CSV text cells, `report.exported` audit event; manager Reports page rebuilt from a disabled placeholder into tabs + filters + summary cards + CSV download; 11 backend + 11 frontend tests, browser-verified live (all four tabs, CSV 200 text/csv, dark mode, no console errors); dev database migrated to head (backup: `backend/database.db.bak-20261010-pre-0033`)
- Implemented voice assistant search (#38): deterministic spoken-brief parser (budget incl. word-numbers/magnitudes, bedrooms/studio, catalog+fallback localities with generic-phrase rejection, purpose/type/furnishing/amenities) producing explainable criteria chips, Web Speech API hook with graceful unsupported/permission/no-speech handling, mic wired into public property search + AI Smart Matchmaker modal; 22 new frontend tests, browser-verified end-to-end
- Implemented AI property matching engine (#35): deterministic explainable weighted scoring (budget/location/size/type/amenities/quality/furnishing/freshness), 1.3× budget hard-cap exclusion, per-factor `score_breakdown` that sums exactly to the score, human-readable reasons, bounded `limit` param, and a silent field-drop bug fix (`max_price`/`city`/`amenities` aliases); 18 backend + 5 frontend tests, browser-verified end-to-end
- Removed hardcoded plaintext admin credentials from `backend/scripts/setup_admin.py` (now reads `ADMIN_EMAIL`/`ADMIN_PASSWORD` from the environment and fails closed when missing); **the previously committed password must be rotated** since it remains in git history
- Implemented dark mode across all portals (#31): ThemeProvider with light/dark/system preference (persisted, OS-preference following), ThemeToggle in the public navbar and all six portal headers, anti-FOUC bootstrap in `index.html`, and a full `html[data-theme="dark"]` override layer over a variable-ized light theme (light rendering unchanged); verified in-browser across public, auth and admin pages; 109 frontend tests green
- Completed mobile responsiveness audit (#29): found 8 breakpoint utility classes used by components but never defined in CSS (silently breaking 3-up grids and header alignment); added the missing base utilities plus mobile collapse rules in the 900px block, verified via CSSOM/computed-style probes; 94 frontend tests green
- Implemented permission granularity skeleton (#28): `domain:action` permission catalog with per-role default grants (admin incl. via `roles_csv`), `require_permission` dependency factory, `GET /auth/me/permissions` for UI gating, admin-only `GET /admin/permissions/catalog`; no migration; 12 backend tests
- Implemented SMS notification skeleton (#23): pluggable transport behind `SMS_BACKEND` (console default; twilio fails closed until provider credentials are set), 1600-char truncation, HIGH/CRITICAL notification fan-out to `users.phone` (no migration), MFA OTP flow reused unchanged; 10 backend tests
- Implemented payment gateway skeleton (#21): pluggable gateway registry with a fully working in-process mock (rejected in production), fail-closed stripe/paypal/mpesa stubs, HMAC-verified idempotent webhooks, `POST /payments/{id}/gateway/charge` + `POST /admin/payments/reconcile`; stores provider txn IDs in existing columns (no migration); 10 backend tests
- Implemented performance optimization (#25): Redis cache-aside on public property endpoints with mutation-driven invalidation and graceful broken-Redis passthrough, optional read-replica routing (`DATABASE_REPLICA_URL` + `get_read_db`), immutable `Cache-Control` on property media; 7 backend cache tests
- Migrated 5 legacy test files (properties, units, leases, payments, maintenance) off the real dev database onto isolated per-test fixtures — eliminates the intermittent duplicate-email failures and stops tests writing junk rows into the dev database
- Fixed an intermittent 500 in GDPR erasure execution: the anonymization password is now hashed without the user password policy (`hash_unusable_password`), since random tokens lacked a special character ~13% of the time

### October 9, 2026
- Completed 9/10 Priority 1 security improvements
- Completed all Priority 2 improvements
- Added email verification flow
- Created database migration for email verification (fixed migration chain: 0029 now follows 0028, single alembic head)
- Implemented file upload security (magic-byte validation, size limits, safe storage)
- Implemented API versioning (/api/v1 with legacy /api compatibility + deprecation headers)
- Enhanced monitoring (uptime, error rates, aggregate counters, system info in /health/metrics)
- Implemented secure password reset flow (forgot/reset/change, hashed single-use tokens, password history, session revocation) + 9 tests
- Updated backend test fixtures to use policy-compliant passwords (55 tests now passing)
- Implemented MFA (TOTP + SMS backup + recovery codes, admin-mandatory option, dual-context endpoints) + 8 backend tests; MFA management UI in all six role portals
- Implemented automated database backups (verified dumps, retention, secondary copy, WAL/PITR plan, restore drill tooling) + 10 tests
- Implemented CI/CD: GitHub Actions pipeline (frontend typecheck/tests/build/e2e, backend pytest + bandit + pip-audit, npm audit gates, backend image build) and dispatch-based staging/production environment promotion
- Added frontend test infrastructure: 88 Vitest tests with enforced coverage thresholds (85.5% lines) and Playwright e2e smoke suite plus an opt-in real-TOTP MFA login journey
- Added `scripts/consolidate-backend-git.sh` to fold the nested backend repository into the root repo (prerequisite for backend CI); annotated bandit B104 on the intentional 12-factor `HOST` default
- Applied non-breaking `npm audit fix` updates (react-router 6.30.6, source-map-js 1.2.2); full frontend suite re-verified green afterwards
- Implemented GDPR compliance (#26): append-only consent log (grants AND refusals, anonymous + authenticated, migration 0032), JSON data export with secret redaction, Art. 17 erasure via anonymize-not-delete with admin approval workflow, cookie consent banner + privacy policy page, admin "Deletion Requests" queue, tenant privacy controls; 9 backend + 6 frontend tests
- Implemented email notifications (#22): SMTP/console transports behind `EMAIL_BACKEND`, branded HTML+text templates (verification, password reset, notification) with HTML escaping, per-user opt-out (migration 0033, `/notifications/email-preferences` + tenant profile toggle), preference-gated fan-out of all in-app notifications; 12 backend tests, live API verified
- Implemented document generation (#24): fpdf2 lease-agreement and invoice PDFs with latin-1 sanitization, stamp-keyed cache under gitignored `DOCUMENTS_DIR` with stale pruning, authenticated download endpoints (`/leases/{id}/document`, `/payments/{id}/invoice`) mirroring existing read authz, explicit not-e-signed disclaimer; 11 backend tests
- Implemented data retention (#30): retention service purging expired/used ephemeral auth tokens (30-day grace), audit logs (365 days, 0 disables) and notifications (read 180 / unread 360) with global `LEGAL_HOLD_ENABLED` litigation hold; `POST /admin/retention/run` + `scripts/run_retention.py` cron CLI, `RETENTION_RUN` audit trail; 10 backend tests
- Implemented comprehensive logging (#27): `security` event stream (`emit_security_event`) covering login/MFA/password-reset journeys, per-request `X-Request-ID` correlation with status/duration on every log line (4xx warning, 5xx error), optional size-rotated file mirror (`LOG_TO_FILE`); 11 backend tests
- Generated production secrets
- Added comprehensive security documentation

---

**Last Updated:** October 11, 2026
**Version:** 1.1.0
