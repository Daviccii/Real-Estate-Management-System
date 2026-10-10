from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional
from datetime import datetime

from app.utils.sanitization import sanitize_string, detect_xss_attack


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "user"

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid = ["user", "tenant", "agent", "manager", "admin", "owner", "service_provider"]
        if v not in valid:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid)}")
        return v

    @field_validator('password', mode='before')
    @classmethod
    def check_password_length(cls, v):
        # ensure password is a string and not excessively long for bcrypt
        if v is None:
            return v
        if not isinstance(v, str):
            v = str(v)
        # bcrypt has a 72-byte input limit; reject long passwords with a clear message
        if len(v.encode('utf-8')) > 72:
            raise ValueError('password must be 72 bytes or fewer')
        return v

    @field_validator('full_name')
    @classmethod
    def sanitize_full_name(cls, v):
        if v is None:
            return v
        if detect_xss_attack(v):
            raise ValueError("Invalid characters detected in name")
        return sanitize_string(v, max_length=100)

class UserOut(BaseModel):
    id: int
    company_id: Optional[int] = None
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    role: str
    roles_csv: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: Optional[bool] = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
