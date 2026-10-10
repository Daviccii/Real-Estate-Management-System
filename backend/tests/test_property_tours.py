"""Tests for property 360/virtual tours (P4-36): URL allowlist + CRUD auth."""
import uuid

from app.models.property import Property
from app.models.property_tour import PropertyTour
from app.models.user import User

PASSWORD = "Str0ng!TestPass42"


def _register(client, db_session, role, prefix):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post('/api/auth/register', json={"email": email, "password": PASSWORD})
    assert resp.status_code in (200, 201), resp.text
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    user.roles_csv = role
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client, email):
    resp = client.post('/api/auth/login', json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_property(db_session, owner, *, name="Riverside Apartments", city="Nairobi"):
    prop = Property(
        owner_id=owner.id,
        name=name,
        city=city,
        property_type="apartment",
        status="active",
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop


def _tours_url(property_id):
    return f'/api/properties/{property_id}/tours'


class TestTourUrlParsing:
    """Provider detection + server-side embed URL rebuilding."""

    def test_matterport_share_link(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        resp = client.post(_tours_url(prop.id), json={
            "url": "https://my.matterport.com/show/?m=SxQL3iGyoDo",
            "title": "Living room 360",
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["provider"] == "matterport"
        assert body["embed_url"] == "https://my.matterport.com/show/?m=SxQL3iGyoDo"

    def test_matterport_models_link_rebuilt(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        resp = client.post(_tours_url(prop.id), json={
            "url": "https://matterport.com/models/abcDEF123456",
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        assert resp.json()["embed_url"] == "https://my.matterport.com/show/?m=abcDEF123456"

    def test_youtube_watch_link(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        resp = client.post(_tours_url(prop.id), json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["provider"] == "youtube"
        assert body["embed_url"] == "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"

    def test_youtube_short_link(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        resp = client.post(_tours_url(prop.id), json={"url": "https://youtu.be/dQw4w9WgXcQ"}, headers=headers)
        assert resp.status_code == 201, resp.text
        assert resp.json()["embed_url"] == "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"

    def test_kuula_roundme_sketchfab(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        cases = [
            ("https://kuula.co/share/7Zg6p", "kuula", "https://kuula.co/share/7Zg6p"),
            ("https://roundme.com/tour/12345/", "roundme", "https://roundme.com/tour/12345/"),
            (
                "https://sketchfab.com/3d-models/apartment-walkthrough-0123456789abcdef0123456789abcdef",
                "sketchfab",
                "https://sketchfab.com/models/0123456789abcdef0123456789abcdef/embed",
            ),
        ]
        for url, provider, embed in cases:
            resp = client.post(_tours_url(prop.id), json={"url": url}, headers=headers)
            assert resp.status_code == 201, resp.text
            body = resp.json()
            assert body["provider"] == provider, url
            assert body["embed_url"] == embed, url

    def test_unknown_https_stays_plain_link(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        resp = client.post(_tours_url(prop.id), json={
            "url": "https://example.com/my-cloud-tour",
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["provider"] == "link"
        assert body["embed_url"] is None

    def test_userinfo_spoof_treated_as_plain_link(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        resp = client.post(_tours_url(prop.id), json={
            "url": "https://my.matterport.com@evil.example/show/?m=SxQL3iGyoDo",
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["provider"] == "link"
        assert body["embed_url"] is None

    def test_provider_with_bad_id_not_embedded(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        resp = client.post(_tours_url(prop.id), json={
            "url": "https://my.matterport.com/show/?m=../../evil",
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["provider"] == "matterport"
        assert body["embed_url"] is None

    def test_rejects_non_https_and_bad_input(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        for bad in ["http://my.matterport.com/show/?m=SxQL3iGyoDo", "javascript:alert(1)", "not a url", ""]:
            resp = client.post(_tours_url(prop.id), json={"url": bad}, headers=headers)
            assert resp.status_code == 422, f"{bad!r} -> {resp.status_code}"

        spaced = client.post(_tours_url(prop.id), json={
            "url": "https://my.matterport.com/show/?m=ab cd",
        }, headers=headers)
        assert spaced.status_code == 422


class TestTourCrud:
    def test_requires_authentication_to_create(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        prop = _make_property(db_session, owner)
        resp = client.post(_tours_url(prop.id), json={"url": "https://example.com/tour"})
        assert resp.status_code == 401

    def test_non_owner_cannot_create(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        other = _register(client, db_session, "owner", "oth")
        headers = _login(client, other.email)
        prop = _make_property(db_session, owner)

        resp = client.post(_tours_url(prop.id), json={"url": "https://example.com/tour"}, headers=headers)
        assert resp.status_code == 403

    def test_non_owner_cannot_list_via_owner_route(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        prop = _make_property(db_session, owner)
        client.post(_tours_url(prop.id), json={
            "url": "https://example.com/tour",
        }, headers=_login(client, owner.email))

        # Public listing works without auth (used by PropertyDetails).
        public = client.get(_tours_url(prop.id))
        assert public.status_code == 200
        assert len(public.json()) == 1

    def test_ordering_sort_order_then_id(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        for url, order in [
            ("https://example.com/first", 2),
            ("https://example.com/second", 1),
            ("https://example.com/third", 1),
        ]:
            resp = client.post(_tours_url(prop.id), json={"url": url, "sort_order": order}, headers=headers)
            assert resp.status_code == 201, resp.text

        listed = client.get(_tours_url(prop.id)).json()
        assert [t["url"] for t in listed] == [
            "https://example.com/second",
            "https://example.com/third",
            "https://example.com/first",
        ]

    def test_update_url_recomputes_embed(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)

        created = client.post(_tours_url(prop.id), json={
            "url": "https://example.com/tour", "title": "Old",
        }, headers=headers).json()
        assert created["embed_url"] is None

        resp = client.patch(f'{_tours_url(prop.id)}/{created["id"]}', json={
            "url": "https://my.matterport.com/show/?m=SxQL3iGyoDo",
            "title": "Updated tour",
        }, headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["provider"] == "matterport"
        assert body["embed_url"] == "https://my.matterport.com/show/?m=SxQL3iGyoDo"
        assert body["title"] == "Updated tour"

    def test_admin_can_manage_other_owners_tour(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        admin = _register(client, db_session, "admin", "adm")
        prop = _make_property(db_session, owner)
        created = client.post(_tours_url(prop.id), json={
            "url": "https://example.com/tour",
        }, headers=_login(client, owner.email)).json()

        admin_headers = _login(client, admin.email)
        resp = client.patch(f'{_tours_url(prop.id)}/{created["id"]}', json={"title": "Admin edit"}, headers=admin_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["title"] == "Admin edit"

        delete = client.delete(f'{_tours_url(prop.id)}/{created["id"]}', headers=admin_headers)
        assert delete.status_code == 204

    def test_non_owner_cannot_update_or_delete(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        other = _register(client, db_session, "owner", "oth")
        prop = _make_property(db_session, owner)
        created = client.post(_tours_url(prop.id), json={
            "url": "https://example.com/tour",
        }, headers=_login(client, owner.email)).json()

        other_headers = _login(client, other.email)
        assert client.patch(f'{_tours_url(prop.id)}/{created["id"]}', json={"title": "x"}, headers=other_headers).status_code == 403
        assert client.delete(f'{_tours_url(prop.id)}/{created["id"]}', headers=other_headers).status_code == 403

    def test_delete_removes_tour(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)
        created = client.post(_tours_url(prop.id), json={
            "url": "https://example.com/tour",
        }, headers=headers).json()

        resp = client.delete(f'{_tours_url(prop.id)}/{created["id"]}', headers=headers)
        assert resp.status_code == 204
        assert client.get(_tours_url(prop.id)).json() == []
        assert db_session.query(PropertyTour).count() == 0

    def test_missing_property_or_tour_404(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)
        other_prop = _make_property(db_session, owner, name="Other property")

        assert client.get(_tours_url(999999)).status_code == 404
        assert client.post(_tours_url(999999), json={"url": "https://example.com/t"}, headers=headers).status_code == 404
        assert client.patch(f'{_tours_url(prop.id)}/999999', json={"title": "x"}, headers=headers).status_code == 404
        assert client.delete(f'{_tours_url(prop.id)}/999999', headers=headers).status_code == 404

        created = client.post(_tours_url(prop.id), json={
            "url": "https://example.com/tour",
        }, headers=headers).json()
        # Tour exists, but not under other_prop -> 404 (no cross-property leak).
        resp = client.patch(f'{_tours_url(other_prop.id)}/{created["id"]}', json={"title": "x"}, headers=headers)
        assert resp.status_code == 404

    def test_tour_deleted_with_property(self, client, db_session):
        owner = _register(client, db_session, "owner", "own")
        headers = _login(client, owner.email)
        prop = _make_property(db_session, owner)
        client.post(_tours_url(prop.id), json={"url": "https://example.com/tour"}, headers=headers)

        resp = client.delete(f'/api/properties/{prop.id}', headers=headers)
        assert resp.status_code == 204, resp.text
        assert db_session.query(PropertyTour).count() == 0
