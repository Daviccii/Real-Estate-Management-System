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
- The backend and Docker jobs are gated behind a "backend sources tracked" check and skip with a `::notice::` until the gitlink is consolidated (below), so the pipeline stays green either way.

**Deploy workflow (`workflow_dispatch`):** re-runs the full CI via `workflow_call`, then promotes to the chosen GitHub Environment (`staging` or `production`). Protect `production` with required reviewers in *Repo settings → Environments* so a dispatch cannot ship without human approval. The deploy steps themselves are placeholders for the hosting command.

**One-time required step for backend CI (run locally, then push):**
The root repository tracks `backend/` as a bare gitlink (nested `.git`, no `.gitmodules`), so GitHub sees **no backend files at all** — backend tests, bandit, and Docker builds cannot run until the nested repository is consolidated into the root repo:
```bash
scripts/consolidate-backend-git.sh   # renames backend/.git aside (history preserved), stages backend/ as normal files, aborts if backend/.env would not stay ignored
git commit -m "Consolidate backend sources into root repository"
git push
```
Exact rollback steps are printed by the script (restore the gitlink + rename `backend/.git.pre-consolidation` back).

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

## Known Limitations

1. **Email Service:** Implemented — SMTP transport with branded HTML/text templates, preference-gated notification fan-out, and console fallback for dev. Production only needs `EMAIL_BACKEND=smtp` + relay credentials from a secrets manager. (SendGrid HTTP API integration remains optional future work; SMTP covers SES/Mailgun relays.)
2. **CSRF Protection:** Skipped as JWT-based API has sufficient protection.
3. **Password Reset:** Implemented (token-based, history-checked). Email delivery needs the production provider above.
4. **File Upload:** Implemented with local storage; virus scanning and S3/signed URLs pending.
5. **Monitoring:** Basic metrics/health/logging in place; Sentry/APM/alerting integrations pending.
6. **Backend repo consolidation pending:** `backend/` is still a nested git repository tracked as a gitlink, so GitHub sees no backend files. Backend CI, pip-audit, bandit, and Docker image jobs skip automatically until `scripts/consolidate-backend-git.sh` is run and the result is committed and pushed.
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

### October 10, 2026
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

**Last Updated:** October 10, 2026
**Version:** 1.1.0
