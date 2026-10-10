"""
Maintenance management API tests.
Tests for maintenance request workflow and authorization.
"""
import uuid

import pytest

from app.models.user import User

PASSWORD = "Str0ng!TestPass42"


def _set_role(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()
    db_session.refresh(user)


def test_create_and_get_maintenance(client, db_session):
    """Test creating and retrieving a maintenance request."""
    # Create admin user for property creation
    admin_email = f"maint_admin_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, admin_email, "admin")

    # Create tenant
    tenant_email = f"maint_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, tenant_email, "tenant")

    # Login as admin to create property
    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property
    property_payload = {
        "name": "Test Property for Maintenance",
        "property_type": "apartment",
        "address": "123 Maintenance St",
        "city": "Maintenanceville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    # Login as tenant
    resp = client.post('/api/auth/login', json={"email": tenant_email, "password": PASSWORD})
    tenant_access = resp.json().get('access_token')
    tenant_headers = {"Authorization": f"Bearer {tenant_access}"}

    # Create maintenance request
    maintenance_payload = {
        "property_id": property_id,
        "title": "Leaking faucet",
        "description": "The kitchen faucet is leaking and needs to be repaired",
        "category": "plumbing",
        "priority": "medium",
        "status": "pending"
    }
    resp = client.post('/api/maintenance/', json=maintenance_payload, headers=tenant_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['title'] == maintenance_payload['title']
    request_id = data['id']

    # Get the maintenance request
    resp = client.get(f'/api/maintenance/{request_id}', headers=tenant_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['id'] == request_id


def test_maintenance_authorization(client, db_session):
    """Test that tenants can only view their own maintenance requests."""
    # Create admin for property creation
    admin_email = f"maint_auth_admin_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, admin_email, "admin")

    # Create two tenants
    tenant1_email = f"maint_auth1_{uuid.uuid4().hex[:8]}@example.com"
    tenant2_email = f"maint_auth2_{uuid.uuid4().hex[:8]}@example.com"

    resp = client.post('/api/auth/register', json={"email": tenant1_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, tenant1_email, "tenant")

    resp = client.post('/api/auth/register', json={"email": tenant2_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, tenant2_email, "tenant")

    # Login as admin to create property
    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    property_payload = {
        "name": "Test Property for Auth",
        "property_type": "apartment",
        "address": "456 Auth St",
        "city": "Authville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    # Login as tenant1 and create maintenance request
    resp = client.post('/api/auth/login', json={"email": tenant1_email, "password": PASSWORD})
    tenant1_access = resp.json().get('access_token')
    tenant1_headers = {"Authorization": f"Bearer {tenant1_access}"}

    maintenance_payload = {
        "property_id": property_id,
        "title": "Broken window",
        "description": "Window in living room is cracked",
        "category": "repairs",
        "priority": "high",
        "status": "pending"
    }
    resp = client.post('/api/maintenance/', json=maintenance_payload, headers=tenant1_headers)
    request_id = resp.json()['id']

    # Login as tenant2 and try to access tenant1's request
    resp = client.post('/api/auth/login', json={"email": tenant2_email, "password": PASSWORD})
    tenant2_access = resp.json().get('access_token')
    tenant2_headers = {"Authorization": f"Bearer {tenant2_access}"}

    resp = client.get(f'/api/maintenance/{request_id}', headers=tenant2_headers)
    assert resp.status_code == 403


def test_maintenance_assignment(client, db_session):
    """Test assigning maintenance request to a manager."""
    # Create admin, manager, and tenant
    admin_email = f"maint_admin_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, admin_email, "admin")

    manager_email = f"maint_manager_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": manager_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    tenant_email = f"maint_tenant_assign_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, tenant_email, "tenant")

    # Login as admin and set manager role
    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    resp = client.get('/api/admin/users', headers=admin_headers)
    users = resp.json()
    manager_id = next(u['id'] for u in users if u['email'] == manager_email)

    resp = client.put(f'/api/admin/users/{manager_id}/role', params={"role": "manager"}, headers=admin_headers)
    assert resp.status_code == 200

    # Create property and maintenance request
    property_payload = {
        "name": "Test Property for Assignment",
        "property_type": "apartment",
        "address": "789 Assign St",
        "city": "Assignville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    maintenance_payload = {
        "property_id": property_id,
        "title": "HVAC issue",
        "description": "Air conditioning not working properly",
        "category": "hvac",
        "priority": "high",
        "status": "pending"
    }
    resp = client.post('/api/maintenance/', json=maintenance_payload, headers=admin_headers)
    request_id = resp.json()['id']

    # Assign maintenance request to manager
    assign_payload = {
        "assigned_manager_id": manager_id,
        "notes": "Please investigate the HVAC system"
    }
    resp = client.post(f'/api/maintenance/{request_id}/assign', json=assign_payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['assigned_manager_id'] == manager_id
    assert data['status'] == "assigned"


def test_maintenance_resolution(client, db_session):
    """Test resolving a maintenance request."""
    # Create admin and tenant
    admin_email = f"maint_resolve_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, admin_email, "admin")

    tenant_email = f"maint_resolve_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property and maintenance request
    property_payload = {
        "name": "Test Property for Resolution",
        "property_type": "apartment",
        "address": "999 Resolve St",
        "city": "Resolveville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    maintenance_payload = {
        "property_id": property_id,
        "title": "Electrical issue",
        "description": "Light switch not working in bedroom",
        "category": "electrical",
        "priority": "medium",
        "status": "pending"
    }
    resp = client.post('/api/maintenance/', json=maintenance_payload, headers=admin_headers)
    request_id = resp.json()['id']

    # Resolve the maintenance request
    resolve_payload = {
        "resolution_notes": "Replaced faulty switch and verified functionality",
        "cost": "150"
    }
    resp = client.post(f'/api/maintenance/{request_id}/resolve', json=resolve_payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == "completed"
    assert data['cost'] == "150"
    assert data['resolved_at'] is not None


def test_maintenance_status_update(client, db_session):
    """Test updating maintenance request status."""
    # Create admin and tenant
    admin_email = f"maint_status_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, admin_email, "admin")

    tenant_email = f"maint_status_tenant_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property and maintenance request
    property_payload = {
        "name": "Test Property for Status",
        "property_type": "apartment",
        "address": "111 Status St",
        "city": "Statusville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    maintenance_payload = {
        "property_id": property_id,
        "title": "Door lock issue",
        "description": "Front door lock is jammed",
        "category": "security",
        "priority": "high",
        "status": "pending"
    }
    resp = client.post('/api/maintenance/', json=maintenance_payload, headers=admin_headers)
    request_id = resp.json()['id']

    # Update status to in_progress
    update_payload = {
        "status": "in_progress",
        "notes": "Maintenance technician has been dispatched"
    }
    resp = client.put(f'/api/maintenance/{request_id}', json=update_payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == "in_progress"


def test_tenant_limited_update(client, db_session):
    """Test that tenants can only update limited fields."""
    # Create admin for property creation
    admin_email = f"maint_limited_admin_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, admin_email, "admin")

    # Create tenant
    tenant_email = f"maint_limited_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": tenant_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, tenant_email, "tenant")

    # Login as admin to create property
    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property
    property_payload = {
        "name": "Test Property for Limited",
        "property_type": "apartment",
        "address": "222 Limited St",
        "city": "Limitedville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    # Login as tenant
    resp = client.post('/api/auth/login', json={"email": tenant_email, "password": PASSWORD})
    tenant_access = resp.json().get('access_token')
    tenant_headers = {"Authorization": f"Bearer {tenant_access}"}

    # Create maintenance request
    maintenance_payload = {
        "property_id": property_id,
        "title": "Initial title",
        "description": "Initial description",
        "category": "general",
        "priority": "low",
        "status": "pending"
    }
    resp = client.post('/api/maintenance/', json=maintenance_payload, headers=tenant_headers)
    request_id = resp.json()['id']

    # Tenant should be able to update allowed fields
    update_payload = {
        "title": "Updated title",
        "description": "Updated description",
        "category": "plumbing"
    }
    resp = client.put(f'/api/maintenance/{request_id}', json=update_payload, headers=tenant_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['title'] == "Updated title"

    # Tenant should not be able to update status
    status_payload = {
        "status": "in_progress"
    }
    resp = client.put(f'/api/maintenance/{request_id}', json=status_payload, headers=tenant_headers)
    # Status change should be ignored for tenants
    data = resp.json()
    assert data['status'] == "pending"  # Status should remain unchanged


def test_property_maintenance_requests(client, db_session):
    """Test getting maintenance requests for a specific property."""
    # Create admin
    admin_email = f"maint_prop_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, admin_email, "admin")

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property
    property_payload = {
        "name": "Test Property for Requests",
        "property_type": "apartment",
        "address": "333 Requests St",
        "city": "Requestsville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    # Create multiple maintenance requests
    for i in range(3):
        maintenance_payload = {
            "property_id": property_id,
            "title": f"Maintenance request {i+1}",
            "description": f"Description for request {i+1}",
            "category": "general",
            "priority": "medium" if i < 2 else "high",
            "status": "pending"
        }
        resp = client.post('/api/maintenance/', json=maintenance_payload, headers=admin_headers)
        assert resp.status_code == 201

    # Get maintenance requests for the property
    resp = client.get(f'/api/maintenance/properties/{property_id}/maintenance', headers=admin_headers)
    assert resp.status_code == 200
    requests = resp.json()
    assert len(requests) == 3

    # Filter by status
    resp = client.get(f'/api/maintenance/properties/{property_id}/maintenance?status=pending', headers=admin_headers)
    assert resp.status_code == 200
    pending_requests = resp.json()
    assert len(pending_requests) == 3


def test_maintenance_priority_filtering(client, db_session):
    """Test filtering maintenance requests by priority."""
    # Create admin
    admin_email = f"maint_priority_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": admin_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)
    _set_role(db_session, admin_email, "admin")

    resp = client.post('/api/auth/login', json={"email": admin_email, "password": PASSWORD})
    admin_access = resp.json().get('access_token')
    admin_headers = {"Authorization": f"Bearer {admin_access}"}

    # Create property
    property_payload = {
        "name": "Test Property for Priority",
        "property_type": "apartment",
        "address": "444 Priority St",
        "city": "Priorityville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=admin_headers)
    property_id = resp.json()['id']

    # Create maintenance requests with different priorities
    priorities = ["low", "medium", "high", "urgent"]
    for priority in priorities:
        maintenance_payload = {
            "property_id": property_id,
            "title": f"{priority.capitalize()} priority issue",
            "description": f"This is a {priority} priority issue",
            "category": "general",
            "priority": priority,
            "status": "pending"
        }
        resp = client.post('/api/maintenance/', json=maintenance_payload, headers=admin_headers)
        assert resp.status_code == 201

    # Filter by high priority
    resp = client.get('/api/maintenance/?priority=high', headers=admin_headers)
    assert resp.status_code == 200
    high_priority = resp.json()
    assert len(high_priority) >= 1
    for request in high_priority:
        assert request['priority'] == "high"

    # Filter by urgent priority
    resp = client.get('/api/maintenance/?priority=urgent', headers=admin_headers)
    assert resp.status_code == 200
    urgent_priority = resp.json()
    assert len(urgent_priority) >= 1
    for request in urgent_priority:
        assert request['priority'] == "urgent"
