"""
Centralized role-based authorization dependencies and resource-level scoping.

This module provides reusable role and permission checking dependencies for FastAPI routes.
All role validation is performed against the database, not JWT claims.

Security principle: The database is the authoritative source for user roles and permissions.
"""
from typing import List, Literal, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.permissions import user_can
from app.database.database import get_db
from app.models.user import User

# Valid roles in the PropNoxa ecosystem
VALID_ROLES: List[Literal["user", "tenant", "agent", "owner", "manager", "service_provider", "admin"]] = [
    "user", "tenant", "agent", "owner", "manager", "service_provider", "admin"
]


def user_has_any_role(user: User, allowed_roles: List[str]) -> bool:
    """Check if user has any of the allowed roles (supporting single and multi-role setups)."""
    if "admin" in allowed_roles and user.role == "admin":
        return True
    if user.role in allowed_roles:
        return True
    if hasattr(user, "roles_csv") and user.roles_csv:
        user_roles = [r.strip() for r in user.roles_csv.split(",")]
        for r in allowed_roles:
            if r in user_roles:
                return True
    return False


def require_role(allowed_roles: List[str]):
    """
    Dependency factory that creates a role-checking dependency.
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        db_user = db.query(User).filter(User.id == current_user.id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended or inactive"
            )

        # Admin always passes any role check
        if db_user.role == "admin" or user_has_any_role(db_user, allowed_roles):
            return db_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: one of {allowed_roles}"
        )

    return role_checker


# Pre-configured role dependencies for common use cases
require_admin = require_role(["admin"])
require_manager = require_role(["manager"])
require_owner = require_role(["owner"])
require_agent = require_role(["agent"])
require_tenant = require_role(["tenant"])
require_service_provider = require_role(["service_provider"])
require_user = require_role(["user", "tenant", "agent", "owner", "manager", "service_provider", "admin"])
require_staff = require_role(["agent", "manager", "owner", "admin"])
require_management = require_role(["owner", "manager", "admin"])


def require_role_or_self(allowed_roles: List[str]):
    """
    Dependency that allows access if user has required role OR is accessing their own data.
    """
    def role_or_self_checker(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        db_user = db.query(User).filter(User.id == current_user.id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended"
            )

        if db_user.role == "admin" or user_has_any_role(db_user, allowed_roles) or db_user.id == user_id:
            return db_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )

    return role_or_self_checker


def verify_role(user: User, allowed_roles: List[str]) -> bool:
    """Programmatically check if user has an allowed role."""
    return user_has_any_role(user, allowed_roles)


def require_permission(permission: str):
    """
    Dependency factory granting access only to users holding the fine-grained
    permission (per app.auth.permissions.ROLE_PERMISSIONS). Admin always passes.
    Resource-level scoping (company/ownership) stays the caller's job.
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        db_user = db.query(User).filter(User.id == current_user.id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        if not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended or inactive"
            )
        if user_can(db_user, permission):
            return db_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {permission}"
        )

    return permission_checker


def check_property_access(property_obj, user: User) -> bool:
    """Check if user has permission to manage or view this property as owner/manager/agent/admin."""
    if not property_obj or not user:
        return False
    if (
        getattr(property_obj, "company_id", None) is not None
        and getattr(user, "company_id", None) is not None
        and property_obj.company_id != user.company_id
    ):
        return False
    if user.role == "admin":
        return True
    if property_obj.owner_id == user.id:
        return True
    if getattr(property_obj, "manager_id", None) == user.id:
        return True
    if getattr(property_obj, "agent_id", None) == user.id:
        return True
    return False


def same_company(user: User, other: User) -> bool:
    """Return whether two users belong to the same explicit company."""
    if not user or not other:
        return False
    return (
        user.company_id is not None
        and other.company_id is not None
        and user.company_id == other.company_id
    )


def company_resource_access(user: User, resource) -> bool:
    """Allow legacy unscoped records, but reject explicit cross-company access."""
    if not user or not resource:
        return False
    resource_company_id = getattr(resource, "company_id", None)
    return resource_company_id is None or resource_company_id == user.company_id


def require_company_resource(user: User, resource, detail: str = "Resource not found") -> None:
    """Raise a not-found response when a resource belongs to another company."""
    if not company_resource_access(user, resource):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def check_application_access(application_obj, user: User) -> bool:
    """Check if user is the applicant, or property owner/manager/agent/admin."""
    if not application_obj or not user:
        return False
    if user.role == "admin":
        return True
    if application_obj.applicant_id == user.id:
        return True
    if getattr(application_obj, "property", None) and check_property_access(application_obj.property, user):
        return True
    return False


def check_lease_access(lease_obj, user: User) -> bool:
    """Check if user is the tenant on the lease, or property owner/manager/admin."""
    if not lease_obj or not user:
        return False
    if user.role == "admin":
        return True
    if lease_obj.tenant_id == user.id:
        return True
    if getattr(lease_obj, "unit", None) and getattr(lease_obj.unit, "property", None):
        return check_property_access(lease_obj.unit.property, user)
    return False
