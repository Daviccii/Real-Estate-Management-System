from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserOut
from app.schemas.role_profiles import (
    TenantRegistrationPayload, TenantProfileOut,
    OwnerRegistrationPayload, OwnerProfileOut,
    AgentRegistrationPayload, AgentProfileOut,
    ProviderRegistrationPayload, ProviderProfileOut,
    ManagerProfileOut,
    UserProfileSummary, AuthLoginResponse
)
from app.models.user import User
from app.models.role_profiles import TenantProfile, OwnerProfile, AgentProfile, ManagerProfile
from app.models.service_marketplace import ServiceProviderProfile
from app.models.audit_log import AuditLog
from app.database.database import get_db
from app.utils.security import get_password_hash, verify_password, validate_password_strength
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.roles import get_current_user
from app.auth.permissions import user_permissions, user_roles
from app.config.settings import settings
from app.services.account_lockout import check_account_locked, record_failed_login_attempt, clear_failed_login_attempts
from app.services.security_events import emit_security_event
from app.services.token_revocation import revoke_all_user_tokens
from app.services.email_verification_service import send_verification_on_registration
from app.services.mfa_service import create_mfa_token
from app.observability.metrics import increment

router = APIRouter(prefix="/auth", tags=["auth"])


def get_dashboard_path(role: str) -> str:
    r = (role or "").lower()
    if r == "admin":
        return "/admin"
    if r == "manager":
        return "/manager"
    if r in ("owner", "landlord"):
        return "/owner"
    if r in ("agent", "realtor"):
        return "/agent"
    if r in ("service_provider", "contractor", "vendor"):
        return "/provider"
    return "/tenant"


def build_user_summary(db_user: User, db: Session) -> UserProfileSummary:
    roles = [r.strip() for r in db_user.roles_csv.split(",")] if db_user.roles_csv else [db_user.role or "user"]
    
    tp = db.query(TenantProfile).filter(TenantProfile.user_id == db_user.id).first()
    op = db.query(OwnerProfile).filter(OwnerProfile.user_id == db_user.id).first()
    ap = db.query(AgentProfile).filter(AgentProfile.user_id == db_user.id).first()
    mp = db.query(ManagerProfile).filter(ManagerProfile.user_id == db_user.id).first()
    sp = db.query(ServiceProviderProfile).filter(ServiceProviderProfile.user_id == db_user.id).first()

    return UserProfileSummary(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        role=db_user.role,
        roles=roles,
        phone=db_user.phone,
        avatar_url=db_user.avatar_url,
        is_verified=bool(db_user.is_verified),
        dashboard_path=get_dashboard_path(db_user.role),
        tenant_profile=TenantProfileOut.model_validate(tp) if tp else None,
        owner_profile=OwnerProfileOut.model_validate(op) if op else None,
        agent_profile=AgentProfileOut.model_validate(ap) if ap else None,
        manager_profile=ManagerProfileOut.model_validate(mp) if mp else None,
        provider_profile=ProviderProfileOut.model_validate(sp) if sp else None,
    )


# ============================================================================
# ROLE-SPECIFIC REGISTRATION ENDPOINTS
# ============================================================================

@router.post("/register/tenant", response_model=AuthLoginResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(payload: TenantRegistrationPayload, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(payload.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    hashed = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed,
        full_name=payload.full_name,
        phone=payload.phone,
        role="tenant",
        roles_csv="tenant",
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    tenant_profile = TenantProfile(
        user_id=user.id,
        preferred_locations=payload.preferred_locations,
        min_budget=payload.min_budget,
        max_budget=payload.max_budget,
        preferred_bedrooms=payload.preferred_bedrooms,
        preferred_property_type=payload.preferred_property_type,
        desired_move_in_date=payload.desired_move_in_date,
        household_size=payload.household_size or 1,
        has_pets=payload.has_pets or "no",
        employment_status=payload.employment_status,
        monthly_income=str(payload.monthly_income) if payload.monthly_income is not None else None,
        employer_name=payload.employer_name,
        job_title=payload.job_title,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone
    )
    db.add(tenant_profile)
    
    # Audit log
    audit = AuditLog(
        actor_id=user.id,
        action="register_tenant",
        entity_type="user",
        entity_id=user.id,
        details_json=f"Tenant account registered: {user.email}"
    )
    db.add(audit)
    db.commit()

    # Send verification email
    send_verification_on_registration(db, user.id)

    access = create_access_token({"sub": str(user.id), "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
    )

    return {
        "access_token": access,
        "token_type": "bearer",
        "redirect_url": get_dashboard_path(user.role),
        "user": build_user_summary(user, db),
        "verification_required": True,
        "message": "Registration successful. Please check your email to verify your account."
    }


@router.post("/register/owner", response_model=AuthLoginResponse, status_code=status.HTTP_201_CREATED)
async def register_owner(payload: OwnerRegistrationPayload, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(payload.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    hashed = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed,
        full_name=payload.full_name,
        phone=payload.phone,
        role="owner",
        roles_csv="owner",
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    owner_profile = OwnerProfile(
        user_id=user.id,
        owner_type=payload.owner_type or "individual",
        company_name=payload.company_name,
        tax_pin=payload.tax_pin,
        national_id_number=payload.national_id_number,
        payout_phone=payload.payout_phone,
        bank_name=payload.bank_name,
        bank_account_number=payload.bank_account_number,
        bank_account_name=payload.bank_account_name,
        emergency_contact=payload.emergency_contact,
        is_verified=False
    )
    db.add(owner_profile)

    audit = AuditLog(
        actor_id=user.id,
        action="register_owner",
        entity_type="user",
        entity_id=user.id,
        details_json=f"Property Owner account registered: {user.email} (Type: {payload.owner_type})"
    )
    db.add(audit)
    db.commit()

    # Send verification email
    send_verification_on_registration(db, user.id)

    access = create_access_token({"sub": str(user.id), "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
    )

    return {
        "access_token": access,
        "token_type": "bearer",
        "redirect_url": get_dashboard_path(user.role),
        "user": build_user_summary(user, db),
        "verification_required": True,
        "message": "Registration successful. Please check your email to verify your account."
    }


@router.post("/register/agent", response_model=AuthLoginResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(payload: AgentRegistrationPayload, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(payload.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    hashed = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed,
        full_name=payload.full_name,
        phone=payload.phone,
        role="agent",
        roles_csv="agent",
        is_verified=False  # Must complete EARB document verification
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    agent_profile = AgentProfile(
        user_id=user.id,
        agency_name=payload.agency_name,
        license_number=payload.license_number,
        operating_areas=payload.operating_areas,
        specialties=payload.specialties,
        years_experience=payload.years_experience or 1,
        bio=payload.bio,
        commission_rate=payload.commission_rate or 5.0,
        is_verified=False
    )
    db.add(agent_profile)

    audit = AuditLog(
        actor_id=user.id,
        action="register_agent",
        entity_type="user",
        entity_id=user.id,
        details_json=f"Real Estate Agent registered: {user.email} (License: {payload.license_number or 'Pending'})"
    )
    db.add(audit)
    db.commit()

    # Send verification email
    send_verification_on_registration(db, user.id)

    access = create_access_token({"sub": str(user.id), "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
    )

    return {
        "access_token": access,
        "token_type": "bearer",
        "redirect_url": get_dashboard_path(user.role),
        "user": build_user_summary(user, db),
        "verification_required": True,
        "message": "Registration successful. Please check your email to verify your account."
    }


@router.post("/register/provider", response_model=AuthLoginResponse, status_code=status.HTTP_201_CREATED)
async def register_provider(payload: ProviderRegistrationPayload, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(payload.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    hashed = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed,
        full_name=payload.full_name,
        phone=payload.phone,
        role="service_provider",
        roles_csv="service_provider",
        is_verified=False  # Must submit NCA certificate
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    provider_profile = ServiceProviderProfile(
        user_id=user.id,
        business_name=payload.business_name,
        specialty=payload.specialty,
        license_number=payload.license_number,
        hourly_rate=payload.hourly_rate or "2500",
        years_experience=payload.years_experience or 1,
        bio=payload.bio,
        service_areas=payload.service_areas,
        is_verified=False
    )
    db.add(provider_profile)

    audit = AuditLog(
        actor_id=user.id,
        action="register_service_provider",
        entity_type="user",
        entity_id=user.id,
        details_json=f"Service Provider registered: {user.email} (Specialty: {payload.specialty})"
    )
    db.add(audit)
    db.commit()

    # Send verification email
    send_verification_on_registration(db, user.id)

    access = create_access_token({"sub": str(user.id), "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
    )

    return {
        "access_token": access,
        "token_type": "bearer",
        "redirect_url": get_dashboard_path(user.role),
        "user": build_user_summary(user, db),
        "verification_required": True,
        "message": "Registration successful. Please check your email to verify your account."
    }



# ============================================================================
# GENERIC PUBLIC REGISTRATION (Strictly forbids admin and manager promotion)
# ============================================================================

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Security constraint: Never allow self-promotion to admin or manager via public registration
    if user.role and user.role.lower() in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration as Administrator or Property Manager is not permitted. Please contact platform administration."
        )
    
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        hashed = get_password_hash(user.password)
    except ValueError:
        raise HTTPException(status_code=400, detail="Password validation failed")

    assigned_role = user.role or "user"
    db_user = User(
        email=user.email,
        hashed_password=hashed,
        full_name=user.full_name,
        role=assigned_role,
        roles_csv=assigned_role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ============================================================================
# LOGIN & SESSION MANAGEMENT
# ============================================================================

@router.post("/login", response_model=AuthLoginResponse)
async def login(user: UserCreate, response: Response, request: Request, db: Session = Depends(get_db)):
    # Check if account is locked before proceeding
    lockout_status = await check_account_locked(user.email)
    if lockout_status["locked"]:
        emit_security_event("auth.login_locked", request=request, actor=user.email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked due to too many failed login attempts. Try again after {lockout_status['lockout_until']}"
        )

    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        # Record failed login attempt
        await record_failed_login_attempt(user.email)
        emit_security_event("auth.login_failed", request=request, actor=user.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not db_user.is_active:
        emit_security_event("auth.login_suspended", request=request, user_id=db_user.id, actor=db_user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account has been suspended. Please contact administrator.")

    # Clear failed login attempts on successful login
    await clear_failed_login_attempts(user.email)

    # MFA: password alone is not enough once the account has a second factor,
    # or when the platform mandates MFA for admins and it isn't enrolled yet.
    mandatory_admin_setup = (
        settings.MFA_MANDATORY_FOR_ADMIN
        and db_user.role == "admin"
        and not db_user.mfa_enabled
    )
    if db_user.mfa_enabled or mandatory_admin_setup:
        mfa_token = create_mfa_token(db_user.id)
        increment("mfa_challenges_issued_total")
        emit_security_event(
            "auth.mfa_challenge_issued",
            request=request,
            user_id=db_user.id,
            actor=db_user.email,
            severity="info",
        )
        allowed_methods = []
        if db_user.mfa_enabled:
            allowed_methods = ["totp", "recovery"] + (["sms"] if db_user.phone else [])
        return {
            "access_token": "",
            "token_type": "bearer",
            "redirect_url": None,
            "user": None,
            "mfa_required": True,
            "mfa_setup_required": mandatory_admin_setup,
            "mfa_token": mfa_token,
            "allowed_methods": allowed_methods,
        }

    access = create_access_token({"sub": str(db_user.id), "role": db_user.role})
    refresh = create_refresh_token({"sub": str(db_user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
    )

    emit_security_event(
        "auth.login_success",
        request=request,
        user_id=db_user.id,
        actor=db_user.email,
        outcome="allowed",
        severity="info",
    )
    return {
        "access_token": access,
        "token_type": "bearer",
        "redirect_url": get_dashboard_path(db_user.role),
        "user": build_user_summary(db_user, db)
    }


@router.get("/me", response_model=UserProfileSummary)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_user_summary(current_user, db)


@router.get("/me/permissions")
def get_my_permissions(current_user: User = Depends(get_current_user)):
    """Effective roles and permissions for the authenticated user (for UI gating)."""
    return {"roles": user_roles(current_user), "permissions": user_permissions(current_user)}


@router.post("/refresh")
def refresh_token(response: Response, request: Request, db: Session = Depends(get_db)):
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = decode_token(refresh)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = int(payload.get("sub"))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    access = create_access_token({"sub": str(db_user.id), "role": db_user.role})
    return {"access_token": access, "token_type": "bearer", "user": build_user_summary(db_user, db)}


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout from all devices by revoking all user tokens.
    """
    # Revoke all tokens for this user
    await revoke_all_user_tokens(current_user.id)
    
    # Clear the refresh cookie
    response.delete_cookie("refresh_token")
    
    return {"message": "Successfully logged out from all devices"}
