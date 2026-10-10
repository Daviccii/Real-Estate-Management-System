import pytest
from fastapi import status
from app.models.user import User
from app.models.property import Property
from app.models.unit import Unit
from app.models.lease import Lease
from app.models.application import RentalApplication
from app.auth.jwt import create_access_token


def test_tenant_cannot_access_other_tenants_leases(client, db_session):
    # Setup Tenant 1 and Tenant 2
    tenant1 = User(email="t1@example.com", hashed_password="p", full_name="Tenant 1", role="tenant", is_active=True)
    tenant2 = User(email="t2@example.com", hashed_password="p", full_name="Tenant 2", role="tenant", is_active=True)
    owner = User(email="o@example.com", hashed_password="p", full_name="Owner", role="owner", is_active=True)
    db_session.add_all([tenant1, tenant2, owner])
    db_session.commit()
    db_session.refresh(tenant1)
    db_session.refresh(tenant2)
    db_session.refresh(owner)

    # Property and Unit
    prop = Property(name="Isolated Estate", owner_id=owner.id, city="Nairobi", status="active", purpose="rent")
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)

    unit = Unit(property_id=prop.id, unit_number="101", status="occupied", rent_amount=50000)
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)

    from datetime import datetime, timedelta, timezone

    # Lease for Tenant 2
    lease2 = Lease(
        tenant_id=tenant2.id,
        property_id=prop.id,
        unit_id=unit.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=365),
        rent_amount="50000",
        status="active"
    )
    db_session.add(lease2)
    db_session.commit()
    db_session.refresh(lease2)

    # Tenant 1 tries to access Tenant 2's lease
    t1_token = create_access_token({"sub": str(tenant1.id), "role": "tenant"})
    headers = {"Authorization": f"Bearer {t1_token}"}

    res = client.get(f"/api/leases/{lease2.id}", headers=headers)
    print("LEASES RES:", res.status_code, res.text)
    # Must be 403 Forbidden or 404 (IDOR protection)
    assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


def test_owner_cannot_modify_other_owners_properties(client, db_session):
    owner1 = User(email="o1@example.com", hashed_password="p", full_name="Owner 1", role="owner", is_active=True)
    owner2 = User(email="o2@example.com", hashed_password="p", full_name="Owner 2", role="owner", is_active=True)
    db_session.add_all([owner1, owner2])
    db_session.commit()
    db_session.refresh(owner1)
    db_session.refresh(owner2)

    prop2 = Property(name="Owner2 Property", owner_id=owner2.id, city="Nairobi", status="active", purpose="rent")
    db_session.add(prop2)
    db_session.commit()
    db_session.refresh(prop2)

    # Owner 1 tries to update Owner 2's property
    o1_token = create_access_token({"sub": str(owner1.id), "role": "owner"})
    headers = {"Authorization": f"Bearer {o1_token}"}

    update_payload = {"name": "Hacked Property Name"}
    res = client.put(f"/api/properties/{prop2.id}", json=update_payload, headers=headers)
    assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)
