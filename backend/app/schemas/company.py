from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field
from .base import ApiSchema


class CompanyCreate(ApiSchema):
    name: str = Field(min_length=2, max_length=255)


class CompanyOut(ApiSchema):
    id: int
    name: str
    slug: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvitationCreate(ApiSchema):
    email: EmailStr
    role: str = Field(pattern="^(tenant|agent|owner|manager|service_provider|user)$")
    expires_in_days: int = Field(default=7, ge=1, le=30)


class InvitationOut(ApiSchema):
    id: int
    email: EmailStr
    role: str
    expires_at: datetime
    token: str


class InvitationAccept(ApiSchema):
    token: str = Field(min_length=32)
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=255)
