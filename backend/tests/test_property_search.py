"""Tests for the public browse search/filter logic (property_repo._apply_filters).

Covers the natural-language extraction (bedrooms / price bounds / purpose from
free text), the budget-bucket and bedrooms slugs used by the browse pages, and
the verified_only semantics the public verified filter relies on.
"""
from app.models.user import User
from app.models.property import Property
from app.repositories.property_repo import list_properties, count_properties
from app.utils.security import get_password_hash


def create_owner(db_session, email="owner@search.test"):
    user = User(
        email=email,
        hashed_password=get_password_hash("Str0ng!TestPass42"),
        role="owner",
        roles_csv="owner",
        full_name="Search Owner",
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
        name="Search Listing",
        property_type="Apartment",
        address="123 Test Ave",
        city="Nairobi",
        county="Nairobi",
        country="Kenya",
        status="active",
        purpose="rent",
        price="45000",
        price_label="KSh 45,000 / month",
        bedrooms=2,
        bathrooms=2,
        is_verified=True,
        verification_status="verified",
    )
    defaults.update(overrides)
    prop = Property(**defaults)
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop


def names(rows):
    return sorted(p.name for p in rows)


class TestNaturalLanguageSearch:
    def test_full_sentence_extracts_bedrooms_location_and_price(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Kilimani 3br 55k",
                        city="Kilimani", bedrooms=3, price="55000")
        create_property(db_session, owner.id, name="Kilimani 3br 120k",
                        city="Kilimani", bedrooms=3, price="120000")
        create_property(db_session, owner.id, name="Kilimani 2br 45k",
                        city="Kilimani", bedrooms=2, price="45000")
        create_property(db_session, owner.id, name="Westlands 3br 50k",
                        city="Westlands", bedrooms=3, price="50000")

        rows = list_properties(
            db_session, search="3 bedroom apartment in kilimani under 60k")
        assert names(rows) == ["Kilimani 3br 55k"]

    def test_studio_word_maps_to_zero_bedrooms(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Studio Unit",
                        property_type="Studio", bedrooms=None, price="15000")
        create_property(db_session, owner.id, name="Two Bed Unit", bedrooms=2)

        rows = list_properties(db_session, search="studio")
        assert names(rows) == ["Studio Unit"]

    def test_purpose_words_are_extracted_from_text(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Rent Home", purpose="rent")
        create_property(db_session, owner.id, name="Sale Home", purpose="buy")

        rows = list_properties(db_session, search="apartment for sale")
        assert names(rows) == ["Sale Home"]

    def test_land_token_does_not_match_westlands_substring(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Westlands Flat",
                        city="Westlands", price="45000", purpose="rent")
        create_property(db_session, owner.id, name="Ngong Plot",
                        property_type="Land", bedrooms=None,
                        city="Ngong", price="3500000", purpose="buy")

        rows = list_properties(db_session, search="land under 5m")
        assert names(rows) == ["Ngong Plot"]


class TestBedroomsFilter:
    def test_studio_filter_matches_zero_bedrooms_and_bedsitter_type(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Zero Bedroom", bedrooms=0)
        create_property(db_session, owner.id, name="Bedsitter Row",
                        property_type="Bedsitter", bedrooms=None)
        create_property(db_session, owner.id, name="Office Space",
                        property_type="Office", bedrooms=None, purpose="rent")

        rows = list_properties(db_session, bedrooms="0", purpose="rent")
        assert names(rows) == ["Bedsitter Row", "Zero Bedroom"]

    def test_four_plus_matches_four_bedroom_and_above(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Three Bed", bedrooms=3)
        create_property(db_session, owner.id, name="Four Bed", bedrooms=4)
        create_property(db_session, owner.id, name="Six Bed", bedrooms=6)

        rows = list_properties(db_session, bedrooms="4-plus")
        assert names(rows) == ["Four Bed", "Six Bed"]


class TestBudgetFilter:
    def test_budget_bucket_bounds(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Cheap Plot",
                        property_type="Land", bedrooms=None,
                        purpose="buy", price="3200000")
        create_property(db_session, owner.id, name="Mid Apartment",
                        purpose="buy", price="9500000")
        create_property(db_session, owner.id, name="Prime Villa",
                        property_type="Villa", purpose="buy", price="60000000")

        assert names(list_properties(db_session, purpose="buy", budget="under-5m")) == ["Cheap Plot"]
        assert names(list_properties(db_session, purpose="buy", budget="5m-15m")) == ["Mid Apartment"]
        assert names(list_properties(db_session, purpose="buy", budget="50m-plus")) == ["Prime Villa"]

    def test_count_matches_list_filters(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="A", purpose="buy", price="4000000")
        create_property(db_session, owner.id, name="B", purpose="buy", price="9000000")

        assert count_properties(db_session, purpose="buy", budget="under-5m") == 1


class TestVerifiedOnly:
    def test_verified_only_requires_flag_and_status(self, db_session):
        owner = create_owner(db_session)
        create_property(db_session, owner.id, name="Fully Verified",
                        is_verified=True, verification_status="verified")
        create_property(db_session, owner.id, name="Flag Only",
                        is_verified=True, verification_status="PENDING_VERIFICATION")
        create_property(db_session, owner.id, name="Pending",
                        is_verified=False, verification_status="PENDING_VERIFICATION")

        rows = list_properties(db_session, verified_only=True)
        assert names(rows) == ["Fully Verified"]
