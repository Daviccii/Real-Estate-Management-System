"""
Fine-grained permission registry layered on the role system.

Roles remain the storage/admin model (users.role + roles_csv); permissions are
the capability vocabulary endpoints can require. ROLE_PERMISSIONS maps each
role to the permissions it grants by default; admin implicitly holds every
permission. Resource-level scoping (company, ownership) is still enforced by
the existing helpers in app.auth.roles — this layer answers "may this user
class do this kind of action at all".
"""
from typing import Dict, FrozenSet, List

# Permission vocabulary: <domain>:<action>
PERMISSION_CATALOG: Dict[str, str] = {
    "properties:read": "View property records",
    "properties:write": "Create and modify properties",
    "units:write": "Create and modify units",
    "leases:read": "View lease records",
    "leases:write": "Create and modify leases",
    "payments:read": "View payment records",
    "payments:write": "Create and modify payments and gateway charges",
    "maintenance:read": "View maintenance requests",
    "maintenance:write": "Manage the maintenance workflow",
    "documents:read": "Download generated documents",
    "users:manage": "Administer user accounts and roles",
    "admin:system": "System administration (reconciliation, retention, backups)",
}

_ALL_PERMISSIONS: FrozenSet[str] = frozenset(PERMISSION_CATALOG)

_ROLE_VIEW: FrozenSet[str] = frozenset(
    ["properties:read", "leases:read", "payments:read", "maintenance:read", "documents:read"]
)

ROLE_PERMISSIONS: Dict[str, FrozenSet[str]] = {
    "admin": _ALL_PERMISSIONS,
    "manager": _ROLE_VIEW
    | frozenset(
        ["properties:write", "units:write", "leases:write", "payments:write", "maintenance:write"]
    ),
    "owner": _ROLE_VIEW
    | frozenset(
        ["properties:write", "units:write", "leases:write", "payments:write", "maintenance:write"]
    ),
    "agent": _ROLE_VIEW,
    "tenant": frozenset(["leases:read", "payments:read", "maintenance:read", "documents:read"]),
    "service_provider": frozenset(["maintenance:read"]),
    "user": frozenset(),
}


def user_roles(user) -> List[str]:
    """Every role a user holds: primary role plus any roles_csv entries."""
    roles = []
    if getattr(user, "role", None):
        roles.append(user.role)
    roles_csv = getattr(user, "roles_csv", None)
    if roles_csv:
        for r in roles_csv.split(","):
            r = r.strip()
            if r and r not in roles:
                roles.append(r)
    return roles


def user_permissions(user) -> List[str]:
    """Union of permission grants across every role the user holds."""
    if getattr(user, "role", None) == "admin" or (
        getattr(user, "roles_csv", None) and "admin" in user_roles(user)
    ):
        return sorted(_ALL_PERMISSIONS)
    granted: set = set()
    for role in user_roles(user):
        granted |= ROLE_PERMISSIONS.get(role, frozenset())
    return sorted(granted)


def user_can(user, permission: str) -> bool:
    """Whether the user holds one permission."""
    return permission in user_permissions(user)


def unknown_permissions() -> List[str]:
    """Permissions referenced somewhere but absent from the catalog (drift guard)."""
    referenced: set = set()
    for grants in ROLE_PERMISSIONS.values():
        referenced |= grants
    return sorted(referenced - _ALL_PERMISSIONS)
