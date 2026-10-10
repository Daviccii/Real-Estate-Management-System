"""Tests for marketplace expansion (P4-40): provider directory, job board, reviews."""
import uuid

from app.models.company import Company
from app.models.maintenance import Maintenance
from app.models.notification import Notification
from app.models.property import Property
from app.models.service_marketplace import (
    MaintenanceQuote,
    MaintenanceWorkOrder,
    ServiceProviderProfile,
)
from app.models.user import User

PASSWORD = "Str0ng!TestPass42"

PROVIDERS = '/api/service-marketplace/providers'
OPEN_REQUESTS = '/api/service-marketplace/open-requests'
QUOTES = '/api/service-marketplace/quotes'
WORK_ORDERS = '/api/service-marketplace/work-orders'


def _register(client, db_session, role, prefix, full_name=None):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": email, "password": PASSWORD})
    assert resp.status_code in (200, 201), resp.text
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    user.roles_csv = role
    if full_name:
        user.full_name = full_name
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client, email):
    resp = client.post('/api/auth/login', json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_property(db_session, owner, *, name="Kilimani Heights", manager=None, company_id=None, city="Nairobi"):
    prop = Property(
        owner_id=owner.id,
        manager_id=manager.id if manager else None,
        company_id=company_id,
        name=name,
        city=city,
        property_type="apartment",
        status="active",
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop


def _make_maintenance(db_session, prop, *, title="Leaking kitchen tap", category="plumbing",
                      status="pending", description="Water dripping from the kitchen tap"):
    item = Maintenance(
        property_id=prop.id,
        title=title,
        description=description,
        category=category,
        status=status,
        priority="medium",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def _make_profile(db_session, provider, *, business_name="Nairobi Pipeworks", specialty="plumbing",
                  areas="Nairobi, Kiambu", is_available=True, rating=None, reviews_count=0):
    profile = ServiceProviderProfile(
        user_id=provider.id,
        business_name=business_name,
        specialty=specialty,
        service_areas=areas,
        is_available=is_available,
        rating=rating,
        reviews_count=reviews_count,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def _make_quote(db_session, maint, provider, *, amount="15000", status="pending"):
    quote = MaintenanceQuote(
        maintenance_id=maint.id,
        provider_id=provider.id,
        amount=amount,
        description="Replace washer and reseal",
        status=status,
    )
    db_session.add(quote)
    db_session.commit()
    db_session.refresh(quote)
    return quote


def _make_work_order(db_session, maint, provider, *, status="completed", quote=None):
    wo = MaintenanceWorkOrder(
        maintenance_id=maint.id,
        provider_id=provider.id,
        quote_id=quote.id if quote else None,
        status=status,
    )
    db_session.add(wo)
    db_session.commit()
    db_session.refresh(wo)
    return wo


class TestProviderDirectory:
    def test_requires_authentication(self, client, db_session):
        assert client.get(PROVIDERS).status_code == 401

    def test_pagination_search_and_availability(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        p1 = _register(client, db_session, "service_provider", "prov")
        p2 = _register(client, db_session, "service_provider", "prov")
        _make_profile(db_session, p1, business_name="Nairobi Pipeworks", specialty="plumbing", is_available=True)
        _make_profile(db_session, p2, business_name="Mombasa Sparks", specialty="electrical",
                      areas="Mombasa", is_available=False)
        headers = _login(client, owner.email)

        resp = client.get(PROVIDERS, headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 2 and body["page"] == 1 and body["page_size"] == 12
        assert len(body["items"]) == 2

        resp = client.get(PROVIDERS, params={"q": "pipe"}, headers=headers)
        assert [i["business_name"] for i in resp.json()["items"]] == ["Nairobi Pipeworks"]

        resp = client.get(PROVIDERS, params={"available_only": True}, headers=headers)
        items = resp.json()["items"]
        assert len(items) == 1 and items[0]["business_name"] == "Nairobi Pipeworks"

        resp = client.get(PROVIDERS, params={"category": "electrical"}, headers=headers)
        items = resp.json()["items"]
        assert len(items) == 1 and items[0]["specialty"] == "electrical"

        resp = client.get(PROVIDERS, params={"page": 2, "page_size": 1}, headers=headers)
        body = resp.json()
        assert body["total"] == 2 and body["page"] == 2 and len(body["items"]) == 1

    def test_contact_details_hidden_from_other_users(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        _make_profile(db_session, provider)

        resp = client.get(PROVIDERS, headers=_login(client, owner.email))
        item = resp.json()["items"][0]
        assert item["user_email"] is None and item["user_phone"] is None

        resp = client.get(PROVIDERS, headers=_login(client, provider.email))
        item = resp.json()["items"][0]
        assert item["user_email"] == provider.email

    def test_real_completed_jobs_and_rating_aggregates(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        manager = _register(client, db_session, "manager", "mgr")
        provider = _register(client, db_session, "service_provider", "prov")
        prop = _make_property(db_session, owner, manager=manager)
        maint = _make_maintenance(db_session, prop)
        _make_profile(db_session, provider)
        _make_work_order(db_session, maint, provider, status="completed")
        _make_work_order(db_session, _make_maintenance(db_session, prop), provider, status="verified")
        _make_work_order(db_session, _make_maintenance(db_session, prop), provider, status="in_progress")

        headers = _login(client, owner.email)
        resp = client.get(PROVIDERS, headers=headers)
        item = resp.json()["items"][0]
        assert item["completed_jobs_count"] == 2
        assert item["rating_avg"] is None and item["reviews_count"] == 0

        # After a review, the aggregate rating is exposed
        headers_mgr = _login(client, manager.email)
        reviewable = _make_work_order(db_session, _make_maintenance(db_session, prop), provider, status="completed")
        resp = client.post(f'{WORK_ORDERS}/{reviewable.id}/review', json={"score": 4}, headers=headers_mgr)
        assert resp.status_code == 201, resp.text
        resp = client.get(PROVIDERS, headers=headers)
        item = resp.json()["items"][0]
        assert item["rating_avg"] == 4.0 and item["reviews_count"] == 1

    def test_provider_can_toggle_availability(self, client, db_session):
        provider = _register(client, db_session, "service_provider", "prov")
        headers = _login(client, provider.email)
        resp = client.post(f'{PROVIDERS}/profile', json={
            "business_name": "Nairobi Pipeworks",
            "specialty": "plumbing",
            "service_areas": "Nairobi",
            "is_available": False,
        }, headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_available"] is False

        resp = client.get(f'{PROVIDERS}/profile/me', headers=headers)
        assert resp.json()["is_available"] is False

        resp = client.post(f'{PROVIDERS}/profile', json={"is_available": True}, headers=headers)
        assert resp.json()["is_available"] is True


class TestOpenRequestsJobBoard:
    def test_provider_sees_open_jobs_only(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        prop = _make_property(db_session, owner)
        open_maint = _make_maintenance(db_session, prop, title="Burst pipe")
        _make_maintenance(db_session, prop, title="Old resolved job", status="resolved")
        _make_maintenance(db_session, prop, title="Closed job", status="closed")

        resp = client.get(OPEN_REQUESTS, headers=_login(client, provider.email))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 1
        item = body["items"][0]
        assert item["id"] == open_maint.id and item["title"] == "Burst pipe"
        assert item["city"] == "Nairobi"
        # Privacy: no tenant/owner/address fields exposed
        for leak in ("tenant_id", "address", "owner_id", "unit_id", "sub_location"):
            assert leak not in item

    def test_tenant_cannot_access_job_board(self, client, db_session):
        tenant = _register(client, db_session, "tenant", "ten")
        resp = client.get(OPEN_REQUESTS, headers=_login(client, tenant.email))
        assert resp.status_code == 403

    def test_filters_and_my_quote_tracking(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        prop = _make_property(db_session, owner, city="Nairobi")
        prop2 = _make_property(db_session, owner, name="Nyali Apartments", city="Mombasa")
        _make_maintenance(db_session, prop, title="Leaking tap", category="plumbing")
        _make_maintenance(db_session, prop2, title="Wiring fault", category="electrical")
        headers = _login(client, provider.email)

        resp = client.get(OPEN_REQUESTS, params={"category": "plumbing"}, headers=headers)
        assert [i["title"] for i in resp.json()["items"]] == ["Leaking tap"]

        resp = client.get(OPEN_REQUESTS, params={"city": "Mombasa"}, headers=headers)
        assert [i["title"] for i in resp.json()["items"]] == ["Wiring fault"]

        maint = db_session.query(Maintenance).filter(Maintenance.title == "Leaking tap").first()
        resp = client.post(QUOTES, json={"request_id": maint.id, "quoted_amount": "12000",
                                         "scope_description": "Swap tap assembly"}, headers=headers)
        assert resp.status_code == 200, resp.text

        resp = client.get(OPEN_REQUESTS, params={"category": "plumbing"}, headers=headers)
        item = resp.json()["items"][0]
        assert item["quotes_count"] == 1
        assert item["my_quote_status"] == "pending"
        assert item["my_quote_amount"] == "12000"


class TestQuoteLifecycle:
    def test_provider_can_quote_cross_company_open_jobs(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        company = Company(name="Acme Holdings", slug="acme-holdings")
        db_session.add(company)
        db_session.commit()
        prop = _make_property(db_session, owner, company_id=company.id)
        maint = _make_maintenance(db_session, prop)

        resp = client.post(QUOTES, json={"request_id": maint.id, "quoted_amount": "8000",
                                         "scope_description": "Fix leak"}, headers=_login(client, provider.email))
        assert resp.status_code == 200, resp.text

    def test_quote_rejected_on_closed_ticket(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        prop = _make_property(db_session, owner)
        maint = _make_maintenance(db_session, prop, status="resolved")

        resp = client.post(QUOTES, json={"request_id": maint.id, "quoted_amount": "8000",
                                         "scope_description": "Fix leak"}, headers=_login(client, provider.email))
        assert resp.status_code == 400

    def test_tenant_cannot_quote(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        tenant = _register(client, db_session, "tenant", "ten")
        prop = _make_property(db_session, owner)
        maint = _make_maintenance(db_session, prop)

        resp = client.post(QUOTES, json={"request_id": maint.id, "quoted_amount": "8000",
                                         "scope_description": "Fix leak"}, headers=_login(client, tenant.email))
        assert resp.status_code == 403

    def test_accept_quote_creates_work_order_once(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        prop = _make_property(db_session, owner)
        maint = _make_maintenance(db_session, prop)
        quote = _make_quote(db_session, maint, provider)

        tenant = _register(client, db_session, "tenant", "ten")
        resp = client.post(f'{QUOTES}/{quote.id}/accept', headers=_login(client, tenant.email))
        assert resp.status_code == 403

        headers = _login(client, owner.email)
        resp = client.post(f'{QUOTES}/{quote.id}/accept', headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "assigned" and body["provider_id"] == provider.id

        resp = client.post(f'{QUOTES}/{quote.id}/accept', headers=headers)
        assert resp.status_code == 400

        db_session.refresh(maint)
        assert maint.status == "in_progress"

        resp = client.get(f'{WORK_ORDERS}/my', headers=_login(client, provider.email))
        assert any(o["request_id"] == maint.id for o in resp.json())

        notifs = db_session.query(Notification).filter(Notification.recipient_id == provider.id).all()
        assert any("Quote Accepted" in n.title for n in notifs)


class TestWorkOrderReviewFlow:
    def _setup(self, client, db_session):
        owner = _register(client, db_session, "owner", "own", full_name="Mary Wanjiku")
        manager = _register(client, db_session, "manager", "mgr")
        provider = _register(client, db_session, "service_provider", "prov")
        tenant = _register(client, db_session, "tenant", "ten")
        prop = _make_property(db_session, owner, manager=manager)
        maint = _make_maintenance(db_session, prop)
        _make_profile(db_session, provider)
        return owner, manager, provider, tenant, prop, maint

    def test_review_requires_management_and_completion(self, client, db_session):
        owner, manager, provider, tenant, prop, maint = self._setup(client, db_session)
        wo = _make_work_order(db_session, maint, provider, status="completed")

        resp = client.post(f'{WORK_ORDERS}/{wo.id}/review', json={"score": 5},
                           headers=_login(client, tenant.email))
        assert resp.status_code == 403

        wo.status = "in_progress"
        db_session.commit()
        resp = client.post(f'{WORK_ORDERS}/{wo.id}/review', json={"score": 5},
                           headers=_login(client, manager.email))
        assert resp.status_code == 400

    def test_review_updates_aggregates_and_dedupes(self, client, db_session):
        owner, manager, provider, tenant, prop, maint = self._setup(client, db_session)
        wo1 = _make_work_order(db_session, maint, provider, status="completed")
        wo2 = _make_work_order(db_session, _make_maintenance(db_session, prop), provider, status="verified")

        resp = client.post(f'{WORK_ORDERS}/{wo1.id}/review', json={"score": 5, "comment": "  Great work  "},
                           headers=_login(client, owner.email))
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["score"] == 5 and body["comment"] == "Great work"
        assert body["reviewer_name"] == "Mary W."
        assert body["provider_rating_avg"] == 5.0 and body["provider_reviews_count"] == 1

        # Duplicate review for the same work order is rejected
        resp = client.post(f'{WORK_ORDERS}/{wo1.id}/review', json={"score": 3},
                           headers=_login(client, owner.email))
        assert resp.status_code == 409

        # Second review (manager) recomputes the average
        resp = client.post(f'{WORK_ORDERS}/{wo2.id}/review', json={"score": 3},
                           headers=_login(client, manager.email))
        assert resp.status_code == 201, resp.text
        assert resp.json()["provider_rating_avg"] == 4.0

        profile = db_session.query(ServiceProviderProfile).filter(
            ServiceProviderProfile.user_id == provider.id).first()
        db_session.refresh(profile)
        assert profile.rating == 4.0 and profile.reviews_count == 2

        notifs = db_session.query(Notification).filter(Notification.recipient_id == provider.id).all()
        assert any(n.title == "New Customer Review" for n in notifs)

    def test_public_review_list_masks_reviewer_names(self, client, db_session):
        owner, manager, provider, tenant, prop, maint = self._setup(client, db_session)
        wo = _make_work_order(db_session, maint, provider, status="completed")
        client.post(f'{WORK_ORDERS}/{wo.id}/review', json={"score": 4, "comment": "Solid"},
                    headers=_login(client, owner.email))

        profile = db_session.query(ServiceProviderProfile).filter(
            ServiceProviderProfile.user_id == provider.id).first()
        resp = client.get(f'{PROVIDERS}/{profile.id}/reviews',
                          headers=_login(client, tenant.email))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 1 and body["reviews_count"] == 1 and body["rating_avg"] == 4.0
        item = body["items"][0]
        assert item["reviewer_name"] == "Mary W." and item["comment"] == "Solid"
        assert item["maintenance_title"] == "Leaking kitchen tap"
        assert "reviewer_id" not in item

    def test_invalid_score_rejected(self, client, db_session):
        owner, manager, provider, tenant, prop, maint = self._setup(client, db_session)
        wo = _make_work_order(db_session, maint, provider, status="completed")
        resp = client.post(f'{WORK_ORDERS}/{wo.id}/review', json={"score": 9, "comment": "x"},
                           headers=_login(client, owner.email))
        assert resp.status_code == 422


class TestWorkOrderStatusGuards:
    def test_invalid_status_rejected(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        prop = _make_property(db_session, owner)
        maint = _make_maintenance(db_session, prop)
        wo = _make_work_order(db_session, maint, provider, status="assigned")

        resp = client.patch(f'{WORK_ORDERS}/{wo.id}/status', json={"status": "banana"},
                            headers=_login(client, owner.email))
        assert resp.status_code == 400

    def test_only_management_can_verify(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        prop = _make_property(db_session, owner)
        maint = _make_maintenance(db_session, prop)
        wo = _make_work_order(db_session, maint, provider, status="completed")

        resp = client.patch(f'{WORK_ORDERS}/{wo.id}/status', json={"status": "verified"},
                            headers=_login(client, provider.email))
        assert resp.status_code == 403

        resp = client.patch(f'{WORK_ORDERS}/{wo.id}/status', json={"status": "verified"},
                            headers=_login(client, owner.email))
        assert resp.status_code == 200, resp.text
        db_session.refresh(wo)
        assert wo.status == "verified" and wo.verified_by_id == owner.id and wo.verified_at is not None

    def test_can_review_flag_in_work_order_list(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        provider = _register(client, db_session, "service_provider", "prov")
        prop = _make_property(db_session, owner)
        maint = _make_maintenance(db_session, prop)
        wo = _make_work_order(db_session, maint, provider, status="completed")

        headers = _login(client, owner.email)
        resp = client.get(WORK_ORDERS, params={"maintenance_id": maint.id}, headers=headers)
        assert resp.status_code == 200, resp.text
        item = resp.json()[0]
        assert item["can_review"] is True and item["has_review"] is False

        client.post(f'{WORK_ORDERS}/{wo.id}/review', json={"score": 5}, headers=headers)

        resp = client.get(WORK_ORDERS, params={"maintenance_id": maint.id}, headers=headers)
        item = resp.json()[0]
        assert item["can_review"] is False and item["has_review"] is True and item["review_score"] == 5

        # Provider never gets review rights in the response
        resp = client.get(WORK_ORDERS, headers=_login(client, provider.email))
        assert all(o["can_review"] is False for o in resp.json())
