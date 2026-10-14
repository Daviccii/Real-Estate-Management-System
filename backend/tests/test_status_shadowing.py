"""
Regression tests for the query-parameter `status` shadowing bug.

Four list endpoints (payments, leases, maintenance x2, units) declared a
query parameter named `status`, which shadowed the imported fastapi `status`
module inside the function body. Any code path that then evaluated
`status.HTTP_*` — e.g. an owner hitting GET /payments/, or any 403/404 branch
of these routes — crashed with
"'NoneType' object has no attribute 'HTTP_403_FORBIDDEN'" and returned 500
instead of the intended 403/404. Fixed by renaming the parameter to
`status_filter` with `alias="status"`, so the wire contract is unchanged.
"""
import uuid

import pytest

from app.models.user import User

PASSWORD = "Str0ng!TestPass42"


@pytest.fixture()
def plain_user_headers(client):
    """Headers for a freshly registered, unprivileged user."""
    email = f"shadow_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.parametrize(
    "path,expected",
    [
        # Unprivileged role -> 403 branches that previously crashed with 500.
        ("/api/v1/payments/", 403),
        ("/api/v1/leases/", 403),
        ("/api/v1/maintenance/", 403),
        # Missing property -> 404 branch inside list_property_units.
        ("/api/v1/units/properties/999999/units", 404),
    ],
)
def test_guard_branches_return_clean_errors(client, plain_user_headers, path, expected):
    resp = client.get(path, headers=plain_user_headers)
    assert resp.status_code == expected, resp.text


def test_status_filter_query_param_still_works_for_admin(client, db_session):
    """The ?status= query parameter keeps its wire contract via alias."""
    email = f"shadow_admin_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    user = db_session.query(User).filter(User.email == email).first()
    user.role = "admin"
    db_session.commit()

    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp = client.get("/api/v1/payments/", params={"status": "pending"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert all(p["status"] == "pending" for p in resp.json())
