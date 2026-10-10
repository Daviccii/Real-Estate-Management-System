"""Remove legacy test rows from the dev SQLite database (dry-run by default).

Before the pytest suite was isolated to in-memory SQLite, the old tests ran
against the real dev database and left @example.com users plus their
properties/units/leases/payments/maintenance rows behind.

Usage:
    python scripts/cleanup_legacy_test_data.py            # dry-run (rolls back)
    python scripts/cleanup_legacy_test_data.py --apply    # backup + commit
"""
from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = BASE_DIR / "database.db"
CHUNK = 400

JUNK_EMAIL_RE = re.compile(r"^(lease|maint|pay|prop|unit|user)_[a-z0-9_]*@example\.com$")
KEEP_EMAILS = (
    "kebirogabriel@gmail.com",
    "manager@realestate.com",
    "owner@realestate.com",
    "agent@realestate.com",
    "tenant@realestate.com",
    "provider@realestate.com",
)

DELETED: list[tuple[str, int]] = []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="path to the SQLite database")
    parser.add_argument("--apply", action="store_true", help="commit changes (default: dry-run)")
    return parser.parse_args()


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        is not None
    )


def columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')]


def delete_ids(conn: sqlite3.Connection, table: str, ids) -> int:
    ids = list(ids)
    total = 0
    for start in range(0, len(ids), CHUNK):
        part = ids[start : start + CHUNK]
        placeholders = ",".join("?" * len(part))
        total += conn.execute(f'DELETE FROM "{table}" WHERE id IN ({placeholders})', part).rowcount
    if total:
        DELETED.append((table, total))
    return total


def val(row, index, col):
    pos = index.get(col)
    return row[pos] if pos is not None else None


def purge(conn: sqlite3.Connection, table: str, predicate) -> int:
    """Delete rows of `table` (by id) whose fetched row matches the predicate."""
    if not table_exists(conn, table):
        return 0
    index = {name: pos for pos, name in enumerate(columns(conn, table))}
    rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
    victims = [row[index["id"]] for row in rows if predicate(row, index)]
    return delete_ids(conn, table, victims)


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"error: database not found: {db_path}")
        return 1

    if args.apply:
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = backup_dir / f"{db_path.name}.pre-cleanup-{stamp}.bak"
        shutil.copy2(db_path, backup)
        print(f"backup written: {backup}")

    conn = sqlite3.connect(db_path)
    conn.isolation_level = None
    conn.execute("PRAGMA busy_timeout=5000")

    mode = "APPLY" if args.apply else "DRY RUN (rolled back)"
    print(f"mode: {mode}  db: {db_path}")

    def fk_violations():
        return conn.execute("PRAGMA foreign_key_check").fetchall()

    pre_violations = fk_violations()

    conn.execute("BEGIN")
    try:
        users = conn.execute("SELECT id, email FROM users").fetchall()
        junk_users = [uid for uid, email in users if JUNK_EMAIL_RE.match(email or "")]
        odd = [
            email
            for _, email in users
            if email and email.endswith("@example.com") and not JUNK_EMAIL_RE.match(email)
        ]
        if odd:
            print(f"ABORT: unrecognized @example.com users (extend the rules first): {odd[:10]}")
            return 1
        if not junk_users:
            print("nothing to clean: no junk users found")
            return 0
        junk_user_set = set(junk_users)

        props = conn.execute("SELECT id, owner_id, name FROM properties").fetchall()
        junk_props = [
            pid
            for pid, owner, name in props
            if owner in junk_user_set
            or (name or "").startswith(("Test Property", "User1 Property"))
        ]
        junk_prop_set = set(junk_props)

        junk_units = [
            uid for uid, pid in conn.execute("SELECT id, property_id FROM units")
            if pid in junk_prop_set
        ]
        junk_unit_set = set(junk_units)

        junk_leases = [
            lid
            for lid, tid, pid, uid in conn.execute(
                "SELECT id, tenant_id, property_id, unit_id FROM leases"
            )
            if tid in junk_user_set or pid in junk_prop_set or uid in junk_unit_set
        ]
        junk_lease_set = set(junk_leases)

        junk_maint = [
            mid
            for mid, tid, pid, uid in conn.execute(
                "SELECT id, tenant_id, property_id, unit_id FROM maintenance"
            )
            if tid in junk_user_set or pid in junk_prop_set or uid in junk_unit_set
        ]
        junk_maint_set = set(junk_maint)

        junk_payments = [
            pay_id
            for pay_id, tid, pid, uid, lid in conn.execute(
                "SELECT id, tenant_id, property_id, unit_id, lease_id FROM payments"
            )
            if tid in junk_user_set
            or pid in junk_prop_set
            or uid in junk_unit_set
            or lid in junk_lease_set
        ]

        print(
            f"junk users: {len(junk_users)}/{len(users)}  properties: {len(junk_props)}/{len(props)}  "
            f"units: {len(junk_units)}  leases: {len(junk_leases)}  "
            f"maintenance: {len(junk_maint)}  payments: {len(junk_payments)}"
        )
        name_by_id = {pid: name for pid, _, name in props}
        for pid in junk_props[:6]:
            print(f"  junk property {pid}: {name_by_id[pid]}")

        # --- dependent rows first (no FK enforcement; explicit order) ---
        junk_ver: list[int] = []
        if table_exists(conn, "verification_records"):
            index = {n: i for i, n in enumerate(columns(conn, "verification_records"))}
            for row in conn.execute("SELECT * FROM verification_records"):
                entity_type = val(row, index, "entity_type")
                entity_id = val(row, index, "entity_id")
                if (
                    (entity_type == "user" and entity_id in junk_user_set)
                    or (entity_type == "property" and entity_id in junk_prop_set)
                    or val(row, index, "reviewed_by_id") in junk_user_set
                ):
                    junk_ver.append(row[index["id"]])
        if junk_ver and table_exists(conn, "verification_evidence"):
            index = {n: i for i, n in enumerate(columns(conn, "verification_evidence"))}
            ids = [
                row[index["id"]]
                for row in conn.execute("SELECT * FROM verification_evidence")
                if val(row, index, "verification_id") in set(junk_ver)
                or val(row, index, "created_by_id") in junk_user_set
            ]
            delete_ids(conn, "verification_evidence", ids)
        delete_ids(conn, "verification_records", junk_ver)

        purge(
            conn,
            "provider_invoices",
            lambda r, ix: val(r, ix, "maintenance_id") in junk_maint_set
            or val(r, ix, "provider_id") in junk_user_set,
        )
        purge(
            conn,
            "provider_ratings",
            lambda r, ix: val(r, ix, "maintenance_id") in junk_maint_set
            or val(r, ix, "reviewer_id") in junk_user_set,
        )
        purge(
            conn,
            "maintenance_work_orders",
            lambda r, ix: val(r, ix, "maintenance_id") in junk_maint_set
            or val(r, ix, "provider_id") in junk_user_set,
        )
        purge(
            conn,
            "maintenance_quotes",
            lambda r, ix: val(r, ix, "maintenance_id") in junk_maint_set
            or val(r, ix, "provider_id") in junk_user_set,
        )
        purge(
            conn,
            "inspection_records",
            lambda r, ix: val(r, ix, "lease_id") in junk_lease_set
            or val(r, ix, "property_id") in junk_prop_set
            or val(r, ix, "unit_id") in junk_unit_set
            or val(r, ix, "inspector_id") in junk_user_set,
        )
        purge(
            conn,
            "owner_expenses",
            lambda r, ix: val(r, ix, "owner_id") in junk_user_set
            or val(r, ix, "property_id") in junk_prop_set,
        )
        purge(
            conn,
            "leads",
            lambda r, ix: val(r, ix, "prospect_id") in junk_user_set
            or val(r, ix, "property_id") in junk_prop_set
            or val(r, ix, "agent_id") in junk_user_set,
        )
        purge(
            conn,
            "rental_applications",
            lambda r, ix: val(r, ix, "applicant_id") in junk_user_set
            or val(r, ix, "property_id") in junk_prop_set
            or val(r, ix, "unit_id") in junk_unit_set,
        )
        purge(
            conn,
            "viewings",
            lambda r, ix: val(r, ix, "prospect_id") in junk_user_set
            or val(r, ix, "property_id") in junk_prop_set
            or val(r, ix, "unit_id") in junk_unit_set
            or val(r, ix, "host_user_id") in junk_user_set,
        )

        for table, col in (
            ("favorites", "user_id"),
            ("inquiries", "user_id"),
            ("notifications", "recipient_id"),
            ("email_verifications", "user_id"),
            ("password_history", "user_id"),
            ("password_reset_tokens", "user_id"),
            ("mfa_recovery_codes", "user_id"),
            ("mfa_sms_challenges", "user_id"),
            ("messages", "sender_id"),
            ("conversation_participants", "user_id"),
            ("company_invitations", "invited_by_id"),
            ("agent_profiles", "user_id"),
            ("manager_profiles", "user_id"),
            ("owner_profiles", "user_id"),
            ("tenant_profiles", "user_id"),
            ("service_provider_profiles", "user_id"),
            ("audit_logs", "actor_id"),
        ):
            purge(conn, table, lambda r, ix, col=col: val(r, ix, col) in junk_user_set)

        purge(conn, "conversations", lambda r, ix: val(r, ix, "property_id") in junk_prop_set)
        purge(conn, "buildings", lambda r, ix: val(r, ix, "property_id") in junk_prop_set)
        purge(conn, "property_media", lambda r, ix: val(r, ix, "property_id") in junk_prop_set)

        delete_ids(conn, "payments", junk_payments)
        delete_ids(conn, "maintenance", junk_maint)
        delete_ids(conn, "leases", junk_leases)
        delete_ids(conn, "units", junk_units)

        # Kept rows that still reference junk entities: apply the schema's own
        # SET NULL semantics (e.g. maintenance.assigned_manager_id -> users).
        parent_sets = {
            "users": junk_user_set,
            "properties": junk_prop_set,
            "units": junk_unit_set,
            "leases": junk_lease_set,
            "maintenance": junk_maint_set,
        }
        normalized = 0
        all_tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        for table in all_tables:
            for fk in conn.execute(f'PRAGMA foreign_key_list("{table}")'):
                parent, child_col, on_delete = fk[2], fk[3], fk[6]
                ids = parent_sets.get(parent)
                if not ids or on_delete != "SET NULL":
                    continue
                ids = list(ids)
                for start in range(0, len(ids), CHUNK):
                    part = ids[start : start + CHUNK]
                    placeholders = ",".join("?" * len(part))
                    normalized += conn.execute(
                        f'UPDATE "{table}" SET "{child_col}" = NULL '
                        f'WHERE "{child_col}" IN ({placeholders})',
                        part,
                    ).rowcount
        if normalized:
            print(f"nulled {normalized} dangling SET NULL references on kept rows")

        delete_ids(conn, "properties", junk_props)
        delete_ids(conn, "users", junk_users)

        # --- verification ---
        remaining_users = conn.execute("SELECT id, email, role FROM users ORDER BY id").fetchall()
        post_violations = fk_violations()

        print("\n--- deleted rows ---")
        if DELETED:
            for table, count in DELETED:
                print(f"  {table}: {count}")
        else:
            print("  nothing to delete")

        print(f"\n--- FK audit: before={len(pre_violations)} after={len(post_violations)} ---")
        for row in post_violations[:20]:
            print("  violation:", row)

        print("\n--- remaining ---")
        print(f"  users: {len(remaining_users)}")
        for row in remaining_users:
            print("   ", row)
        for table in ("properties", "units", "leases", "payments", "maintenance", "buildings"):
            count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            print(f"  {table}: {count}")
        kept_props = [row[0] for row in conn.execute("SELECT name FROM properties ORDER BY id")]
        print(f"  kept property names ({len(kept_props)}):")
        for name in kept_props[:80]:
            print("   ", name)

        problems: list[str] = []
        if len(remaining_users) != len(KEEP_EMAILS):
            problems.append(f"expected {len(KEEP_EMAILS)} users, found {len(remaining_users)}")
        emails = {email for _, email, _ in remaining_users}
        missing = set(KEEP_EMAILS) - emails
        if missing:
            problems.append(f"missing keep-list accounts: {sorted(missing)}")
        for table, ids in (
            ("users", junk_users),
            ("properties", junk_props),
            ("units", junk_units),
            ("leases", junk_leases),
            ("payments", junk_payments),
            ("maintenance", junk_maint),
        ):
            left = 0
            for start in range(0, len(ids), CHUNK):
                part = list(ids)[start : start + CHUNK]
                placeholders = ",".join("?" * len(part))
                left += conn.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE id IN ({placeholders})', part
                ).fetchone()[0]
            if left:
                problems.append(f"{table}: {left} junk rows still present")
        if len(post_violations) > len(pre_violations):
            problems.append(
                f"foreign_key_check grew: {len(pre_violations)} -> {len(post_violations)}"
            )

        if problems:
            print("\nPROBLEMS:")
            for problem in problems:
                print("  -", problem)
            conn.execute("ROLLBACK")
            print("rolled back - nothing was changed")
            return 1

        if args.apply:
            conn.execute("COMMIT")
            print("\ncommitted")
        else:
            conn.execute("ROLLBACK")
            print("\ndry run complete - rolled back (use --apply to commit)")
        return 0
    except BaseException:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
