from app.auth.jwt import create_access_token
from app.models.company import Company
from app.models.property import Property
from app.models.unit import Unit
from app.models.user import User


def auth_headers(user):
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def test_company_user_cannot_start_conversation_with_foreign_company_user(client, db_session):
    company_a = Company(name="Company A", slug="company-a")
    company_b = Company(name="Company B", slug="company-b")
    db_session.add_all([company_a, company_b])
    db_session.flush()

    sender = User(
        email="sender@a.test", hashed_password="p", role="tenant",
        is_active=True, company_id=company_a.id,
    )
    recipient = User(
        email="recipient@b.test", hashed_password="p", role="owner",
        is_active=True, company_id=company_b.id,
    )
    db_session.add_all([sender, recipient])
    db_session.commit()

    response = client.post(
        "/api/communications/conversations",
        headers=auth_headers(sender),
        json={"recipient_id": recipient.id, "initial_message": "Cross-company access"},
    )

    assert response.status_code == 404


def test_company_user_cannot_create_maintenance_for_foreign_property(client, db_session):
    company_a = Company(name="Company A", slug="company-a")
    company_b = Company(name="Company B", slug="company-b")
    db_session.add_all([company_a, company_b])
    db_session.flush()

    tenant = User(
        email="tenant@a.test", hashed_password="p", role="tenant",
        is_active=True, company_id=company_a.id,
    )
    owner = User(
        email="owner@b.test", hashed_password="p", role="owner",
        is_active=True, company_id=company_b.id,
    )
    db_session.add_all([tenant, owner])
    db_session.flush()
    prop = Property(
        name="Foreign Property", owner_id=owner.id, company_id=company_b.id,
        city="Nairobi", status="active", purpose="rent",
    )
    db_session.add(prop)
    db_session.commit()

    response = client.post(
        "/api/maintenance/",
        headers=auth_headers(tenant),
        json={
            "property_id": prop.id,
            "title": "Unauthorized repair",
            "description": "Should be rejected",
        },
    )

    assert response.status_code == 404


def test_application_rejects_unit_from_another_property(client, db_session):
    company = Company(name="Company A", slug="company-a")
    db_session.add(company)
    db_session.flush()
    tenant = User(
        email="applicant@a.test", hashed_password="p", role="tenant",
        is_active=True, company_id=company.id,
    )
    owner = User(
        email="owner@a.test", hashed_password="p", role="owner",
        is_active=True, company_id=company.id,
    )
    db_session.add_all([tenant, owner])
    db_session.flush()
    first = Property(
        name="First Property", owner_id=owner.id, company_id=company.id,
        city="Nairobi", status="active", purpose="rent",
    )
    second = Property(
        name="Second Property", owner_id=owner.id, company_id=company.id,
        city="Nairobi", status="active", purpose="rent",
    )
    db_session.add_all([first, second])
    db_session.flush()
    foreign_unit = Unit(property_id=second.id, unit_number="B-1", status="vacant", rent_amount=1000)
    db_session.add(foreign_unit)
    db_session.commit()

    response = client.post(
        "/api/applications/",
        headers=auth_headers(tenant),
        json={"property_id": first.id, "unit_id": foreign_unit.id},
    )

    assert response.status_code == 404
