"""
Lease management API tests.
Tests for lease lifecycle, validation, and authorization.
"""
import uuid

import pytest
from datetime import datetime, timedelta, timezone

from app.models.user import User

PASSWORD = "Str0ng!TestPass42"


def _promote_admin(db_session, email):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = "admin"
    db_session.commit()
    db_session.refresh(user)


def test_create_and_get_lease(client, db_session):
    """Test creating and retrieving a lease."""
    # Create admin user
    admin_email = f"lease_admin_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _promote_admin(db_session, admin_email)

    # Create tenant user
    tenant_email = f"lease_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Login as admin
    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property and unit
    property_payload = {
        "name": "Test Property for Lease",
        "property_type": "apartment",
        "address": "123 Lease St",
        "city": "Leaseville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    unit_payload = {
        "property_id": property_id,
        "unit_number": "101",
        "unit_type": "1 bedroom",
        "bedrooms": 1,
        "bathrooms": 1,
        "area": "750 sqft",
        "rent": "1500",
        "status": "available"
    }
    resp = client.post('/api/units/', json=unit_payload, headers=admin_headers)
    unit_id = resp.json()['id']

    # Get tenant ID using admin endpoint (now that user has admin role)
    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    tenant_id = next(u['id'] for u in users if u['email'] == tenant_email)

    # Create lease
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=365)
    lease_payload = {
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "property_id": property_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "rent_amount": "1500",
        "deposit": "3000",
        "status": "active"
    }
    resp = client.post('/api/leases/', json=lease_payload, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['tenant_id'] == tenant_id
    lease_id = data['id']

    # Get the lease
    resp = client.get(f'/api/leases/{lease_id}', headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['id'] == lease_id


def test_lease_date_validation(client, db_session):
    """Test that lease dates are validated."""
    # Create admin user
    admin_email = f"lease_date_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _promote_admin(db_session, admin_email)

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property and unit
    property_payload = {
        "name": "Test Property for Date Validation",
        "property_type": "apartment",
        "address": "456 Date St",
        "city": "Dateville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    unit_payload = {
        "property_id": property_id,
        "unit_number": "201",
        "unit_type": "studio",
        "bedrooms": 0,
        "bathrooms": 1,
        "area": "500 sqft",
        "rent": "1200",
        "status": "available"
    }
    resp = client.post('/api/units/', json=unit_payload, headers=admin_headers)
    unit_id = resp.json()['id']

    # Get tenant ID using admin endpoint (now that user has admin role)
    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    tenant_id = users[0]['id']

    # Try to create lease with end date before start date
    start_date = datetime.now(timezone.utc)
    end_date = start_date - timedelta(days=30)
    lease_payload = {
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "property_id": property_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "rent_amount": "1200",
        "status": "draft"
    }
    resp = client.post('/api/leases/', json=lease_payload, headers=admin_headers)
    assert resp.status_code == 400


def test_conflicting_lease_validation(client, db_session):
    """Test that conflicting leases are prevented."""
    # Create admin user
    admin_email = f"lease_conflict_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _promote_admin(db_session, admin_email)

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property and unit
    property_payload = {
        "name": "Test Property for Conflict",
        "property_type": "apartment",
        "address": "789 Conflict St",
        "city": "Conflictville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    unit_payload = {
        "property_id": property_id,
        "unit_number": "301",
        "unit_type": "1 bedroom",
        "bedrooms": 1,
        "bathrooms": 1,
        "area": "750 sqft",
        "rent": "1500",
        "status": "available"
    }
    resp = client.post('/api/units/', json=unit_payload, headers=admin_headers)
    unit_id = resp.json()['id']

    # Get tenant ID using admin endpoint (now that user has admin role)
    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    tenant_id = users[0]['id']

    # Create first lease
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=365)
    lease_payload = {
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "property_id": property_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "rent_amount": "1500",
        "status": "active"
    }
    resp = client.post('/api/leases/', json=lease_payload, headers=admin_headers)
    assert resp.status_code == 201

    # Try to create conflicting lease
    conflict_start = start_date + timedelta(days=30)
    conflict_end = end_date + timedelta(days=30)
    conflict_payload = {
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "property_id": property_id,
        "start_date": conflict_start.isoformat(),
        "end_date": conflict_end.isoformat(),
        "rent_amount": "1600",
        "status": "draft"
    }
    resp = client.post('/api/leases/', json=conflict_payload, headers=admin_headers)
    assert resp.status_code == 400


def test_lease_authorization(client, db_session):
    """Test that tenants can only view their own leases."""
    # Create two tenants
    tenant1_email = f"lease_auth1_{uuid.uuid4().hex[:8]}@example.com"
    tenant2_email = f"lease_auth2_{uuid.uuid4().hex[:8]}@example.com"

    resp = client.post('/api/auth/register', json={"email": tenant1_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/register', json={"email": tenant2_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Create admin
    admin_email = f"lease_auth_admin_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _promote_admin(db_session, admin_email)

    # Login as admin and create lease for tenant1
    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    property_payload = {
        "name": "Test Property for Auth",
        "property_type": "apartment",
        "address": "999 Auth St",
        "city": "Authville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    unit_payload = {
        "property_id": property_id,
        "unit_number": "401",
        "unit_type": "studio",
        "bedrooms": 0,
        "bathrooms": 1,
        "area": "500 sqft",
        "rent": "1200",
        "status": "available"
    }
    resp = client.post('/api/units/', json=unit_payload, headers=admin_headers)
    unit_id = resp.json()['id']

    # Get tenant1 ID using admin endpoint (now that user has admin role)
    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    tenant1_id = next(u['id'] for u in users if u['email'] == tenant1_email)

    # Create lease for tenant1
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=365)
    lease_payload = {
        "tenant_id": tenant1_id,
        "unit_id": unit_id,
        "property_id": property_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "rent_amount": "1200",
        "status": "active"
    }
    resp = client.post('/api/leases/', json=lease_payload, headers=admin_headers)
    lease_id = resp.json()['id']

    # Login as tenant2 and try to access tenant1's lease
    resp = client.post('/api/auth/login', json={"email": tenant2_email, "password": PASSWORD})
    tenant2_access = resp.json().get('access_token')
    tenant2_headers = {"Authorization": f"Bearer {tenant2_access}"}

    resp = client.get(f'/api/leases/{lease_id}', headers=tenant2_headers)
    assert resp.status_code == 403


def test_lease_renewal(client, db_session):
    """Test lease renewal functionality."""
    # Create admin and tenant
    admin_email = f"lease_renew_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _promote_admin(db_session, admin_email)

    tenant_email = f"lease_renew_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property, unit, and lease
    property_payload = {
        "name": "Test Property for Renewal",
        "property_type": "apartment",
        "address": "555 Renew St",
        "city": "Renewville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    unit_payload = {
        "property_id": property_id,
        "unit_number": "501",
        "unit_type": "1 bedroom",
        "bedrooms": 1,
        "bathrooms": 1,
        "area": "750 sqft",
        "rent": "1500",
        "status": "available"
    }
    resp = client.post('/api/units/', json=unit_payload, headers=admin_headers)
    unit_id = resp.json()['id']

    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    tenant_id = next(u['id'] for u in users if u['email'] == tenant_email)

    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=180)
    lease_payload = {
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "property_id": property_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "rent_amount": "1500",
        "status": "active"
    }
    resp = client.post('/api/leases/', json=lease_payload, headers=admin_headers)
    lease_id = resp.json()['id']

    # Renew the lease
    new_end_date = end_date + timedelta(days=365)
    renewal_payload = {
        "new_end_date": new_end_date.isoformat(),
        "new_rent_amount": "1600",
        "notes": "Annual renewal with rent increase"
    }
    resp = client.post(f'/api/leases/{lease_id}/renew', json=renewal_payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == "renewed"
    assert data['rent_amount'] == "1600"


def test_lease_termination(client, db_session):
    """Test lease termination functionality."""
    # Create admin and tenant
    admin_email = f"lease_term_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _promote_admin(db_session, admin_email)

    tenant_email = f"lease_term_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property, unit, and lease
    property_payload = {
        "name": "Test Property for Termination",
        "property_type": "apartment",
        "address": "777 Term St",
        "city": "Termville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    unit_payload = {
        "property_id": property_id,
        "unit_number": "601",
        "unit_type": "studio",
        "bedrooms": 0,
        "bathrooms": 1,
        "area": "500 sqft",
        "rent": "1200",
        "status": "available"
    }
    resp = client.post('/api/units/', json=unit_payload, headers=admin_headers)
    unit_id = resp.json()['id']

    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    tenant_id = next(u['id'] for u in users if u['email'] == tenant_email)

    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=365)
    lease_payload = {
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "property_id": property_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "rent_amount": "1200",
        "status": "active"
    }
    resp = client.post('/api/leases/', json=lease_payload, headers=admin_headers)
    lease_id = resp.json()['id']

    # Terminate the lease
    termination_date = start_date + timedelta(days=90)
    termination_payload = {
        "termination_date": termination_date.isoformat(),
        "reason": "Early termination due to job relocation",
        "notes": "Tenant moving to another city"
    }
    resp = client.post(f'/api/leases/{lease_id}/terminate', json=termination_payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == "terminated"
