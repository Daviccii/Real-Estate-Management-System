import pytest
from fastapi import status


def test_tenant_registration_creates_profile(client):
    payload = {
        "email": "tenant.test@example.com",
        "password": "Str0ng!TestPass42",
        "full_name": "Test Tenant",
        "phone": "+254711000111",
        "preferred_locations": "Westlands, Kilimani",
        "min_budget": 45000,
        "max_budget": 85000,
        "preferred_bedrooms": 2,
        "preferred_property_type": "apartment",
        "household_size": 2,
        "has_pets": "no",
        "employment_status": "employed",
        "monthly_income": 150000,
        "employer_name": "Acme Kenya Ltd",
        "job_title": "Software Engineer"
    }
    res = client.post("/api/auth/register/tenant", json=payload)
    print("STATUS:", res.status_code, "BODY:", res.json())
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert "access_token" in data
    assert data["redirect_url"] == "/tenant"
    assert data["user"]["role"] == "tenant"
    assert data["user"]["tenant_profile"] is not None
    assert data["user"]["tenant_profile"]["min_budget"] == 45000
    assert data["user"]["tenant_profile"]["max_budget"] == 85000


def test_owner_registration_creates_profile(client):
    payload = {
        "email": "owner.test@example.com",
        "password": "Str0ng!TestPass42",
        "full_name": "Test Landlord",
        "phone": "+254722000222",
        "owner_type": "company",
        "company_name": "Apex Properties Ltd",
        "tax_pin": "P051234567Z",
        "national_id_number": "12345678",
        "payout_phone": "+254722000222",
        "bank_name": "Equity Bank",
        "bank_account_number": "0123456789",
        "emergency_contact": "Jane Landlord (+254733000333)"
    }
    res = client.post("/api/auth/register/owner", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert "access_token" in data
    assert data["redirect_url"] == "/owner"
    assert data["user"]["role"] == "owner"
    assert data["user"]["owner_profile"] is not None
    assert data["user"]["owner_profile"]["company_name"] == "Apex Properties Ltd"
    assert data["user"]["owner_profile"]["tax_pin"] == "P051234567Z"


def test_agent_registration_creates_profile(client):
    payload = {
        "email": "agent.test@example.com",
        "password": "Str0ng!TestPass42",
        "full_name": "Agent Smith",
        "phone": "+254733000444",
        "agency_name": "Nairobi Premier Realty",
        "license_number": "EARB/2024/9912",
        "operating_areas": "Westlands, Riverside",
        "specialties": "Luxury Condos & Apartments",
        "years_experience": 5,
        "bio": "Top realtor specializing in residential investments.",
        "commission_rate": 5.0
    }
    res = client.post("/api/auth/register/agent", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert "access_token" in data
    assert data["redirect_url"] == "/agent"
    assert data["user"]["role"] == "agent"
    assert data["user"]["agent_profile"] is not None
    assert data["user"]["agent_profile"]["license_number"] == "EARB/2024/9912"


def test_provider_registration_creates_profile(client):
    payload = {
        "email": "provider.test@example.com",
        "password": "Str0ng!TestPass42",
        "full_name": "John Plumber",
        "phone": "+254744000555",
        "business_name": "Nairobi Pro Plumbing",
        "specialty": "plumbing",
        "license_number": "NCA-PL-1234",
        "hourly_rate": "3000",
        "years_experience": 4,
        "service_areas": "Nairobi Metropolitan",
        "bio": "Certified commercial and residential plumbing."
    }
    res = client.post("/api/auth/register/provider", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert "access_token" in data
    assert data["redirect_url"] == "/provider"
    assert data["user"]["role"] == "service_provider"
    assert data["user"]["provider_profile"] is not None
    assert data["user"]["provider_profile"]["specialty"] == "plumbing"


def test_public_registration_rejects_admin_and_manager_role_escalation(client):
    admin_payload = {
        "email": "hacker.admin@example.com",
        "password": "Str0ng!TestPass42",
        "full_name": "Fake Admin",
        "role": "admin"
    }
    res = client.post("/api/auth/register", json=admin_payload)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in res.json()["detail"].lower()

    manager_payload = {
        "email": "fake.manager@example.com",
        "password": "Str0ng!TestPass42",
        "full_name": "Fake Manager",
        "role": "manager"
    }
    res_mgr = client.post("/api/auth/register", json=manager_payload)
    assert res_mgr.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in res_mgr.json()["detail"].lower()


def test_admin_provision_manager_flow(client, db_session):
    from app.models.user import User
    from app.auth.roles import require_admin
    from app.main import app

    admin_user = User(
        email="superadmin@propnoxa.test",
        hashed_password="hashed_pwd",
        full_name="Super Admin",
        role="admin",
        roles_csv="admin",
        is_active=True,
        is_verified=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)

    app.dependency_overrides[require_admin] = lambda: admin_user

    provision_payload = {
        "email": "manager.provisioned@example.com",
        "password": "Str0ng!TestPass42",
        "full_name": "Authorized Manager",
        "phone": "+254755000666",
        "company_name": "Prime Asset Management",
        "license_number": "PAM-MGR-8899",
        "operating_areas": "Nairobi CBD, Westlands",
        "max_managed_units": 200,
        "emergency_phone": "+254755000666"
    }

    prov_res = client.post("/api/admin/provision-manager", json=provision_payload)
    assert prov_res.status_code == status.HTTP_201_CREATED
    prov_data = prov_res.json()
    assert prov_data["email"] == "manager.provisioned@example.com"
    assert prov_data["role"] == "manager"
    assert prov_data["is_verified"] is True
    assert prov_data["profile"]["company_name"] == "Prime Asset Management"

    app.dependency_overrides.pop(require_admin, None)

