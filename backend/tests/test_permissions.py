"""
Fine-grained permission granularity tests.
Covers the ROLE_PERMISSIONS registry, multi-role union via roles_csv, the
self-service /auth/me/permissions endpoint, and the admin catalog endpoint
gated by require_permission.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.permissions import (
    PERMISSION_CATALOG,
    ROLE_PERMISSIONS,
    unknown_permissions,
    user_can,
    user_permissions,
    user_roles,
)
from app.main import app
from app.models.user import User

client = TestClient(app)
PASSWORD = "Str0ng!TestPass42"


def _user(email, role, roles_csv=None):
    return User(
        email=email,
        hashed_password="not-a-real-hash",
        full_name="Perm Tester",
        role=role,
        roles_csv=roles_csv or role,
    )


def _set_role(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()
    db_session.refresh(user)


def _register_and_login(client, db_session, tag, role):
    email = f"perm_{tag}_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, email, role)
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    token = resp.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


def test_admin_holds_entire_catalog():
    user = _user("admin@example.com", "admin")
    assert user_permissions(user) == sorted(PERMISSION_CATALOG)


def test_manager_can_write_payments_but_not_manage_users():
    user = _user("manager@example.com", "manager")
    assert user_can(user, "payments:write") is True
    assert user_can(user, "properties:write") is True
    assert user_can(user, "users:manage") is False
    assert user_can(user, "admin:system") is False


def test_tenant_is_read_only_outside_maintenance():
    user = _user("tenant@example.com", "tenant")
    for perm in ("leases:read", "payments:read", "maintenance:read", "documents:read"):
        assert user_can(user, perm) is True
    for perm in ("payments:write", "properties:write", "users:manage", "maintenance:write"):
        assert user_can(user, perm) is False


def test_fresh_user_role_grants_nothing():
    user = _user("fresh@example.com", "user")
    assert user_permissions(user) == []


def test_roles_csv_unions_multi_role_grants():
    user = _user("multi@example.com", "tenant", roles_csv="tenant, manager")
    assert user_can(user, "payments:write") is True
    assert user_can(user, "users:manage") is False


def test_admin_via_roles_csv_holds_everything():
    user = _user("delegated@example.com", "user", roles_csv="tenant, admin")
    assert user_permissions(user) == sorted(PERMISSION_CATALOG)


def test_unknown_role_grants_nothing():
    user = _user("ghost@example.com", "wizard")
    assert user_permissions(user) == []
    assert user_can(user, "properties:read") is False


def test_user_roles_lists_primary_and_csv():
    user = _user("roles@example.com", "tenant", roles_csv="tenant, agent")
    assert user_roles(user) == ["tenant", "agent"]


def test_no_permission_drift_outside_catalog():
    assert unknown_permissions() == []
    assert set(ROLE_PERMISSIONS) == {
        "admin", "manager", "owner", "agent", "tenant", "service_provider", "user"
    }


def test_me_permissions_endpoint(client, db_session):
    headers = _register_and_login(client, db_session, "me", "manager")
    resp = client.get("/api/auth/me/permissions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "manager" in data["roles"]
    assert "payments:write" in data["permissions"]
    assert "users:manage" not in data["permissions"]


def test_me_permissions_requires_auth(client):
    resp = client.get("/api/auth/me/permissions")
    assert resp.status_code in (401, 403)


def test_admin_catalog_endpoint_and_permission_gate(client, db_session):
    admin_headers = _register_and_login(client, db_session, "cat_admin", "admin")
    resp = client.get("/api/admin/permissions/catalog", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    entries = {p["permission"]: p["description"] for p in data["permissions"]}
    assert entries == PERMISSION_CATALOG
    assert set(data["role_permissions"]) == set(ROLE_PERMISSIONS)

    tenant_headers = _register_and_login(client, db_session, "cat_tenant", "tenant")
    resp = client.get("/api/admin/permissions/catalog", headers=tenant_headers)
    assert resp.status_code == 403
