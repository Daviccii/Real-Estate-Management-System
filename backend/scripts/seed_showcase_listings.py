"""Seed a wide, presentation-ready property catalogue.

Adds listings across many Kenyan towns/neighbourhoods, every mainstream
property type, all bedroom bands (studio/bedsitter through 6-bed), and price
ranges from KSh 3.2M to KSh 200M, plus rent from KSh 9.5k to KSh 350k.

Also:
  * assigns every property (old and new) a type-matched photo from the local
    library in frontend public/property-images, mirroring the exact mapping
    used by src/utils/propertyImages.ts so the DB and the frontend agree;
  * fixes PropNoxa Demo Court (id 17) which had no price/bedrooms.

Idempotent: rows are matched by name; existing rows are only topped up with
missing fields. Safe to re-run.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database.database import SessionLocal
from app.models.property import Property

IMG = '/property-images'

# Mirrors src/utils/propertyImages.ts LIBRARY / resolveKind() exactly.
LIBRARY = {
    'apartment': [f'{IMG}/apartment-{i}.jpg' for i in (1, 2, 3, 4)],
    'apartmentInterior': [f'{IMG}/apartment-interior-{i}.jpg' for i in (1, 2)],
    'studio': [f'{IMG}/studio-{i}.jpg' for i in (1, 2)],
    'penthouse': [f'{IMG}/penthouse-1.jpg'],
    'villa': [f'{IMG}/villa-{i}.jpg' for i in (1, 2)],
    'mansion': [f'{IMG}/mansion-{i}.jpg' for i in (1, 2)],
    'bungalow': [f'{IMG}/bungalow-{i}.jpg' for i in (1, 2)],
    'townhouse': [f'{IMG}/townhouse-{i}.jpg' for i in (1, 2)],
    'maisonette': [f'{IMG}/maisonette-{i}.jpg' for i in (1, 2)],
    'office': [f'{IMG}/office-{i}.jpg' for i in (1, 2)],
    'commercial': [f'{IMG}/commercial-{i}.jpg' for i in (1, 2)],
    'warehouse': [f'{IMG}/warehouse-{i}.jpg' for i in (1, 2)],
    'land': [f'{IMG}/land-{i}.jpg' for i in (1, 2)],
}


def resolve_kind(prop_type, purpose, pid):
    t = (prop_type or '').lower()
    if 'bedsitter' in t or 'bedsit' in t or 'studio' in t:
        return 'studio'
    if 'penthouse' in t:
        return 'penthouse'
    if 'apartment' in t or 'flat' in t:
        if (purpose or '').lower() == 'rent' and abs(pid) % 2 == 1:
            return 'apartmentInterior'
        return 'apartment'
    if 'villa' in t:
        return 'villa'
    if 'mansion' in t:
        return 'mansion'
    if 'bungalow' in t:
        return 'bungalow'
    if 'townhouse' in t or 'town house' in t:
        return 'townhouse'
    if 'maisonette' in t:
        return 'maisonette'
    if 'office' in t or 'mixed' in t:
        return 'office'
    if 'commercial' in t or 'shop' in t or 'retail' in t or 'plaza' in t or 'mall' in t:
        return 'commercial'
    if 'industrial' in t or 'warehouse' in t or 'godown' in t or 'factory' in t:
        return 'warehouse'
    if 'land' in t or 'plot' in t:
        return 'land'
    return 'apartment'


def image_for(prop_type, purpose, pid):
    pool = LIBRARY[resolve_kind(prop_type, purpose, pid)]
    return pool[abs(int(pid)) % len(pool)]


def gallery_for(prop_type, purpose, pid):
    main = image_for(prop_type, purpose, pid)
    kind = resolve_kind(prop_type, purpose, pid)
    parity = abs(int(pid)) % 2 + 1
    if kind in ('studio', 'apartmentInterior', 'apartment', 'penthouse',
                'villa', 'mansion', 'bungalow', 'townhouse', 'maisonette'):
        extras = [f'{IMG}/bedroom-{parity}.jpg', f'{IMG}/kitchen-{parity}.jpg']
    elif kind == 'land':
        extras = [LIBRARY['land'][abs(int(pid)) % 2]]
    else:
        pool = LIBRARY[kind]
        extras = [pool[(abs(int(pid)) + 1) % len(pool)]]
    seen, gallery = set(), []
    for url in [main, *extras]:
        if url not in seen:
            seen.add(url)
            gallery.append(url)
    return json.dumps(gallery)


# (name, type, purpose, price, beds, baths, area, city, county, sub_location,
#  landmark, lat, lng, verified, description, amenities,
#  deposit, lease_term, furnishing, parking, agent_id, manager_id)
NEW_LISTINGS = [
    # ---------------- Nairobi rentals ----------------
    ("Riverside Drive Studio Suites", "Studio", "rent", "18000", 0, 1, "45 sqm",
     "Riverside", "Nairobi", "Riverside", "Riverside Drive near German Embassy",
     -1.2685, 36.7951, True,
     "Bright studio suites on Riverside Drive with fitted kitchenette, secure underground parking and backup power. Walking distance to Westlands offices.",
     "Backup Generator, Borehole, CCTV, Lift, Secure Parking",
     "KSh 36,000", "12 months", "semi-furnished", 1, 96, 94),
    ("Kilimani Bedsitter Mews", "Bedsitter", "rent", "12000", 0, 1, "28 sqm",
     "Kilimani", "Nairobi", "Kilimani", "Off Argwings Kodhek Road",
     -1.2921, 36.7937, True,
     "Neat bedsitter in a quiet Kilimani mews, tiled floors, instant shower and own prepaid meter. Minutes to Yaya Centre and matatu routes.",
     "CCTV, Prepaid Meter, Water Tank, Gated",
     "KSh 24,000", "12 months", "unfurnished", 0, 96, None),
    ("Donholm Phase 5 Bedsitter", "Bedsitter", "rent", "9500", 0, 1, "24 sqm",
     "Donholm", "Nairobi", "Donholm", "Near Donholm Roundabout",
     -1.3021, 36.8887, False,
     "Affordable bedsitter in Donholm Phase 5 with reliable water, own meter and easy access to Outer Ring Road and Thika Superhighway.",
     "Water Tank, Prepaid Meter, Gated, Ample Parking",
     "KSh 19,000", "12 months", "unfurnished", 0, None, None),
    ("Roysambu Lumumba Studio Apartments", "Studio", "rent", "15000", 0, 1, "35 sqm",
     "Roysambu", "Nairobi", "Roysambu", "Lumumba Drive",
     -1.2221, 36.8842, True,
     "Modern studio apartments along Lumumba Drive, Roysambu. Open-plan layout with kitchenette, lift access and standby generator.",
     "Lift, Backup Generator, CCTV, Borehole",
     "KSh 30,000", "12 months", "semi-furnished", 1, 96, None),
    ("Parklands 1-Bedroom City Apartment", "Apartment", "rent", "45000", 1, 1, "65 sqm",
     "Parklands", "Nairobi", "Parklands", "3rd Parklands Avenue",
     -1.2627, 36.8123, True,
     "Executive 1-bedroom apartment on 3rd Parklands Avenue with gym, rooftop terrace and 24-hour concierge. Near Aga Khan Hospital and Sarit Centre.",
     "Gym, Rooftop Terrace, Concierge, Lift, Backup Generator, CCTV",
     "KSh 90,000", "12 months", "fully-furnished", 1, 96, 94),
    ("Embakasi Pipeline 1-Bedroom Apartment", "Apartment", "rent", "22000", 1, 1, "55 sqm",
     "Embakasi", "Nairobi", "Embakasi", "Pipeline Estate",
     -1.3180, 36.8920, True,
     "Spacious 1-bedroom unit in Pipeline with borehole water, tiled floors and quick access to JKIA and Outering Road.",
     "Borehole, Water Tank, CCTV, Gated",
     "KSh 44,000", "12 months", "unfurnished", 1, None, None),
    ("South C Cosy 2-Bedroom Apartment", "Apartment", "rent", "38000", 2, 2, "90 sqm",
     "South C", "Nairobi", "South C", "Near South C Shopping Centre",
     -1.3200, 36.8280, True,
     "Well-kept 2-bedroom apartment in South C with master ensuite, balcony and secure parking. Family-friendly neighbourhood near schools and shopping.",
     "CCTV, Gated, Playground, Water Tank",
     "KSh 76,000", "12 months", "unfurnished", 1, None, 94),
    ("South B Family 3-Bedroom Apartment", "Apartment", "rent", "42000", 3, 2, "110 sqm",
     "South B", "Nairobi", "South B", "Mariakani Road",
     -1.3133, 36.8337, True,
     "Family-sized 3-bedroom apartment along Mariakani Road with servant quarters and borehole. Walking distance to Mariakani Primary and Capital Centre.",
     "Borehole, Servant Quarter, CCTV, Gated, Parking",
     "KSh 84,000", "12 months", "unfurnished", 2, None, None),
    ("Kasarani Sunton 2-Bedroom Apartment", "Apartment", "rent", "28000", 2, 1, "75 sqm",
     "Kasarani", "Nairobi", "Kasarani", "Sunton Estate",
     -1.2280, 36.9010, False,
     "Clean 2-bedroom apartment in Sunton, Kasarani with own meter, steady water supply and quick matatu access to town via Mwiki Road.",
     "Prepaid Meter, Water Tank, Gated",
     "KSh 56,000", "12 months", "unfurnished", 1, None, None),
    ("Ruaka 2-Bedroom Apartment", "Apartment", "rent", "35000", 2, 2, "88 sqm",
     "Ruaka", "Nairobi", "Ruaka", "Near Two Rivers Mall",
     -1.2155, 36.7944, True,
     "Modern 2-bedroom apartment in Ruaka minutes from Two Rivers and the Limuru Road expressway. Kids play area, borehole and gym.",
     "Gym, Playground, Borehole, Lift, CCTV",
     "KSh 70,000", "12 months", "semi-furnished", 1, 96, 94),
    ("Kileleshwa Executive 2-Bedroom Apartment", "Apartment", "rent", "70000", 2, 2, "105 sqm",
     "Kileleshwa", "Nairobi", "Kileleshwa", "Laikipia Road",
     -1.2841, 36.7800, True,
     "Executive 2-bedroom apartment on Laikipia Road, Kileleshwa with DSQ option, swimming pool, gym and full backup power.",
     "Swimming Pool, Gym, Lift, Backup Generator, CCTV, Borehole",
     "KSh 140,000", "12 months", "semi-furnished", 2, 96, 94),
    ("Westlands Pearl 2-Bedroom Apartment", "Apartment", "rent", "85000", 2, 2, "110 sqm",
     "Westlands", "Nairobi", "Westlands", "Off Waiyaki Way",
     -1.2678, 36.8078, True,
     "Refined 2-bedroom apartment in Westlands off Waiyaki Way with heated pool, sky lounge and 24/7 security. Walk to Sarit Centre.",
     "Heated Pool, Sky Lounge, Gym, Concierge, Lift, Backup Generator",
     "KSh 170,000", "12 months", "fully-furnished", 2, 96, 94),
    ("Hurlingham 3-Bedroom Apartment", "Apartment", "rent", "80000", 3, 2, "130 sqm",
     "Hurlingham", "Nairobi", "Hurlingham", "Argwings Kodhek Road",
     -1.2965, 36.7960, True,
     "Roomy 3-bedroom apartment in Hurlingham with DSQ, borehole and gym. Close to Yaya Centre, schools and hospital.",
     "Gym, Borehole, Servant Quarter, Lift, CCTV",
     "KSh 160,000", "12 months", "unfurnished", 2, None, 94),
    ("Lavington Garden Maisonette", "Maisonette", "rent", "150000", 3, 3, "180 sqm",
     "Lavington", "Nairobi", "Lavington", "Muthangari Drive",
     -1.2790, 36.7680, True,
     "Elegant 3-bedroom garden maisonette on Muthangari Drive with private lawn, DSQ and solar water heating in a gated Lavington compound.",
     "Private Garden, Solar Water Heating, Servant Quarter, Electric Fence, Borehole",
     "KSh 300,000", "24 months", "semi-furnished", 2, None, 94),
    ("Spring Valley 4-Bedroom Maisonette", "Maisonette", "rent", "180000", 4, 4, "240 sqm",
     "Spring Valley", "Nairobi", "Spring Valley", "Off Riverside Drive",
     -1.2660, 36.7870, True,
     "All-ensuite 4-bedroom maisonette in Spring Valley with mature garden, double garage and full inverter backup. Diplomatic neighbourhood.",
     "Private Garden, Inverter Backup, Double Garage, Electric Fence, Borehole",
     "KSh 360,000", "24 months", "semi-furnished", 3, None, None),
    ("Langata 4-Bedroom Townhouse", "Townhouse", "rent", "120000", 4, 3, "200 sqm",
     "Langata", "Nairobi", "Langata", "Near Galleria Mall",
     -1.3530, 36.7580, True,
     "Modern 4-bedroom townhouse in a gated Langata community near Galleria, with clubhouse, playground and borehole water.",
     "Clubhouse, Playground, Borehole, Electric Fence, CCTV",
     "KSh 240,000", "12 months", "unfurnished", 2, None, 94),
    ("Runda Ambassadorial 5-Bedroom Villa", "Villa", "rent", "250000", 5, 5, "350 sqm",
     "Runda", "Nairobi", "Runda", "Runda Drive",
     -1.2210, 36.8060, True,
     "Stately 5-bedroom villa on Runda Drive with manicured acre garden, staff quarters and generator. Ideal for diplomatic missions.",
     "Acre Garden, Staff Quarters, Generator, Electric Fence, Borehole, Alarm",
     "KSh 500,000", "24 months", "semi-furnished", 4, None, None),
    ("Gigiri Diplomatic 5-Bedroom Villa", "Villa", "rent", "350000", 5, 5, "400 sqm",
     "Gigiri", "Nairobi", "Gigiri", "UN Avenue",
     -1.2330, 36.8080, True,
     "Premium 5-bedroom villa on UN Avenue, Gigiri with heated pool, cinema room and 2 staff quarters. Minutes to UN complex and Village Market.",
     "Heated Pool, Cinema Room, Staff Quarters, Generator, Electric Fence, CCTV",
     "KSh 700,000", "24 months", "fully-furnished", 4, None, 94),
    ("Muthaiga 6-Bedroom Mansion", "Mansion", "rent", "300000", 6, 6, "550 sqm",
     "Muthaiga", "Nairobi", "Muthaiga", "Muthaiga Road",
     -1.2450, 36.8320, False,
     "Grand 6-bedroom mansion off Muthaiga Road set on 1.5 acres with tennis court, pool and 3 staff quarters. Old-money charm with modern finishes.",
     "Tennis Court, Swimming Pool, Staff Quarters, Generator, Electric Fence, Borehole",
     "KSh 600,000", "24 months", "semi-furnished", 6, None, None),
    ("Upper Hill Executive Office Suite", "Office", "rent", "150000", 0, 2, "220 sqm",
     "Upper Hill", "Nairobi", "Upper Hill", "Upper Hill Road",
     -1.2996, 36.8166, True,
     "Grade A office suite in Upper Hill with panoramic skyline views, fibre connectivity, 4 reserved parking bays and 24/7 access control.",
     "Central AC, Fibre Internet, Lift, Backup Generator, Access Control, 4 Parking Bays",
     "KSh 450,000", "24 months", "furnished", 4, None, None),
    ("Nairobi CBD Kimathi Retail Shop", "Commercial", "rent", "90000", 0, 1, "85 sqm",
     "Nairobi CBD", "Nairobi", "Nairobi CBD", "Kimathi Street",
     -1.2840, 36.8220, True,
     "High-footfall retail shop on Kimathi Street with glass frontage, mezzanine storage and steady foot traffic from surrounding banks and offices.",
     "Glass Frontage, Mezzanine Storage, Backup Power, CCTV",
     "KSh 270,000", "36 months", "unfurnished", 0, None, None),
    # ---------------- Coastal & upcountry rentals ----------------
    ("Nyali Beachfront 3-Bedroom Apartment", "Apartment", "rent", "120000", 3, 3, "165 sqm",
     "Nyali", "Mombasa", "Nyali", "Links Road",
     -4.0330, 39.7000, True,
     "Beachfront 3-bedroom apartment on Nyali Links Road with ocean-view balcony, infinity pool and gym. Fully serviced with backup power.",
     "Infinity Pool, Ocean View, Gym, Lift, Backup Generator, CCTV",
     "KSh 240,000", "12 months", "fully-furnished", 2, 96, 94),
    ("Bamburi 2-Bedroom Apartment", "Apartment", "rent", "45000", 2, 2, "95 sqm",
     "Bamburi", "Mombasa", "Bamburi", "Bamburi Beach Road",
     -3.9930, 39.7180, False,
     "Airy 2-bedroom apartment near Bamburi Beach with communal pool, borehole and standby generator. Short walk to Haller Park and beach hotels.",
     "Pool, Borehole, Generator, CCTV, Gated",
     "KSh 90,000", "12 months", "semi-furnished", 1, None, None),
    ("Mtwapa 1-Bedroom Apartment", "Apartment", "rent", "25000", 1, 1, "60 sqm",
     "Mtwapa", "Kilifi", "Mtwapa", "Mtwapa Creek",
     -3.9400, 39.7440, True,
     "Budget-friendly 1-bedroom apartment in Mtwapa with own meter, casual parking and easy access to Mombasa-Malindi highway.",
     "Prepaid Meter, Water Tank, Gated, Parking",
     "KSh 50,000", "12 months", "unfurnished", 1, None, None),
    # ---------------- Buyers ----------------
    ("Juja 2-Bedroom Starter Apartment", "Apartment", "buy", "4500000", 2, 1, "82 sqm",
     "Juja", "Kiambu", "Juja", "Near JKUAT Main Gate",
     -1.1010, 37.0140, True,
     "Affordable 2-bedroom apartment near JKUAT ideal for staff, students' hostels or first-time buyers. High rental demand area with 10%+ gross yields.",
     "Lift, Backup Generator, CCTV, Gated",
     "KSh 450,000", "Freehold / 99-yr lease", "unfurnished", 1, None, None),
    ("Ngong 50x100 Residential Plot", "Land", "buy", "3200000", 0, 0, "1/8 acre",
     "Ngong", "Kajiado", "Ngong", "Ngong Town",
     -1.3600, 36.6600, False,
     "Ready-to-build 50x100 residential plot in Ngong with red soil, water and electricity on site. Title deed ready, immediate transfer.",
     "Water On Site, Electricity, Ready Title, Fenced",
     None, "Freehold", None, 0, None, None),
    ("Kitengela Acacia Ready Plot", "Land", "buy", "3800000", 0, 0, "1/8 acre",
     "Kitengela", "Kajiado", "Kitengela", "Acacia Estate",
     -1.4830, 36.9570, True,
     "Prime 50x100 plot in gated Acacia Estate, Kitengela with perimeter wall, graded roads and utilities. Fast-growing residential corridor.",
     "Gated Community, Perimeter Wall, Graded Roads, Utilities",
     None, "Freehold", None, 0, None, None),
    ("Thika Road 2-Bedroom Apartment", "Apartment", "buy", "4200000", 2, 2, "90 sqm",
     "Thika", "Kiambu", "Thika", "Near Thika Greens",
     -1.0330, 37.0740, False,
     "New 2-bedroom apartment near Thika Greens with lift, kids' playground and 8.5% projected rental yield. Ideal investment starter home.",
     "Lift, Playground, Backup Generator, CCTV",
     "KSh 420,000", "99-yr lease", "unfurnished", 1, None, None),
    ("Ongata Rongai 3-Bedroom Apartment", "Apartment", "buy", "6500000", 3, 2, "115 sqm",
     "Ongata Rongai", "Kajiado", "Ongata Rongai", "Near Tuskys Rongai",
     -1.4020, 36.7530, True,
     "Spacious 3-bedroom apartment in Ongata Rongai with master ensuite, borehole and ample parking. Great value entry into home ownership.",
     "Borehole, CCTV, Ample Parking, Water Tank",
     "KSh 650,000", "Freehold / 99-yr lease", "unfurnished", 2, None, None),
    ("Syokimau 3-Bedroom Apartment", "Apartment", "buy", "8000000", 3, 2, "125 sqm",
     "Syokimau", "Machakos", "Syokimau", "Katani Road",
     -1.4420, 36.9630, True,
     "Modern 3-bedroom apartment off Katani Road, Syokimau near SGR station. Lift, gym and backup power in a secure gated community.",
     "Lift, Gym, Backup Generator, CCTV, Gated",
     "KSh 800,000", "99-yr lease", "semi-furnished", 2, None, 94),
    ("Kikuyu 3-Bedroom Bungalow", "Bungalow", "buy", "9500000", 3, 2, "120 sqm",
     "Kikuyu", "Kiambu", "Kikuyu", "Kikuyu Town",
     -1.2470, 36.6630, True,
     "Well-maintained 3-bedroom bungalow on an eighth-acre in Kikuyu Town with mature garden, borehole and separate servant room.",
     "Private Garden, Borehole, Servant Room, Gated",
     "KSh 950,000", "Freehold", "unfurnished", 2, None, None),
    ("Ruiru Kamakis 3-Bedroom Townhouse", "Townhouse", "buy", "11000000", 3, 3, "160 sqm",
     "Ruiru", "Kiambu", "Ruiru", "Kamakis",
     -1.1590, 36.9960, True,
     "Contemporary 3-bedroom townhouse in Kamakis, Ruiru with rooftop terrace, DSQ and gated compound. Minutes to Eastern Bypass.",
     "Rooftop Terrace, Servant Quarter, Electric Fence, Borehole",
     "KSh 1,100,000", "Freehold", "unfurnished", 2, None, None),
    ("Athi River 4-Bedroom Maisonette", "Maisonette", "buy", "13500000", 4, 3, "210 sqm",
     "Athi River", "Machakos", "Athi River", "Great Wall Estate",
     -1.4560, 36.9830, True,
     "All-ensuite 4-bedroom maisonette in Great Wall Estate, Athi River with DSQ, borehole and clubhouse. Family-friendly gated community near EPZ.",
     "Clubhouse, Servant Quarter, Borehole, Electric Fence, Playground",
     "KSh 1,350,000", "Freehold", "unfurnished", 3, None, 94),
    ("Kileleshwa 3-Bedroom Apartment", "Apartment", "buy", "15000000", 3, 2, "140 sqm",
     "Kileleshwa", "Nairobi", "Kileleshwa", "Gatundu Road",
     -1.2820, 36.7790, True,
     "High-floor 3-bedroom apartment on Gatundu Road with city views, pool and gym. Strong capital appreciation in Kileleshwa corridor.",
     "Swimming Pool, Gym, Lift, Backup Generator, CCTV",
     "KSh 1,500,000", "99-yr lease", "semi-furnished", 2, None, None),
    ("Lavington 4-Bedroom Townhouse", "Townhouse", "buy", "25000000", 4, 4, "220 sqm",
     "Lavington", "Nairobi", "Lavington", "Muthangari",
     -1.2800, 36.7690, True,
     "Elegant 4-bedroom townhouse in Lavington with private garden, DSQ and double garage. Sought-after school catchment area.",
     "Private Garden, Servant Quarter, Double Garage, Electric Fence",
     "KSh 2,500,000", "Freehold", "unfurnished", 3, None, 94),
    ("Karen 5-Bedroom Villa", "Villa", "buy", "85000000", 5, 5, "450 sqm",
     "Karen", "Nairobi", "Karen", "Karen Road",
     -1.3300, 36.7100, True,
     "Timeless 5-bedroom villa on half an acre along Karen Road with mature indigenous garden, pool and staff quarters. Serene, secure and private.",
     "Half-Acre Garden, Swimming Pool, Staff Quarters, Borehole, Electric Fence",
     "KSh 8,500,000", "Freehold", "semi-furnished", 4, None, None),
    ("Runda Modern 6-Bedroom Mansion", "Mansion", "buy", "150000000", 6, 7, "700 sqm",
     "Runda", "Nairobi", "Runda", "Runda Mumwe",
     -1.2180, 36.8100, True,
     "Architect-designed 6-bedroom mansion in Runda Mumwe with home cinema, heated pool, gym and 3 staff quarters set on 1.25 acres.",
     "Home Cinema, Heated Pool, Gym, Staff Quarters, Generator, Electric Fence",
     "KSh 15,000,000", "Freehold", "fully-furnished", 6, None, None),
    ("Nyali Luxury 3-Bedroom Apartment", "Apartment", "buy", "13500000", 3, 3, "170 sqm",
     "Nyali", "Mombasa", "Nyali", "Links Road",
     -4.0350, 39.7020, True,
     "Serviced 3-bedroom apartment off Nyali Links Road steps from the beach. Pool, gym and strong holiday-let yields of 8-10% gross.",
     "Pool, Gym, Lift, Backup Generator, CCTV, Serviced",
     "KSh 1,350,000", "99-yr lease", "fully-furnished", 2, None, 94),
    ("Diani 4-Bedroom Beach Villa", "Villa", "buy", "65000000", 4, 4, "380 sqm",
     "Diani", "Kwale", "Diani", "Diani Beach Road",
     -4.2850, 39.5920, True,
     "White-washed 4-bedroom beach villa on Diani Beach Road with direct beach access, infinity pool and separate guest cottage. Proven holiday-rental income.",
     "Beach Access, Infinity Pool, Guest Cottage, Staff Quarters, Solar",
     "KSh 6,500,000", "Freehold", "fully-furnished", 2, None, None),
    ("Milimani Nakuru 4-Bedroom Maisonette", "Maisonette", "buy", "14500000", 4, 3, "230 sqm",
     "Milimani", "Nakuru", "Milimani", "Milimani Estate",
     -0.2910, 36.0740, True,
     "Elegant 4-bedroom maisonette in Milimani, Nakuru with sprawling lawn, DSQ and solar water heating in a leafy estate near the hospital.",
     "Lawn, Servant Quarter, Solar Water Heating, Borehole, Alarm",
     "KSh 1,450,000", "Freehold", "semi-furnished", 2, None, None),
    ("Nakuru CBD 2-Bedroom Apartment", "Apartment", "buy", "6800000", 2, 2, "95 sqm",
     "Nakuru CBD", "Nakuru", "Nakuru CBD", "Kenyatta Avenue",
     -0.2860, 36.0660, False,
     "Central 2-bedroom apartment on Kenyatta Avenue, Nakuru CBD with lift and backup generator. Walk to shops, banks and offices.",
     "Lift, Backup Generator, CCTV, Gated",
     "KSh 680,000", "Freehold / 99-yr lease", "unfurnished", 1, None, None),
    ("Kisumu Milimani 3-Bedroom Bungalow", "Bungalow", "buy", "11500000", 3, 2, "140 sqm",
     "Milimani", "Kisumu", "Milimani", "Milimani Estate",
     -0.0890, 34.7620, True,
     "Solid 3-bedroom bungalow on a quarter-acre in Milimani, Kisumu with mature trees, borehole and room to extend.",
     "Quarter-Acre, Borehole, Mature Trees, Gated",
     "KSh 1,150,000", "Freehold", "unfurnished", 2, None, None),
    ("Eldoret Elgon View 4-Bedroom Maisonette", "Maisonette", "buy", "13000000", 4, 3, "200 sqm",
     "Elgon View", "Uasin Gishu", "Elgon View", "Elgon View Estate",
     -0.0580, 35.2840, True,
     "Beautifully finished 4-bedroom maisonette in Elgon View, Eldoret with garden, DSQ and solar backup. Prestigious neighbourhood near Moi University.",
     "Garden, Servant Quarter, Solar Backup, Electric Fence",
     "KSh 1,300,000", "Freehold", "semi-furnished", 2, None, None),
    ("Nyeri CBD 3-Bedroom Apartment", "Apartment", "buy", "7500000", 3, 2, "110 sqm",
     "Nyeri CBD", "Nyeri", "Nyeri CBD", "Kimathi Way",
     -0.4230, 36.9480, False,
     "Modern 3-bedroom apartment on Kimathi Way, Nyeri with lift, parking and standby water. Ideal rental income or starter home.",
     "Lift, Water Storage, Backup Generator, Gated",
     "KSh 750,000", "Freehold / 99-yr lease", "unfurnished", 1, None, None),
    ("Naivasha 5-Bedroom Villa", "Villa", "buy", "32000000", 5, 4, "320 sqm",
     "Naivasha", "Nakuru", "Naivasha", "Moi South Lake Road",
     -0.7200, 36.4300, True,
     "Rustic-luxury 5-bedroom villa off Moi South Lake Road, Naivasha with lake views, landscaped garden and guest cottage. Weekend escape or Airbnb gold.",
     "Lake View, Guest Cottage, Landscaped Garden, Solar, Borehole",
     "KSh 3,200,000", "Freehold", "semi-furnished", 4, None, None),
    # ---------------- Investments ----------------
    ("Kilimani 1-Bedroom Investment Apartment", "Apartment", "invest", "9500000", 1, 1, "60 sqm",
     "Kilimani", "Nairobi", "Kilimani", "Near Yaya Centre",
     -1.2930, 36.7870, True,
     "Tenanted 1-bedroom apartment near Yaya Centre currently let at KSh 55,000/month — 6.9% gross yield with strong tenant demand from young professionals.",
     "Lift, Backup Generator, CCTV, Gym",
     None, "Freehold / 99-yr lease", "furnished", 1, None, None),
    ("Ruaka Studio Investment Block", "Studio", "invest", "5500000", 1, 1, "42 sqm",
     "Ruaka", "Nairobi", "Ruaka", "Near Two Rivers",
     -1.2160, 36.7960, True,
     "Studios near Two Rivers letting at KSh 28,000/month — 6.1% gross yield in Nairobi's fastest-growing satellite town.",
     "Lift, Borehole, CCTV, Gated",
     None, "99-yr lease", "semi-furnished", 1, None, None),
    ("Upper Hill Commercial Office Floor", "Commercial", "invest", "48000000", 0, 2, "260 sqm",
     "Upper Hill", "Nairobi", "Upper Hill", "Hospital Road",
     -1.2990, 36.8160, True,
     "Whole-floor Grade A office in Upper Hill let to a multinational at KSh 320,000/month — 8% net yield with 5-year lease in place.",
     "Central AC, Lift, 6 Parking Bays, Backup Generator, Access Control",
     None, "Commercial Title", "furnished", 6, None, 94),
    ("Nakuru Section 58 Prime Plot", "Land", "invest", "2500000", 0, 0, "1/4 acre",
     "Nakuru CBD", "Nakuru", "Nakuru CBD", "Section 58",
     -0.2830, 36.0720, False,
     "Quarter-acre prime plot in Section 58, Nakuru ideal for rental apartments or commercial development. Utilities adjacent, ready title.",
     "Ready Title, Utilities Adjacent, Road Access",
     None, "Freehold", None, 0, None, None),
    ("Athi River EPZ Warehouse", "Warehouse", "invest", "22000000", 0, 2, "500 sqm",
     "Athi River", "Machakos", "Athi River", "EPZ Road",
     -1.4520, 36.9790, True,
     "Purpose-built 500 sqm warehouse off EPZ Road, Athi River with loading bay, 3-phase power and container parking — leased to a logistics firm.",
     "Loading Bay, 3-Phase Power, Container Parking, Perimeter Wall, Security",
     None, "Commercial Title", None, 4, None, None),
    ("Malindi Casuarina 1-Acre Beach Plot", "Land", "invest", "15000000", 0, 0, "1 acre",
     "Malindi", "Kilifi", "Malindi", "Casuarina Road",
     -3.2190, 40.1190, True,
     "One-acre beach plot off Casuarina Road, Malindi with 60m frontage potential for boutique hotel or villa development. Beach access.",
     "Beach Access, Surveyed, Ready Title, Fenced",
     None, "Freehold", None, 0, None, None),
    ("Watamu Boutique Guesthouse", "Commercial", "invest", "42000000", 8, 8, "650 sqm",
     "Watamu", "Kilifi", "Watamu", "Turtle Bay Road",
     -3.3550, 40.0200, True,
     "Turnkey 8-room boutique guesthouse on Turtle Bay Road, Watamu running at 72% occupancy. Pool, restaurant and staff quarters included.",
     "Pool, Restaurant, Staff Quarters, Ocean Proximity, Solar, Borehole",
     None, "Commercial Title", "furnished", 6, None, None),
]


def fmt_price_label(price, purpose):
    n = int(price)
    pretty = f"{n:,}"
    if purpose == 'rent':
        return f"KSh {pretty} / month"
    return f"KSh {pretty}"


def seed():
    db = SessionLocal()
    created = updated = 0
    try:
        owner_id = 95  # David Kamau (demo owner)
        for (name, ptype, purpose, price, beds, baths, area, city, county,
             sub_location, landmark, lat, lng, verified, descr, amenities,
             deposit, lease_term, furnishing, parking, agent_id, manager_id) in NEW_LISTINGS:
            existing = db.query(Property).filter(Property.name == name).first()
            payload = dict(
                property_type=ptype, purpose=purpose, price=price,
                price_label=fmt_price_label(price, purpose),
                bedrooms=beds, bathrooms=baths, area=area,
                city=city, county=county, sub_location=sub_location,
                landmark=landmark, latitude=lat, longitude=lng,
                country='Kenya', status='active', units_count=1,
                is_verified=verified,
                verification_status='verified' if verified else 'PENDING_VERIFICATION',
                description=descr, amenities=amenities,
                deposit=deposit, lease_term=lease_term,
                furnishing=furnishing, parking_spaces=parking or 0,
                address=f"{sub_location}, {city}, Kenya",
                allow_direct_contact=verified,
            )
            if existing:
                # Top up only rows this script owns; never clobber curated data.
                for k, v in payload.items():
                    if getattr(existing, k, None) in (None, ''):
                        setattr(existing, k, v)
                db.add(existing)
                updated += 1
            else:
                prop = Property(
                    owner_id=owner_id, company_id=1,
                    name=name, agent_id=agent_id, manager_id=manager_id,
                    **payload,
                )
                db.add(prop)
                created += 1
        db.commit()
        print(f"Listings: created {created}, topped-up {updated}")

        # Every property gets its type-matched photo + gallery (old and new).
        fixed = 0
        for p in db.query(Property).all():
            image = image_for(p.property_type, p.purpose, p.id)
            gallery = gallery_for(p.property_type, p.purpose, p.id)
            if p.image_url != image or p.gallery_urls != gallery:
                p.image_url = image
                p.gallery_urls = gallery
                fixed += 1
        db.commit()
        print(f"Images assigned to {fixed} properties")

        # PropNoxa Demo Court was seeded without pricing — complete it.
        demo = db.query(Property).filter(Property.name == 'PropNoxa Demo Court').first()
        if demo:
            changed = False
            for k, v in dict(
                price='65000', price_label='KSh 65,000 / month',
                bedrooms=2, bathrooms=2, sub_location='Kilimani',
                area='110 sqm', landmark='Argwings Kodhek Road, Kilimani',
                latitude=-1.2921, longitude=36.7937,
                deposit='KSh 130,000', lease_term='12 months',
                furnishing='unfurnished', parking_spaces=1,
                amenities='Borehole, CCTV, Gated, Backup Generator',
            ).items():
                if getattr(demo, k, None) in (None, ''):
                    setattr(demo, k, v)
                    changed = True
            if changed:
                db.add(demo)
                db.commit()
                print('Demo Court completed with price/bedrooms')

        total = db.query(Property).count()
        print(f"Total properties now: {total}")

        # Non-residential spaces don't carry a bedroom count — null out zeros
        # so a "Studio" bedroom filter never surfaces a plot or an office.
        normalized = (
            db.query(Property)
            .filter(
                Property.property_type.in_(
                    ['Land', 'Commercial', 'Office', 'Warehouse', 'Industrial']),
                Property.bedrooms == 0,
            )
            .update({Property.bedrooms: None}, synchronize_session=False)
        )
        db.commit()
        print(f"Normalized bedrooms on {normalized} non-residential rows")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed()
