"""
Unit management API tests.
Tests for CRUD operations, filtering, and authorization.
"""
import uuid

import pytest

PASSWORD = "Str0ng!TestPass42"


def test_create_and_get_unit(client):
    """Test creating and retrieving a unit."""
    # Create and authenticate a user
    unique_email = f"unit_test_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": PASSWORD, "role": "owner"})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": unique_email, "password": PASSWORD})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access

    headers = {"Authorization": f"Bearer {access}"}

    # Create a property first
    property_payload = {
        "name": "Test Property for Units",
        "property_type": "apartment",
        "address": "123 Test St",
        "city": "Testville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=headers)
    assert resp.status_code == 201
    property_id = resp.json()['id']

    # Create a unit
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
    resp = client.post('/api/units/', json=unit_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['unit_number'] == unit_payload['unit_number']
    unit_id = data['id']

    # Get the unit
    resp = client.get(f'/api/units/{unit_id}', headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['id'] == unit_id
    assert data['unit_number'] == unit_payload['unit_number']


def test_list_units_with_filters(client):
    """Test listing units with various filters."""
    # Create and authenticate a user
    unique_email = f"unit_filter_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": PASSWORD, "role": "owner"})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": unique_email, "password": PASSWORD})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access

    headers = {"Authorization": f"Bearer {access}"}

    # Create a property
    property_payload = {
        "name": "Test Property for Filtering",
        "property_type": "apartment",
        "address": "456 Filter St",
        "city": "Filterville",
        "country": "Testland",
        "units_count": 3
    }
    resp = client.post('/api/properties/', json=property_payload, headers=headers)
    assert resp.status_code == 201
    property_id = resp.json()['id']

    # Create multiple units
    for i in range(3):
        unit_payload = {
            "property_id": property_id,
            "unit_number": f"{201 + i}",
            "unit_type": "1 bedroom" if i < 2 else "2 bedroom",
            "bedrooms": 1 if i < 2 else 2,
            "bathrooms": 1,
            "area": f"{750 + i * 100} sqft",
            "rent": str(1500 + i * 200),
            "status": "available"
        }
        resp = client.post('/api/units/', json=unit_payload, headers=headers)
        assert resp.status_code == 201

    # List all units
    resp = client.get('/api/units/', headers=headers)
    assert resp.status_code == 200
    units = resp.json()
    assert len(units) >= 3

    # Filter by property
    resp = client.get(f'/api/units/?property_id={property_id}', headers=headers)
    assert resp.status_code == 200
    property_units = resp.json()
    assert len(property_units) == 3

    # Filter by status
    resp = client.get('/api/units/?status=available', headers=headers)
    assert resp.status_code == 200
    available_units = resp.json()
    assert len(available_units) >= 3

    # Filter by bedrooms
    resp = client.get('/api/units/?bedrooms=1', headers=headers)
    assert resp.status_code == 200
    one_bed_units = resp.json()
    assert len(one_bed_units) >= 2


def test_update_unit(client):
    """Test updating a unit."""
    # Create and authenticate a user
    unique_email = f"unit_update_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": PASSWORD, "role": "owner"})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": unique_email, "password": PASSWORD})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access

    headers = {"Authorization": f"Bearer {access}"}

    # Create a property and unit
    property_payload = {
        "name": "Test Property for Update",
        "property_type": "apartment",
        "address": "789 Update St",
        "city": "Updateville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=headers)
    property_id = resp.json()['id']

    unit_payload = {
        "property_id": property_id,
        "unit_number": "301",
        "unit_type": "studio",
        "bedrooms": 0,
        "bathrooms": 1,
        "area": "500 sqft",
        "rent": "1200",
        "status": "available"
    }
    resp = client.post('/api/units/', json=unit_payload, headers=headers)
    unit_id = resp.json()['id']

    # Update the unit
    update_payload = {
        "rent": "1400",
        "status": "reserved"
    }
    resp = client.put(f'/api/units/{unit_id}', json=update_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['rent'] == "1400"
    assert data['status'] == "reserved"


def test_delete_unit(client):
    """Test deleting a unit."""
    # Create and authenticate a user
    unique_email = f"unit_delete_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": PASSWORD, "role": "owner"})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": unique_email, "password": PASSWORD})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access

    headers = {"Authorization": f"Bearer {access}"}

    # Create a property and unit
    property_payload = {
        "name": "Test Property for Delete",
        "property_type": "apartment",
        "address": "999 Delete St",
        "city": "Deleteville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=headers)
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
    resp = client.post('/api/units/', json=unit_payload, headers=headers)
    unit_id = resp.json()['id']

    # Delete the unit
    resp = client.delete(f'/api/units/{unit_id}', headers=headers)
    assert resp.status_code == 204

    # Verify unit is deleted
    resp = client.get(f'/api/units/{unit_id}', headers=headers)
    assert resp.status_code == 404


def test_unit_authorization(client):
    """Test that users cannot access units they don't have permission for."""
    # Create two users
    user1_email = f"unit_auth1_{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"unit_auth2_{uuid.uuid4().hex[:8]}@example.com"

    resp = client.post('/api/auth/register', json={"email": user1_email, "password": PASSWORD, "role": "owner"})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/register', json={"email": user2_email, "password": PASSWORD})
    assert resp.status_code in (200, 201)

    # Login as first user and create property/unit
    resp = client.post('/api/auth/login', json={"email": user1_email, "password": PASSWORD})
    user1_access = resp.json().get('access_token')
    user1_headers = {"Authorization": f"Bearer {user1_access}"}

    property_payload = {
        "name": "User1 Property",
        "property_type": "apartment",
        "address": "111 Auth St",
        "city": "Authville",
        "country": "Testland",
        "units_count": 1
    }
    resp = client.post('/api/properties/', json=property_payload, headers=user1_headers)
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
    resp = client.post('/api/units/', json=unit_payload, headers=user1_headers)
    unit_id = resp.json()['id']

    # Login as second user and try to access the unit
    resp = client.post('/api/auth/login', json={"email": user2_email, "password": PASSWORD})
    user2_access = resp.json().get('access_token')
    user2_headers = {"Authorization": f"Bearer {user2_access}"}

    # Second user should not be able to view the unit
    resp = client.get(f'/api/units/{unit_id}', headers=user2_headers)
    assert resp.status_code == 403

    # Second user should not be able to update the unit
    resp = client.put(f'/api/units/{unit_id}', json={"rent": "2000"}, headers=user2_headers)
    assert resp.status_code == 403

    # Second user should not be able to delete the unit
    resp = client.delete(f'/api/units/{unit_id}', headers=user2_headers)
    assert resp.status_code == 403


def test_get_property_units(client):
    """Test getting units for a specific property."""
    # Create and authenticate a user
    unique_email = f"unit_prop_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": PASSWORD, "role": "owner"})
    assert resp.status_code in (200, 201)

    resp = client.post('/api/auth/login', json={"email": unique_email, "password": PASSWORD})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access

    headers = {"Authorization": f"Bearer {access}"}

    # Create a property
    property_payload = {
        "name": "Test Property for Units List",
        "property_type": "apartment",
        "address": "222 Units St",
        "city": "Unitsville",
        "country": "Testland",
        "units_count": 2
    }
    resp = client.post('/api/properties/', json=property_payload, headers=headers)
    property_id = resp.json()['id']

    # Create units for the property
    for i in range(2):
        unit_payload = {
            "property_id": property_id,
            "unit_number": f"{601 + i}",
            "unit_type": "1 bedroom",
            "bedrooms": 1,
            "bathrooms": 1,
            "area": "750 sqft",
            "rent": "1500",
            "status": "available"
        }
        resp = client.post('/api/units/', json=unit_payload, headers=headers)
        assert resp.status_code == 201

    # Get units for the property
    resp = client.get(f'/api/units/properties/{property_id}/units', headers=headers)
    assert resp.status_code == 200
    units = resp.json()
    assert len(units) == 2

    # Verify all units belong to the property
    for unit in units:
        assert unit['property_id'] == property_id
