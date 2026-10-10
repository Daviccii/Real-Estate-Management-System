from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


# ============================================================================
# TENANT REGISTRATION & PROFILE
# ============================================================================

class TenantRegistrationPayload(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    preferred_locations: Optional[str] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    preferred_bedrooms: Optional[int] = None
    preferred_property_type: Optional[str] = None
    desired_move_in_date: Optional[str] = None
    household_size: Optional[int] = 1
    has_pets: Optional[str] = "no"
    employment_status: Optional[str] = None
    monthly_income: Optional[Any] = None
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator('password', mode='before')
    @classmethod
    def check_password_length(cls, v):
        if v and len(str(v).encode('utf-8')) > 72:
            raise ValueError('password must be 72 bytes or fewer')
        return v


class TenantProfileOut(BaseModel):
    id: int
    user_id: int
    preferred_locations: Optional[str] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    preferred_bedrooms: Optional[int] = None
    preferred_property_type: Optional[str] = None
    desired_move_in_date: Optional[str] = None
    household_size: Optional[int] = 1
    has_pets: Optional[str] = "no"
    employment_status: Optional[str] = None
    monthly_income: Optional[str] = None
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# OWNER REGISTRATION & PROFILE
# ============================================================================

class OwnerRegistrationPayload(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    owner_type: Optional[str] = "individual"  # individual, company, trust, family
    company_name: Optional[str] = None
    tax_pin: Optional[str] = None
    national_id_number: Optional[str] = None
    payout_phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    emergency_contact: Optional[str] = None

    @field_validator('password', mode='before')
    @classmethod
    def check_password_length(cls, v):
        if v and len(str(v).encode('utf-8')) > 72:
            raise ValueError('password must be 72 bytes or fewer')
        return v


class OwnerProfileOut(BaseModel):
    id: int
    user_id: int
    owner_type: str
    company_name: Optional[str] = None
    tax_pin: Optional[str] = None
    national_id_number: Optional[str] = None
    payout_phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    emergency_contact: Optional[str] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AGENT REGISTRATION & PROFILE
# ============================================================================

class AgentRegistrationPayload(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    agency_name: Optional[str] = None
    license_number: Optional[str] = None
    operating_areas: Optional[str] = None
    specialties: Optional[str] = None
    years_experience: Optional[int] = 1
    bio: Optional[str] = None
    commission_rate: Optional[float] = 5.0

    @field_validator('password', mode='before')
    @classmethod
    def check_password_length(cls, v):
        if v and len(str(v).encode('utf-8')) > 72:
            raise ValueError('password must be 72 bytes or fewer')
        return v


class AgentProfileOut(BaseModel):
    id: int
    user_id: int
    agency_name: Optional[str] = None
    license_number: Optional[str] = None
    operating_areas: Optional[str] = None
    specialties: Optional[str] = None
    years_experience: Optional[int] = 1
    bio: Optional[str] = None
    commission_rate: Optional[float] = 5.0
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SERVICE PROVIDER REGISTRATION & PROFILE
# ============================================================================

class ProviderRegistrationPayload(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    business_name: str
    specialty: str  # plumbing, electrical, hvac, carpentry, painting, general
    license_number: Optional[str] = None
    hourly_rate: Optional[str] = "2500"
    years_experience: Optional[int] = 1
    bio: Optional[str] = None
    service_areas: Optional[str] = None

    @field_validator('password', mode='before')
    @classmethod
    def check_password_length(cls, v):
        if v and len(str(v).encode('utf-8')) > 72:
            raise ValueError('password must be 72 bytes or fewer')
        return v


class ProviderProfileOut(BaseModel):
    id: int
    user_id: int
    business_name: str
    specialty: str
    license_number: Optional[str] = None
    hourly_rate: Optional[str] = None
    years_experience: Optional[int] = 1
    rating: Optional[float] = 5.0
    bio: Optional[str] = None
    service_areas: Optional[str] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PROPERTY MANAGER PROVISIONING & PROFILE
# ============================================================================

class ManagerProvisionPayload(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    company_name: Optional[str] = None
    license_number: Optional[str] = None
    operating_areas: Optional[str] = None
    max_managed_units: Optional[int] = 50
    emergency_phone: Optional[str] = None

    @field_validator('password', mode='before')
    @classmethod
    def check_password_length(cls, v):
        if v and len(str(v).encode('utf-8')) > 72:
            raise ValueError('password must be 72 bytes or fewer')
        return v


class ManagerProfileOut(BaseModel):
    id: int
    user_id: int
    company_name: Optional[str] = None
    license_number: Optional[str] = None
    operating_areas: Optional[str] = None
    max_managed_units: Optional[int] = 50
    emergency_phone: Optional[str] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# UNIFIED AUTH / LOGIN / CURRENT USER SCHEMAS
# ============================================================================

class UserProfileSummary(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    roles: List[str]
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool
    dashboard_path: str
    tenant_profile: Optional[TenantProfileOut] = None
    owner_profile: Optional[OwnerProfileOut] = None
    agent_profile: Optional[AgentProfileOut] = None
    manager_profile: Optional[ManagerProfileOut] = None
    provider_profile: Optional[ProviderProfileOut] = None

    model_config = ConfigDict(from_attributes=True)


class AuthLoginResponse(BaseModel):
    access_token: str = ""
    token_type: str = "bearer"
    redirect_url: Optional[str] = None
    user: Optional[UserProfileSummary] = None
    # MFA challenge fields: set when the password was correct but a second
    # factor is required before a session is issued.
    mfa_required: bool = False
    mfa_setup_required: bool = False
    mfa_token: Optional[str] = None
    allowed_methods: Optional[List[str]] = None

