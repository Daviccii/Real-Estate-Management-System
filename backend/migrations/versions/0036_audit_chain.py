"""tamper-evident audit chain

Adds prev_hash/entry_hash to audit_logs, seeds the audit_chain_state tip row,
and backfills the chain over every existing entry so verification has a
complete history to check.

Backfill uses a frozen copy of app/utils/audit_hash.py's canonicalization
(naive-UTC iso timestamps, sorted compact JSON, HMAC-SHA256 over
prev_hash + ":" + payload). It is copied rather than imported so that a later
change to the app's hashing rules can never retroactively alter what this
revision wrote. Requires an online connection (the backfill reads rows);
`alembic upgrade --sql` is not supported for this revision.

Revision ID: 0036_audit_chain
Revises: 0035_property_tours
Create Date: 2026-10-10
"""
import hashlib
import hmac
import json
from datetime import timezone

from alembic import op
import sqlalchemy as sa


revision = "0036_audit_chain"
down_revision = "0035_property_tours"
branch_labels = None
depends_on = None

GENESIS_PREV = "0" * 64


def _chain_key() -> bytes:
    # env.py already imports app.config.settings (which reads .env), so the
    # key this backfill uses is exactly the one the running app will use.
    from app.config.settings import settings

    return (settings.AUDIT_CHAIN_SECRET or settings.SECRET_KEY).encode("utf-8")


def _iso(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat()


def _entry_hash(key: bytes, prev_hash: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    message = f"{prev_hash}:{canonical}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("prev_hash", sa.String(length=64), nullable=True))
    op.add_column("audit_logs", sa.Column("entry_hash", sa.String(length=64), nullable=True))
    op.create_table(
        "audit_chain_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_entry_hash", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    key = _chain_key()
    bind = op.get_bind()
    audit = sa.table(
        "audit_logs",
        sa.column("id", sa.Integer),
        sa.column("actor_id", sa.Integer),
        sa.column("action", sa.String),
        sa.column("entity_type", sa.String),
        sa.column("entity_id", sa.Integer),
        sa.column("ip_address", sa.String),
        sa.column("user_agent", sa.String),
        sa.column("details_json", sa.Text),
        sa.column("created_at", sa.DateTime),
        sa.column("prev_hash", sa.String),
        sa.column("entry_hash", sa.String),
    )

    tip = None
    last_id = 0
    while True:
        rows = bind.execute(
            sa.select(
                audit.c.id,
                audit.c.actor_id,
                audit.c.action,
                audit.c.entity_type,
                audit.c.entity_id,
                audit.c.ip_address,
                audit.c.user_agent,
                audit.c.details_json,
                audit.c.created_at,
            )
            .where(audit.c.id > last_id)
            .order_by(audit.c.id)
            .limit(1000)
        ).all()
        if not rows:
            break
        updates = []
        for row in rows:
            prev = tip if tip is not None else GENESIS_PREV
            payload = {
                "v": 1,
                "actor_id": row.actor_id,
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "ip_address": row.ip_address,
                "user_agent": row.user_agent,
                "details_json": row.details_json,
                "created_at": _iso(row.created_at),
            }
            entry_hash = _entry_hash(key, prev, payload)
            updates.append({"_id": row.id, "_prev": prev, "_hash": entry_hash})
            tip = entry_hash
            last_id = row.id
        bind.execute(
            audit.update()
            .where(audit.c.id == sa.bindparam("_id"))
            .values(prev_hash=sa.bindparam("_prev"), entry_hash=sa.bindparam("_hash")),
            updates,
        )

    chain_state = sa.table(
        "audit_chain_state",
        sa.column("id", sa.Integer),
        sa.column("last_entry_hash", sa.String),
    )
    bind.execute(chain_state.insert().values(id=1, last_entry_hash=tip))


def downgrade() -> None:
    op.drop_table("audit_chain_state")
    op.drop_column("audit_logs", "entry_hash")
    op.drop_column("audit_logs", "prev_hash")
