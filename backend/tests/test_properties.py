import uuid


PASSWORD = "Str0ng!TestPass42"


def test_create_and_get_property(client):
    unique_email = f"prop_test_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": PASSWORD, "role": "owner"})
    assert resp.status_code in (200, 201)
    # Login
    resp = client.post('/api/auth/login', json={"email": unique_email, "password": PASSWORD})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access

    headers = {"Authorization": f"Bearer {access}"}
    # Create property
    payload = {
        "name": "Test Property",
        "property_type": "apartment",
        "address": "123 Main St",
        "city": "Testville",
        "country": "Testland",
        "units_count": 4
    }
    resp = client.post('/api/properties/', json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['name'] == payload['name']
    prop_id = data['id']

    # Get property
    resp = client.get(f'/api/properties/{prop_id}', headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['id'] == prop_id
