"""Tests for the explainable property matching engine (P4-35)."""
from datetime import timedelta

from app.models.user import User
from app.models.property import Property
from app.services.matching_service import match_label, parse_price
from app.utils.security import get_password_hash
from app.utils.time import utc_now


def create_owner(db_session, email="owner@match.test"):
    user = User(
        email=email,
        hashed_password=get_password_hash("Str0ng!TestPass42"),
        role="owner",
        roles_csv="owner",
        full_name="Match Owner",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_property(db_session, owner_id, **overrides):
    defaults = dict(
        owner_id=owner_id,
        name="Test Listing",
        property_type="Apartment",
        address="123 Test Ave",
        city="Nairobi",
        county="Nairobi",
        country="Kenya",
        status="active",
        purpose="rent",
        price="45000",
        bedrooms=2,
        bathrooms=2,
        amenities="Swimming Pool, Gym, High-Speed Internet, CCTV",
        furnishing="fully-furnished",
        parking_spaces=1,
        is_verified=True,
    )
    defaults.update(overrides)
    prop = Property(**defaults)
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop


FULL_CRITERIA = {
    "max_budget": 50000.0,
    "preferred_city": "Nairobi",
    "min_bedrooms": 2,
    "property_type": "Apartment",
    "furnishing": "fully-furnished",
    "require_parking": True,
    "require_security": True,
    "amenities": ["Swimming Pool", "Gym"],
}


class TestParsePrice:
    def test_plain_number(self):
        assert parse_price("45000") == 45000.0

    def test_currency_and_commas(self):
        assert parse_price("KSh 45,000/Month") == 45000.0

    def test_k_suffix(self):
        assert parse_price("45k") == 45000.0

    def test_m_suffix(self):
        assert parse_price("1.2M") == 1200000.0

    def test_unparseable(self):
        assert parse_price(None) is None
        assert parse_price("price on request") is None


class TestMatchLabel:
    def test_thresholds(self):
        assert match_label(85) == "Excellent match"
        assert match_label(70) == "Strong match"
        assert match_label(55) == "Good match"
        assert match_label(54) == "Possible match"


class TestMatchEndpoint:
    def test_perfect_match_scores_excellent(self, client, db_session):
        owner = create_owner(db_session)
        prop = create_property(db_session, owner.id)

        resp = client.post("/api/properties/match", json=FULL_CRITERIA)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        top = data[0]
        assert top["property"]["id"] == prop.id
        assert top["match_score"] >= 90
        assert top["match_label"] == "Excellent match"
        assert len(top["match_reasons"]) > 0
        assert sum(top["score_breakdown"].values()) == top["match_score"]

    def test_breakdown_sums_to_score_for_all_results(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Straight Match")
        create_property(
            db_session, owner.id, name="Villa Elsewhere",
            property_type="Villa", city="Mombasa", price="60000",
        )
        create_property(
            db_session, owner.id, name="Small Unfurnished",
            bedrooms=1, furnishing="unfurnished",
        )

        resp = client.post("/api/properties/match", json=FULL_CRITERIA)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        for item in data:
            assert 0 <= item["match_score"] <= 100
            assert len(item["match_reasons"]) > 0
            assert sum(item["score_breakdown"].values()) == item["match_score"]
        # Ranked descending
        scores = [item["match_score"] for item in data]
        assert scores == sorted(scores, reverse=True)

    def test_way_over_budget_listing_is_excluded(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, price="80000")  # > 1.3 x 50000

        resp = client.post("/api/properties/match", json={"max_budget": 50000.0})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_slightly_over_budget_is_kept_but_penalised(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, price="55000")  # within 1.15 x 50000

        resp = client.post("/api/properties/match", json={"max_budget": 50000.0})
        data = resp.json()
        assert len(data) == 1
        reasons = " ".join(data[0]["match_reasons"])
        assert "Slightly over budget" in reasons
        assert data[0]["score_breakdown"]["Budget"] < 50

    def test_legacy_alias_fields_are_applied(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Nairobi Flat", city="Nairobi", price="40000")
        create_property(
            db_session, owner.id, name="Mombasa Flat",
            city="Mombasa", county="Mombasa", price="40000",
        )
        create_property(db_session, owner.id, name="Overpriced", city="Nairobi", price="90000")

        # Legacy payload: max_price / city were silently dropped before.
        resp = client.post(
            "/api/properties/match",
            json={"city": "Nairobi", "max_price": 50000.0, "amenities": ["Swimming Pool"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        names = [item["property"]["name"] for item in data]
        assert names == ["Nairobi Flat", "Mombasa Flat"]  # Overpriced excluded by alias budget
        assert data[0]["score_breakdown"]["Location"] > 0
        assert data[1]["score_breakdown"].get("Location", 0) == 0

    def test_bedroom_shortfall_is_graded(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Two Bed", bedrooms=2)
        create_property(db_session, owner.id, name="One Bed", bedrooms=1)

        resp = client.post("/api/properties/match", json={"min_bedrooms": 3})
        data = {item["property"]["name"]: item for item in resp.json()}
        assert data["Two Bed"]["match_score"] > data["One Bed"]["match_score"]
        assert any("below your space needs" in r for r in data["One Bed"]["match_reasons"])

    def test_type_synonyms_match(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Synonym Flat", property_type="Flat")
        create_property(db_session, owner.id, name="Mismatched Villa", property_type="Villa")

        resp = client.post("/api/properties/match", json={"property_type": "Apartment"})
        data = {item["property"]["name"]: item for item in resp.json()}
        assert data["Synonym Flat"]["score_breakdown"]["Type"] > 0
        assert data["Mismatched Villa"]["score_breakdown"].get("Type", 0) == 0
        assert data["Synonym Flat"]["match_score"] > data["Mismatched Villa"]["match_score"]

    def test_amenity_requirement_ratio(self, client, db_session):
        owner = create_owner(db_session)
        create_property(
            db_session, owner.id, name="Rich Amenities",
            parking_spaces=1, amenities="Parking, Balcony, Gym",
        )
        create_property(
            db_session, owner.id, name="Bare Amenities",
            parking_spaces=0, amenities="Water",
        )

        resp = client.post(
            "/api/properties/match",
            json={"require_parking": True, "require_balcony": True, "amenities": ["Gym"]},
        )
        data = {item["property"]["name"]: item for item in resp.json()}
        assert data["Rich Amenities"]["score_breakdown"]["Amenities"] > data["Bare Amenities"]["score_breakdown"]["Amenities"]
        assert data["Rich Amenities"]["match_score"] > data["Bare Amenities"]["match_score"]

    def test_limit_caps_results_and_is_bounded(self, client, db_session):
        owner = create_owner(db_session)
        for i in range(3):
            create_property(db_session, owner.id, name=f"Listing {i}")

        resp = client.post("/api/properties/match?limit=2", json={"max_budget": 50000.0})
        assert len(resp.json()) == 2

        resp = client.post("/api/properties/match?limit=100", json={})
        assert resp.status_code == 422  # over the allowed maximum

    def test_empty_criteria_returns_ranked_list(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id)

        resp = client.post("/api/properties/match", json={})
        data = resp.json()
        assert len(data) == 1
        assert 0 <= data[0]["match_score"] <= 100
        assert data[0]["match_label"]
        assert len(data[0]["match_reasons"]) > 0

    def test_stale_listing_loses_freshness_points(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Fresh")
        create_property(
            db_session, owner.id, name="Stale",
            created_at=utc_now() - timedelta(days=120),
        )

        resp = client.post("/api/properties/match", json={})
        data = {item["property"]["name"]: item for item in resp.json()}
        assert data["Fresh"]["score_breakdown"]["Freshness"] > data["Stale"]["score_breakdown"]["Freshness"]
        assert data["Fresh"]["match_score"] > data["Stale"]["match_score"]

    def test_purpose_filter_still_applies(self, client, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Rental", purpose="rent")
        create_property(db_session, owner.id, name="For Sale", purpose="sale")

        resp = client.post("/api/properties/match", json={"purpose": "rent"})
        names = [item["property"]["name"] for item in resp.json()]
        assert names == ["Rental"]
