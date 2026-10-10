import sys
import os
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.models.user import User

client = TestClient(app)

ADMIN_EMAIL = 'kebirogabriel@gmail.com'
ADMIN_PASSWORD = 'onsomuRiley2022'

properties = [
    {"name": "The Meridian Residences", "property_type": "Residential", "city": "Kilimani", "country": "Kenya", "units_count": 96, "address": "Meridian Ave, Kilimani", "description": "Premium residential tower in Kilimani.", "purpose": "buy", "price": "KES 45,000,000", "price_label": "From KES 45M", "bedrooms": 3, "bathrooms": 2, "area": "180 sqm"},
    {"name": "Azure Heights", "property_type": "Residential", "city": "Westlands", "country": "Kenya", "units_count": 128, "address": "Azure Rd, Westlands", "description": "Modern apartment complex in Westlands.", "purpose": "rent", "price": "KES 85,000", "price_label": "KES 85,000/month", "bedrooms": 2, "bathrooms": 2, "area": "120 sqm", "deposit": "KES 170,000", "lease_term": "12 months"},
    {"name": "Nova Heights", "property_type": "Residential", "city": "Kileleshwa", "country": "Kenya", "units_count": 84, "address": "Nova St, Kileleshwa", "description": "Contemporary living near Kileleshwa.", "purpose": "buy", "price": "KES 38,000,000", "price_label": "From KES 38M", "bedrooms": 3, "bathrooms": 2, "area": "165 sqm"},
    {"name": "The Grand Arc", "property_type": "Mixed Use", "city": "Westlands", "country": "Kenya", "units_count": 114, "address": "Grand Arc Blvd, Westlands", "description": "Mixed-use development with retail and offices.", "purpose": "invest", "price": "KES 120,000,000", "price_label": "KES 120M", "bedrooms": 4, "bathrooms": 3, "area": "250 sqm"},
    {"name": "Urban Nexus", "property_type": "Mixed Use", "city": "Kilimani", "country": "Kenya", "units_count": 134, "address": "Nexus Way, Kilimani", "description": "Vibrant mixed-use property.", "purpose": "rent", "price": "KES 120,000", "price_label": "KES 120,000/month", "bedrooms": 3, "bathrooms": 2, "area": "140 sqm", "deposit": "KES 240,000", "lease_term": "12 months"},
    {"name": "Cedar Park Apartments", "property_type": "Residential", "city": "Kilimani", "country": "Kenya", "units_count": 72, "address": "Cedar Park Rd, Kilimani", "description": "Quiet residential community.", "purpose": "buy", "price": "KES 32,000,000", "price_label": "From KES 32M", "bedrooms": 2, "bathrooms": 2, "area": "110 sqm"},
    {"name": "Capital Square", "property_type": "Commercial", "city": "Nairobi CBD", "country": "Kenya", "units_count": 64, "address": "Capital Sq, Nairobi", "description": "Prime commercial office spaces.", "purpose": "invest", "price": "KES 85,000,000", "price_label": "KES 85M", "bedrooms": 0, "bathrooms": 0, "area": "500 sqm"},
    {"name": "The Pinnacle", "property_type": "Mixed Use", "city": "Upper Hill", "country": "Kenya", "units_count": 110, "address": "Pinnacle Ave, Upper Hill", "description": "Landmark mixed-use tower.", "purpose": "buy", "price": "KES 95,000,000", "price_label": "From KES 95M", "bedrooms": 4, "bathrooms": 3, "area": "280 sqm"},
    {"name": "The Haven Apartments", "property_type": "Residential", "city": "Lavington", "country": "Kenya", "units_count": 68, "address": "Haven Lane, Lavington", "description": "Comfortable family apartments.", "purpose": "rent", "price": "KES 95,000", "price_label": "KES 95,000/month", "bedrooms": 3, "bathrooms": 2, "area": "130 sqm", "deposit": "KES 190,000", "lease_term": "12 months"},
    {"name": "Greenview Residences", "property_type": "Residential", "city": "Ruaka", "country": "Kenya", "units_count": 80, "address": "Greenview Rd, Ruaka", "description": "Suburban residences in Ruaka.", "purpose": "buy", "price": "KES 28,000,000", "price_label": "From KES 28M", "bedrooms": 3, "bathrooms": 2, "area": "150 sqm"},
    {"name": "Skyline Towers", "property_type": "Commercial", "city": "Parklands", "country": "Kenya", "units_count": 52, "address": "Skyline Dr, Parklands", "description": "Business towers in Parklands.", "purpose": "invest", "price": "KES 65,000,000", "price_label": "KES 65M", "bedrooms": 0, "bathrooms": 0, "area": "400 sqm"},
    {"name": "Emerald Gardens", "property_type": "Residential", "city": "Karen", "country": "Kenya", "units_count": 40, "address": "Emerald Way, Karen", "description": "Exclusive garden apartments.", "purpose": "buy", "price": "KES 75,000,000", "price_label": "From KES 75M", "bedrooms": 4, "bathrooms": 3, "area": "220 sqm"},
    {"name": "Riverside Plaza", "property_type": "Commercial", "city": "Westlands", "country": "Kenya", "units_count": 75, "address": "Riverside Ave, Westlands", "description": "Retail and office plaza.", "purpose": "rent", "price": "KES 150,000", "price_label": "KES 150,000/month", "bedrooms": 0, "bathrooms": 0, "area": "350 sqm", "deposit": "KES 300,000", "lease_term": "24 months"},
    {"name": "Sunrise Court", "property_type": "Residential", "city": "Ruiru", "country": "Kenya", "units_count": 120, "address": "Sunrise Rd, Ruiru", "description": "Large residential development.", "purpose": "buy", "price": "KES 22,000,000", "price_label": "From KES 22M", "bedrooms": 2, "bathrooms": 1, "area": "90 sqm"},
    {"name": "The Arcadia", "property_type": "Residential", "city": "Syokimau", "country": "Kenya", "units_count": 90, "address": "Arcadia Ln, Syokimau", "description": "Modern family residences.", "purpose": "rent", "price": "KES 65,000", "price_label": "KES 65,000/month", "bedrooms": 3, "bathrooms": 2, "area": "125 sqm", "deposit": "KES 130,000", "lease_term": "12 months"},
]

# FIX (corrected): main.py mounts every router with app.include_router(..., prefix="/api"),
# and properties.py itself uses APIRouter(prefix="/properties"), so the real path is
# /api/properties/... — NOT /properties/... A previous pass on this file stripped the
# /api prefix by mistake; restoring it here since main.py confirms it's required.
AUTH_REGISTER_PATH = '/api/auth/register'
AUTH_LOGIN_PATH = '/api/auth/login'
PROPERTIES_PATH = '/api/properties/'


def ensure_admin():
    try:
        resp = client.post(AUTH_REGISTER_PATH, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "full_name": "PropNoxa Admin"})
        print('register', resp.status_code, resp.text[:200])
    except Exception as e:
        print('register exception', e)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if user:
            user.role = 'admin'
            db.add(user)
            db.commit()
            print('ensured admin role for', ADMIN_EMAIL)
        else:
            print('WARNING: admin user not found after register — check AUTH_REGISTER_PATH matches your auth router')
    finally:
        db.close()


def login():
    """
    FIX: this used to POST JSON only. If your auth route depends on FastAPI's
    OAuth2PasswordRequestForm (very common for the /auth/login pattern), it
    requires application/x-www-form-urlencoded body with 'username'/'password'
    fields, NOT JSON — a JSON POST to that kind of route returns 422 and no
    token, so every subsequent property create then fails with 401 (silently,
    since the old script never checked status codes). This tries JSON first,
    and falls back to form-encoding automatically if that fails.
    """
    resp = client.post(AUTH_LOGIN_PATH, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    print('login (json)', resp.status_code)

    token = None
    if resp.status_code < 400:
        try:
            token = resp.json().get('access_token')
        except Exception:
            pass

    if not token:
        resp = client.post(AUTH_LOGIN_PATH, data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        print('login (form fallback)', resp.status_code)
        try:
            body = resp.json()
            print('login body', body)
            token = body.get('access_token') if isinstance(body, dict) else None
        except Exception:
            print('login text', resp.text)

    if token:
        client.headers.update({'Authorization': f'Bearer {token}'})
    else:
        print('WARNING: no access_token obtained via JSON or form login — property creates will 401. Check your auth router\'s expected request shape.')
    return resp


def create_properties():
    created, failed = 0, 0
    for p in properties:
        try:
            resp = client.post(PROPERTIES_PATH, json=p)
            if resp.status_code == 201:
                created += 1
            else:
                failed += 1
                print('create FAILED', p['name'], resp.status_code, resp.text[:200])
        except Exception as e:
            failed += 1
            print('create exception for', p['name'], e)
    print(f'Created {created}/{len(properties)} properties ({failed} failed)')


if __name__ == '__main__':
    try:
        ensure_admin()
        login()
        create_properties()
        print('Done')
    except Exception:
        traceback.print_exc()
        sys.exit(1)