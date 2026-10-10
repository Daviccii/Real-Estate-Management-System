"""
Payment management API tests.
Tests for payment tracking, financial overview, and authorization.
"""
import uuid

import pytest
from datetime import datetime, timedelta, timezone

from app.models.user import User

PASSWORD = "Str0ng!TestPass42"


def _set_role(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()
    db_session.refresh(user)


def test_create_and_get_payment(client, db_session):
    """Test creating and retrieving a payment."""
    # Create admin and tenant
    admin_email = f"pay_admin_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _set_role(db_session, admin_email, "admin")

    tenant_email = f"pay_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user tenant
    _set_role(db_session, tenant_email, "tenant")

    # Login as admin
    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property, unit, and lease
    property_payload = {
        "name": "Test Property for Payment",
        "property_type": "apartment",
        "address": "123 Payment St",
        "city": "Paymentville",
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
        "rent_amount": "1500",
        "status": "active"
    }
    resp = client.post('/api/leases/', json=lease_payload, headers=admin_headers)
    lease_id = resp.json()['id']

    # Create payment
    due_date = datetime.now(timezone.utc) + timedelta(days=30)
    payment_payload = {
        "tenant_id": tenant_id,
        "lease_id": lease_id,
        "property_id": property_id,
        "unit_id": unit_id,
        "amount": "1500",
        "due_date": due_date.isoformat(),
        "payment_type": "rent",
        "status": "pending"
    }
    resp = client.post('/api/payments/', json=payment_payload, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['amount'] == "1500"
    payment_id = data['id']

    # Get the payment
    resp = client.get(f'/api/payments/{payment_id}', headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['id'] == payment_id


def test_payment_authorization(client, db_session):
    """Test that tenants can only view their own payments."""
    # Create two tenants
    tenant1_email = f"pay_auth1_{uuid.uuid4().hex[:8]}@example.com"
    tenant2_email = f"pay_auth2_{uuid.uuid4().hex[:8]}@example.com"

    resp = client.post('/api/auth/register', json={"email": tenant1_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, tenant1_email, "tenant")

    resp = client.post('/api/auth/register', json={"email": tenant2_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, tenant2_email, "tenant")

    # Create admin
    admin_email = f"pay_auth_admin_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _set_role(db_session, admin_email, "admin")

    # Login as admin and create payment for tenant1
    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    property_payload = {
        "name": "Test Property for Payment Auth",
        "property_type": "apartment",
        "address": "456 Auth St",
        "city": "Authville",
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

    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    tenant_id = next(u['id'] for u in users if u['email'] == tenant1_email)

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

    due_date = datetime.now(timezone.utc) + timedelta(days=30)
    payment_payload = {
        "tenant_id": tenant_id,
        "lease_id": lease_id,
        "property_id": property_id,
        "unit_id": unit_id,
        "amount": "1200",
        "due_date": due_date.isoformat(),
        "payment_type": "rent",
        "status": "pending"
    }
    resp = client.post('/api/payments/', json=payment_payload, headers=admin_headers)
    payment_id = resp.json()['id']

    # Login as tenant2 and try to access tenant1's payment
    resp = client.post('/api/auth/login', json={"email": tenant2_email, "password": PASSWORD})
    tenant2_access = resp.json().get('access_token')
    tenant2_headers = {"Authorization": f"Bearer {tenant2_access}"}

    resp = client.get(f'/api/payments/{payment_id}', headers=tenant2_headers)
    assert resp.status_code == 403


def test_payment_status_update(client, db_session):
    """Test updating payment status."""
    # Create admin and tenant
    admin_email = f"pay_status_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _set_role(db_session, admin_email, "admin")

    tenant_email = f"pay_status_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user tenant
    _set_role(db_session, tenant_email, "tenant")

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property, unit, lease, and payment
    property_payload = {
        "name": "Test Property for Status",
        "property_type": "apartment",
        "address": "789 Status St",
        "city": "Statusville",
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
        "rent_amount": "1500",
        "status": "active"
    }
    resp = client.post('/api/leases/', json=lease_payload, headers=admin_headers)
    lease_id = resp.json()['id']

    due_date = datetime.now(timezone.utc) + timedelta(days=30)
    payment_payload = {
        "tenant_id": tenant_id,
        "lease_id": lease_id,
        "property_id": property_id,
        "unit_id": unit_id,
        "amount": "1500",
        "due_date": due_date.isoformat(),
        "payment_type": "rent",
        "status": "pending"
    }
    resp = client.post('/api/payments/', json=payment_payload, headers=admin_headers)
    payment_id = resp.json()['id']

    # Update payment status to paid
    update_payload = {
        "status": "paid",
        "payment_date": datetime.now(timezone.utc).isoformat(),
        "payment_method": "bank_transfer",
        "reference": "TXN123456"
    }
    resp = client.put(f'/api/payments/{payment_id}', json=update_payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == "paid"
    assert data['payment_method'] == "bank_transfer"


def test_payment_overview(client, db_session):
    """Test financial overview endpoint."""
    # Create admin and tenant
    admin_email = f"pay_overview_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _set_role(db_session, admin_email, "admin")

    tenant_email = f"pay_overview_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user tenant
    _set_role(db_session, tenant_email, "tenant")

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property, unit, lease, and multiple payments
    property_payload = {
        "name": "Test Property for Overview",
        "property_type": "apartment",
        "address": "999 Overview St",
        "city": "Overviewville",
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

    # Create paid payment
    due_date = datetime.now(timezone.utc) + timedelta(days=30)
    payment_payload = {
        "tenant_id": tenant_id,
        "lease_id": lease_id,
        "property_id": property_id,
        "unit_id": unit_id,
        "amount": "1200",
        "due_date": due_date.isoformat(),
        "payment_type": "rent",
        "status": "paid",
        "payment_date": datetime.now(timezone.utc).isoformat()
    }
    resp = client.post('/api/payments/', json=payment_payload, headers=admin_headers)

    # Create pending payment
    overdue_date = datetime.now(timezone.utc) - timedelta(days=5)
    overdue_payload = {
        "tenant_id": tenant_id,
        "lease_id": lease_id,
        "property_id": property_id,
        "unit_id": unit_id,
        "amount": "1200",
        "due_date": overdue_date.isoformat(),
        "payment_type": "rent",
        "status": "pending"
    }
    resp = client.post('/api/payments/', json=overdue_payload, headers=admin_headers)

    # Get financial overview
    resp = client.get('/api/payments/overview', headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert 'total_collected' in data
    assert 'outstanding_balance' in data
    assert 'overdue_amount' in data
    assert 'total_revenue' in data
    assert data['paid_payments'] >= 1
    assert data['pending_payments'] >= 1


def test_tenant_payment_history(client, db_session):
    """Test getting payment history for a specific tenant."""
    # Create admin and tenant
    admin_email = f"pay_history_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user admin
    _set_role(db_session, admin_email, "admin")

    tenant_email = f"pay_history_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Make user tenant
    _set_role(db_session, tenant_email, "tenant")

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property, unit, lease, and payments
    property_payload = {
        "name": "Test Property for History",
        "property_type": "apartment",
        "address": "111 History St",
        "city": "Historyville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    unit_payload = {
        "property_id": property_id,
        "unit_number": "501",
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

    # Create multiple payments
    for i in range(3):
        due_date = datetime.now(timezone.utc) + timedelta(days=30 * (i + 1))
        payment_payload = {
            "tenant_id": tenant_id,
            "lease_id": lease_id,
            "property_id": property_id,
            "unit_id": unit_id,
            "amount": "1200",
            "due_date": due_date.isoformat(),
            "payment_type": "rent",
            "status": "paid" if i < 2 else "pending",
            "payment_date": datetime.now(timezone.utc).isoformat() if i < 2 else None
        }
        resp = client.post('/api/payments/', json=payment_payload, headers=admin_headers)
        assert resp.status_code == 201

    # Get tenant payment history
    resp = client.get(f'/api/payments/tenants/{tenant_id}/payments', headers=admin_headers)
    assert resp.status_code == 200
    payments = resp.json()
    assert len(payments) >= 3

    # Filter by status
    resp = client.get(f'/api/payments/tenants/{tenant_id}/payments?status=paid', headers=admin_headers)
    assert resp.status_code == 200
    paid_payments = resp.json()
    assert len(paid_payments) >= 2
