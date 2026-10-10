# Deployment Guide — PropNoxa Real Estate Management System

Status snapshot: 2026-10-11, `main` at `7b17e32` (all of Priority 1–4 pushed and green).
This guide is the operational companion to `SECURITY_IMPROVEMENTS.md`.

Legend: `[x]` done and verified in the repo · `[~]` repo-side ready, needs infrastructure to complete · `[ ]` not yet done.

---

## 1. Deployment checklist

### Pre-Deployment

- [x] **All Priority 1 critical issues resolved** — P1–P4 complete. The only P1 skip is CSRF, deliberately skipped and documented (JWT bearer API, no cookie-based auth for state changes).
- [x] **Security audit completed** — this program of work; `SECURITY_IMPROVEMENTS.md` is the source of truth (MFA, rate limiting, lockout, uploads hardening, GDPR, audit chain, etc.).
- [ ] **Penetration testing** — not performed. Automated gates are green (bandit medium+, `pip-audit` advisory, `npm audit` blocking at high+ for prod deps); recommend an external engagement before public launch.
- [ ] **Load testing** — not performed. Perf work done (Redis cache-aside, read-replica routing, pool tuning, indexed hot paths); recommend k6 or Locust against the staging stack before launch.
- [x] **Database backups configured** — verified dumps, retention with a floor, optional secondary copy, WAL archiving + documented PITR plan, restore-drill tooling (`backend/scripts/backup_database.py`, `backend/scripts/restore_database.py`), and a `db-backup` daemon service in `docker-compose.yml`.
- [x] **Monitoring configured** — `/health/live`, `/health/ready`, `/health/metrics` (uptime, error rates, counters, system info), structured JSON logs to stdout (CloudWatch-ready), `security` event stream, `X-Request-ID` on every line. Sentry/APM integration pending.
- [ ] **Alerting configured** — no PagerDuty/Datadog wiring yet. Interim: CloudWatch alarms on 5xx rate, p95 latency, disk, and a poller on `/health/metrics`.
- [ ] **SSL/TLS certificates** — infrastructure step (ACM / Cloudflare edge). App already honors `--proxy-headers`.
- [ ] **DNS configured** — infrastructure step.
- [ ] **CDN configured** — infrastructure step; build artifacts are ready (hashed filenames, immutable caching support).
- [~] **Secrets management configured** — every secret is env-based, `.env` is gitignored/untracked, `backend/.env.example` + `backend/scripts/generate_secrets.py` exist. A production secrets manager (AWS Secrets Manager or equivalent) still needs provisioning. **The leaked admin password must be rotated (see §6).**
- [x] **CI/CD pipeline tested** — `.github/workflows/ci.yml` runs on push (5 jobs, see §3); `deploy.yml` is a dispatch-based promotion that re-runs CI as the gate. The Docker build job runs on GitHub runners — check the Actions tab; it has never executed on the dev machine (no Docker daemon).
- [~] **Staging environment tested** — promotion workflow + GitHub Environments exist; real staging infra is not provisioned. Closest stand-in today: the full `docker-compose` stack (Postgres + Redis + API + worker + backups).
- [x] **Data migration plan tested** — Alembic chain runs via the container `release` step (`entrypoint.sh` → `alembic upgrade head`), gated in compose by the `migrate` service. Backup-first pattern used for every dev-DB migration; the full chain replays on Postgres (one pre-existing Postgres-only migration means SQLite dev DBs must stamp past it — the full chain is a non-issue on Postgres).
- [~] **Rollback plan tested** — see §5. App rollback is image/dist swap; DB rollback is downgrade or restore + PITR; audit-chain verification re-run after any restore. Rehearse once on staging before launch.
- [x] **Incident response plan documented** — see §6.

### Deployment

- [x] **Database migrations run** — `docker compose run --rm migrate` (or the `release` entrypoint) before starting API containers.
- [ ] **Secrets injected** — from the secrets manager into container env at deploy time (full list in §4).
- [ ] **Application deployed** — commands are ready (§2), but `deploy.yml` deploy steps are placeholders until a hosting target is chosen.
- [x] **Health checks passing** — `/health/live` (liveness; also the Docker `HEALTHCHECK`), `/health/ready` (readiness, checks DB), `/health/metrics` (operational metrics).
- [~] **Smoke tests passing** — 264 backend + 263 frontend tests green pre-push; production smoke checklist in §2.
- [ ] **Monitoring verified / Alerts verified / DNS switched / SSL verified / Performance verified** — infrastructure steps, perform on launch day in this order.

### Post-Deployment

- [ ] **24-hour monitoring** — watch `/health/metrics`, 5xx rate, latency, and the `security` log stream for the first 24 h.
- [ ] **Error rate monitoring** — alert threshold suggested: 5xx > 1% for 5 min.
- [ ] **Performance monitoring** — p95 latency, DB pool saturation, Redis hit rate.
- [ ] **Security monitoring** — failed-login/lockout spikes, MFA failures, audit-chain verification (run `scripts/verify_audit_chain.py` after go-live).
- [ ] **User feedback collection** — iterate on the bug triage queue.
- [ ] **Bug triage** — hotfixes flow through the same CI gates (see §5).

---

## 2. Recommended architecture (as designed)

```
                    ┌──────────────────────┐
                    │  CDN (Cloudflare)    │  static frontend (dist/, hashed assets)
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Load Balancer (ALB) │  health checks → /health/ready
                    └──────────┬───────────┘
                        ┌──────┴──────┐
                    ┌───▼───┐     ┌───▼───┐
                    │ api-1 │     │ api-2 │  backend/Dockerfile (uvicorn, WORKERS)
                    └───┬───┘     └───┬───┘
                        └──────┬──────┘
                    ┌──────────▼───────────┐
                    │ PostgreSQL (RDS)     │  DATABASE_URL (+ DATABASE_REPLICA_URL)
                    │ Multi-AZ + replica   │
                    └──────────┬───────────┘
                    ┌──────────▼───────────┐
                    │ Redis (ElastiCache)  │  REDIS_URL (rate limiting, lockout, revocation)
                    └──────────────────────┘

Monitoring: Datadog APM (pending) · Sentry (pending) · CloudWatch Logs (ready:
JSON stdout) · PagerDuty alerting (pending; interim CloudWatch alarms)
```

Mapping to this codebase:

| Diagram box | What the repo provides | What you must add |
|---|---|---|
| CDN | `npm run build` → `dist/`, content-hashed assets, PWA service worker (auto-versioned caches) | Cloudflare/S3/R2 bucket + cache rules: hashed assets immutable; `index.html` and `sw.js` no-cache |
| Load balancer | `/health/live` liveness, `/health/ready` readiness | ALB target group → api task/service; stickiness not required (stateless JWT API) |
| 2× web/API | `backend/Dockerfile` (non-root, 12-factor), `entrypoint.sh release|run`, `WORKERS` env | ECS/EC2/K8s; run `release` once before rolling out replicas |
| PostgreSQL | SQLAlchemy + Alembic, pool sizing envs, `DATABASE_REPLICA_URL` read routing for public property endpoints | RDS Multi-AZ + read replica; `pg_dump` client major must match server (image ships v16 — match if you upgrade) |
| Redis | cache-aside + rate limit + account lockout + token revocation, graceful broken-Redis passthrough | ElastiCache; set `REDIS_URL` |
| Worker | `python -m app.worker` (compose `worker` service) | Long-running task container |
| Backups | `db-backup` daemon (dumps + retention + verify + WAL), `--pitr-plan` | Secondary copy to a bucket (`BACKUP_SECONDARY_DIR`) |
| Monitoring | JSON logs, `/health/metrics`, `security` event stream | Datadog/Sentry SDKs (pending), CloudWatch log shipping (container stdout), PagerDuty route |

---

## 3. CI/CD pipeline

`ci.yml` (runs on every push / PR):

1. **Frontend** — `npm ci` → typecheck → vitest with coverage → production build → Playwright e2e (artifacts uploaded).
2. **Backend sources tracked** — guards against re-introducing a nested-repo gitlink.
3. **Backend** — `pytest` (in-memory SQLite) → bandit medium+ (blocking) → pip-audit (advisory).
4. **Frontend dependency audit** — `npm audit --omit=dev --audit-level=high` (blocking); full tree moderate+ (advisory).
5. **Backend image build** — `docker build ./backend`.

`deploy.yml` (manual dispatch): choose `staging` or `production`; the workflow re-runs the full CI pipeline, then promotes **only on green** into the matching GitHub Environment. Protect the `production` environment with required reviewers so a dispatch cannot ship without human approval. The deploy steps are placeholders — replace them with your hosting command (`docker compose pull && up -d`, `kubectl set image`, PaaS CLI, ...).

---

## 4. Required environment variables (production)

From `backend/app/config/settings.py`; template in `backend/.env.example`.

| Variable | Notes |
|---|---|
| `ENVIRONMENT` | `production` (enables production-only guards) |
| `DEBUG` | `false` |
| `DATABASE_URL` | `postgresql://…` (RDS primary) |
| `DATABASE_REPLICA_URL` | optional read replica |
| `SECRET_KEY` | ≥32 chars, from secrets manager |
| `AUDIT_CHAIN_SECRET` | **write-once** HMAC key for the audit chain; changing it invalidates verification of every earlier entry — pin it in the secrets manager |
| `CORS_ORIGINS` | production frontend domains only |
| `REDIS_URL` | ElastiCache endpoint |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_PER_MINUTE` | `true` / e.g. `120` |
| `LOG_FORMAT` | `json` (for CloudWatch) |
| `MFA_MANDATORY_FOR_ADMIN` | set `true` in production |
| `EMAIL_BACKEND` / `SMTP_*` | `smtp` + relay credentials (fails fast if host missing) |
| `SMS_BACKEND` | `console` or `twilio` (twilio needs provider creds) |
| `PAYMENT_GATEWAY` | **`mock` is rejected in production.** Choose `stripe`/`paypal`/`mpesa` and set `PAYMENT_WEBHOOK_SECRET`, or leave payments off |
| `LEGAL_HOLD_ENABLED` / `RETENTION_*` | retention windows and litigation hold |
| `BACKUP_*` | backup dir, retention, secondary copy, WAL archive, physical base backups |
| `UPLOAD_DIR` / `DOCUMENTS_DIR` | **mount persistent storage** — containers have no volume for these in `docker-compose.yml` today |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` | only for the one-shot `scripts/setup_admin.py`; never store in code |

Frontend build-time: `VITE_API_BASE` (e.g. `https://api.your-domain.com`) — baked into `dist/` at `npm run build`.

---

## 5. Deploy, verify, roll back

### Deploy (Docker Compose reference; adapt to your target)

```bash
# 1. Backend
docker compose build api worker db-backup
docker compose run --rm migrate            # alembic upgrade head
docker compose up -d api worker db-backup

# 2. Frontend
VITE_API_BASE=https://api.your-domain.com npm ci && npm run build
# upload dist/ to CDN origin; keep index.html + sw.js short-lived, hashed assets immutable

# 3. Verify
curl -fsS https://api.your-domain.com/health/live
curl -fsS https://api.your-domain.com/health/ready
curl -fsS https://api.your-domain.com/health/metrics
python backend/scripts/verify_audit_chain.py     # expect {"verified": true, ...}
python backend/scripts/backup_database.py --status
```

Smoke tests after deploy: register/login (MFA challenge if enabled), public property listing + detail, AI match endpoint, one authenticated CRUD (e.g. create draft property), audit-logs chain verify (admin), `manifest.webmanifest` reachable via the CDN.

Operational crons: daily `scripts/run_retention.py` (prints a JSON report; honors legal hold), then `scripts/verify_audit_chain.py` to confirm pruning anchors kept the chain intact.

### Rollback

1. **App** — redeploy the previous image tag; redeploy the previous `dist/` build (hashed filenames make this safe). Migrations are additive across the P1–P4 set.
2. **Database** — `alembic downgrade -1` for the last revision, or restore from a verified dump (`scripts/restore_database.py`) plus WAL replay for point-in-time recovery (see `backup_database.py --pitr-plan`).
3. **After any restore** — re-run `scripts/verify_audit_chain.py`. A restore rewinds the chain tip together with the data, so verification should pass; if it does not, treat it as a tamper signal and investigate before serving traffic.
4. **Never rotate `AUDIT_CHAIN_SECRET`** during an incident — it would make every historical entry fail verification.

### Hotfix flow

Branch → fix → push → CI gates → dispatch `deploy.yml` → green promotion. No hotfix bypasses CI.

---

## 6. Incident response quick guide

| Scenario | First moves |
|---|---|
| Suspected audit tampering | `scripts/verify_audit_chain.py` (or `GET /api/v1/audit-logs/chain/verify` as admin). `first_broken` names the entry; cross-check with `security` logs by `X-Request-ID`. |
| Compromised account | Admin: revoke sessions (lockout + token revocation via Redis), force password reset, review `login`/`mfa` events. |
| Leaked credentials | Rotate in the secrets manager, redeploy with new env. Note: the old admin password for `kebirogabriel@gmail.com` is still in git history — **rotate it and never reuse it anywhere.** |
| Litigation / legal hold | Set `LEGAL_HOLD_ENABLED=true` — destructive purges (audit logs, notifications) suspend immediately; token cleanup continues. |
| DB incident | `backup_database.py --list` → pick verified dump → `restore_database.py` → re-verify audit chain. |
| Key compromise (`SECRET_KEY`) | Rotate → all access/refresh tokens become invalid (planned blast radius) → users re-login. Audit chain falls back cleanly only if `AUDIT_CHAIN_SECRET` was pinned separately — pin it. |

---

## 7. Outstanding manual actions before production

1. **Rotate the leaked admin password** (`kebirogabriel@gmail.com`) — still in git history, un-rotated as of 2026-10-11.
2. Provision a secrets manager and inject the §4 variables.
3. Choose the hosting target and fill in `deploy.yml` deploy commands; protect the `production` environment with reviewers.
4. Decide payments: real gateway credentials or leave `PAYMENT_GATEWAY` off (mock is rejected in production).
5. Real SMTP relay credentials (`EMAIL_BACKEND=smtp`).
6. Mount persistent volumes for `UPLOAD_DIR` / `DOCUMENTS_DIR` (property media, generated PDFs).
7. Schedule `run_retention.py` + `verify_audit_chain.py` (daily), and `backup_database.py --daemon` is already containerized.
8. Commission penetration testing and load testing before public launch.
9. Wire alerting (Datadog/Sentry/PagerDuty or interim CloudWatch alarms).
