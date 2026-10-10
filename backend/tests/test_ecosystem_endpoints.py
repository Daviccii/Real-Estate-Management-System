import pytest
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.property import Property
from app.utils.security import get_password_hash

def create_user(db_session, email, role="tenant", name="Test User"):
    user = User(
        email=email,
        hashed_password=get_password_hash("Str0ng!TestPass42"),
        role=role,
        roles_csv=role,
        full_name=name,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def create_property(db_session, owner_id, name="Sunset Heights"):
    prop = Property(
        owner_id=owner_id,
        name=name,
        property_type="Apartment",
        address="123 Ocean View",
        city="Nairobi",
        country="Kenya",
        status="active",
        price="45000",
        bedrooms=2,
        bathrooms=2,
        amenities="Swimming Pool, Gym, High-Speed Internet, Backup Generator",
        furnishing="fully-furnished",
        parking_spaces=1,
        is_verified=True
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop

def test_smart_match_calculation(client, db_session):
    owner = create_user(db_session, "owner1@test.com", "owner", "Owner 1")
    prop = create_property(db_session, owner.id, "Luxury City Apartment")
    
    # Match query matching price and city
    payload = {
        "city": "Nairobi",
        "property_type": "Apartment",
        "min_bedrooms": 2,
        "max_price": 50000.0,
        "furnishing": "fully-furnished",
        "amenities": ["Swimming Pool", "Gym"]
    }
    
    resp = client.post("/api/properties/match", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    top_match = data[0]
    assert top_match["property"]["id"] == prop.id
    assert top_match["match_score"] >= 80
    assert len(top_match["match_reasons"]) > 0

def test_viewings_booking_flow(client, db_session):
    tenant = create_user(db_session, "tenant1@test.com", "tenant", "Tenant 1")
    owner = create_user(db_session, "owner2@test.com", "owner", "Owner 2")
    prop = create_property(db_session, owner.id, "Parkview Suites")
    
    # Login as tenant
    login_resp = client.post("/api/auth/login", json={"email": "tenant1@test.com", "password": "Str0ng!TestPass42"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Book viewing
    viewing_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    booking_payload = {
        "property_id": prop.id,
        "scheduled_time": viewing_time,
        "viewing_type": "in_person",
        "notes": "Looking forward to seeing the balcony"
    }
    
    resp = client.post("/api/viewings/book", json=booking_payload, headers=headers)
    assert resp.status_code in (200, 201)
    viewing = resp.json()
    assert viewing["status"] == "pending"
    assert viewing["property_id"] == prop.id
    
    # Check tenant viewings list
    my_viewings = client.get("/api/viewings/my-viewings", headers=headers)
    assert my_viewings.status_code == 200
    assert len(my_viewings.json()) == 1

def test_rental_application_and_review(client, db_session):
    tenant = create_user(db_session, "tenant2@test.com", "tenant", "Tenant 2")
    owner = create_user(db_session, "owner3@test.com", "owner", "Owner 3")
    prop = create_property(db_session, owner.id, "Highland Towers")
    
    # Login as tenant
    login_resp = client.post("/api/auth/login", json={"email": "tenant2@test.com", "password": "Str0ng!TestPass42"})
    tenant_token = login_resp.json()["access_token"]
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}
    
    # Submit rental application
    app_payload = {
        "property_id": prop.id,
        "monthly_income": "120000",
        "employment_status": "employed",
        "employer_name": "Tech Corp",
        "job_title": "Software Engineer",
        "credit_score_range": "750+",
        "occupants_count": 2,
        "has_pets": "No"
    }
    
    resp = client.post("/api/applications/apply", json=app_payload, headers=tenant_headers)
    assert resp.status_code in (200, 201)
    app_data = resp.json()
    app_id = app_data["id"]
    assert app_data["status"] == "submitted"
    
    # Login as owner/manager to review
    owner_login = client.post("/api/auth/login", json={"email": "owner3@test.com", "password": "Str0ng!TestPass42"})
    owner_token = owner_login.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    
    # Review application
    review_payload = {
        "status": "approved",
        "review_notes": "Great profile, all checks passed"
    }
    review_resp = client.patch(f"/api/applications/{app_id}/review", json=review_payload, headers=owner_headers)
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "approved"

def test_leads_pipeline(client, db_session):
    agent = create_user(db_session, "agent1@test.com", "agent", "Agent Smith")
    owner = create_user(db_session, "owner4@test.com", "owner", "Owner 4")
    prop = create_property(db_session, owner.id, "Westlands Residency")
    
    agent_login = client.post("/api/auth/login", json={"email": "agent1@test.com", "password": "Str0ng!TestPass42"})
    agent_token = agent_login.json()["access_token"]
    agent_headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create lead
    lead_payload = {
        "property_id": prop.id,
        "prospect_name": "Jane Prospect",
        "prospect_email": "jane@prospect.com",
        "prospect_phone": "+254712345678",
        "estimated_budget": "50000",
        "notes": "Interested in 2-bedroom with parking"
    }
    
    resp = client.post("/api/leads/", json=lead_payload, headers=agent_headers)
    assert resp.status_code in (200, 201)
    lead_id = resp.json()["id"]
    assert resp.json()["stage"] == "new"
    
    # Update stage to 'tour_scheduled'
    update_resp = client.patch(f"/api/leads/{lead_id}/stage", json={"stage": "viewing"}, headers=agent_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["stage"] == "viewing"

