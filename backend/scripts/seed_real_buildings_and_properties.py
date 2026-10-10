import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database.database import SessionLocal
from app.models.user import User
from app.models.building import Building
from app.models.property import Property

REAL_BUILDINGS = [
    {
        "name": "Britam Tower",
        "building_type": "Commercial Skyscraper",
        "address": "Hospital Road, Upper Hill",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Upper Hill",
        "latitude": -1.2996,
        "longitude": 36.8166,
        "landmark": "Near Nairobi Hospital & Equity Centre",
        "image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 31,
        "units_count": 180,
        "year_built": 2017,
        "description": "The iconic 31-storey prism-shaped landmark tower in Upper Hill, Nairobi. Offers Grade A office suites, panoramic skyline vistas, high-speed destination lifts, and 24/7 biometric security.",
        "amenities": "High-Speed Elevators, 24/7 CCTV, Backup Generators, Ample Basement Parking, Fibre Optic, Helipad, Conference Facilities, Coffee Shop"
    },
    {
        "name": "FCB Mihrab",
        "building_type": "Commercial & Corporate Plaza",
        "address": "Lenana Road, Kilimani",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Kilimani",
        "latitude": -1.2921,
        "longitude": 36.7937,
        "landmark": "Near Yaya Centre & Department of Defence",
        "image_url": "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 25,
        "units_count": 120,
        "year_built": 2018,
        "description": "An architectural masterpiece in Kilimani embodying modern Islamic architectural inspiration with eco-friendly design, rainwater harvesting, sensory prayer rooms, and premium corporate offices.",
        "amenities": "LEED Certified, High-Speed Lifts, Gym & Fitness Studio, 4-Level Basement Parking, Access Control, Cafeteria"
    },
    {
        "name": "The Mirage",
        "building_type": "Commercial & Mixed-Use Complex",
        "address": "Chiromo Road, Westlands",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Westlands",
        "latitude": -1.2678,
        "longitude": 36.8078,
        "landmark": "Opposite Villa Rosa Kempinski",
        "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 15,
        "units_count": 150,
        "year_built": 2016,
        "description": "A prestigious 3-tower commercial complex along Chiromo Road in Westlands, connecting Nairobi CBD and Westlands. Features luxury office suites, banking halls, and retail outlets.",
        "amenities": "Full Backup Generator, Borehole Water Supply, 6 High-Speed Lifts, 24-Hour Security, Access Control, Ample Parking"
    },
    {
        "name": "Le'Mac Towers",
        "building_type": "Luxury Mixed-Use & Sky Residences",
        "address": "Church Road, off Waiyaki Way, Westlands",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Westlands",
        "latitude": -1.2625,
        "longitude": 36.8005,
        "landmark": "Off Waiyaki Way near Sarit Centre",
        "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 24,
        "units_count": 140,
        "year_built": 2019,
        "description": "A 24-storey pinnacle of luxury living in Westlands featuring the renowned cantilevered sky glass floor walkway on the 24th floor, heated rooftop infinity pool, and luxury residential suites.",
        "amenities": "Rooftop Heated Pool, Sky Lounge & Restaurant, Gym & Spa, Glass Walkway, 24/7 Concierge, 3-tier Security"
    },
    {
        "name": "Two Rivers Riverbank Residences",
        "building_type": "Ultra-Modern Residential Estate",
        "address": "Limuru Road, Ruaka / Runda",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Ruaka",
        "latitude": -1.2155,
        "longitude": 36.7944,
        "landmark": "Within Two Rivers Mall Precinct",
        "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 17,
        "units_count": 160,
        "year_built": 2021,
        "description": "Premier residential community within East Africa's largest mixed-use development, Two Rivers. Boasts private clubhouse, river walks, direct mall access, and Olympic-size pools.",
        "amenities": "Olympic-Size Pool, Clubhouse, 7-Acre Park & Waterfront, Smart Home Automation, Fiber Optic, 24/7 Armed Security"
    },
    {
        "name": "UAP Old Mutual Tower",
        "building_type": "Commercial Skyscraper",
        "address": "Upper Hill Road, Upper Hill",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Upper Hill",
        "latitude": -1.2990,
        "longitude": 36.8193,
        "landmark": "Near Radisson Blu & British High Commission",
        "image_url": "https://images.unsplash.com/photo-1554469384-e58fac16e23a?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 33,
        "units_count": 210,
        "year_built": 2016,
        "description": "Towering at 163 meters, UAP Old Mutual Tower is one of East Africa's tallest buildings with Grade A certified commercial corporate spaces, banking halls, and premium facilities.",
        "amenities": "8 High Speed Elevators, 800-Car Parking Silo, Central Air Conditioning, Fire Suppression System, 24hr Security"
    },
    {
        "name": "14 Riverside (Riverside Office Park)",
        "building_type": "Commercial Corporate Office Park",
        "address": "Riverside Drive, Westlands",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Westlands",
        "latitude": -1.2685,
        "longitude": 36.7951,
        "landmark": "Along Riverside Drive near German Embassy",
        "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 7,
        "units_count": 85,
        "year_built": 2014,
        "description": "State-of-the-art office park with lush landscaped grounds, multi-national embassies, financial tech headquarters, and premium security protocols.",
        "amenities": "Landscaped Gardens, High-Tech Access Control, High-Speed Internet, Ample Parking, On-Site Gourmet Cafes"
    },
    {
        "name": "Vienna Court",
        "building_type": "Eco-Friendly Commercial Complex",
        "address": "State House Crescent, Kilimani / Milimani",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Kilimani",
        "latitude": -1.2863,
        "longitude": 36.8095,
        "landmark": "Off State House Road near Arboretum",
        "image_url": "https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 4,
        "units_count": 60,
        "year_built": 2016,
        "description": "Gold LEED certified eco-friendly corporate offices featuring reflection pools, landscaped courtyard gardens, low solar-gain glass, and energy-neutral design.",
        "amenities": "LEED Gold Certified, Solar Thermal Powered, Reflecting Water Ponds, Fitness Gym, 24/7 Security"
    },
    {
        "name": "Yaya Centre & Towers",
        "building_type": "Mixed-Use Shopping & Residences",
        "address": "Argwings Kodhek Road, Kilimani",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Kilimani",
        "latitude": -1.2936,
        "longitude": 36.7865,
        "landmark": "Corner of Argwings Kodhek & Chania Ave",
        "image_url": "https://images.unsplash.com/photo-1541888946425-d0fbb186f5f8?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 12,
        "units_count": 95,
        "year_built": 2010,
        "description": "Famous Kilimani shopping and residential landmark. Offers fully serviced executive hotel apartments, retail, banking, food courts, and medical facilities under one roof.",
        "amenities": "Supermarket, Swimming Pool, Tennis Court, Backup Power, 24/7 Guarded Entry, High-Speed Elevators"
    },
    {
        "name": "Prism Tower",
        "building_type": "Grade A Commercial Tower",
        "address": "Third Ngong Avenue, Upper Hill",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Upper Hill",
        "latitude": -1.2965,
        "longitude": 36.8130,
        "landmark": "Near NHIF Building & Community Bus Stop",
        "image_url": "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 28,
        "units_count": 130,
        "year_built": 2018,
        "description": "Known as the 'Jewel of Upper Hill', Prism Tower has a captivating jewel-faceted glass façade, Grade A smart offices, and column-free flexible floor plates.",
        "amenities": "Smart Building Management, 5 High-Speed Lifts, 3-Tier Security, 500 Parking Bays, Restaurant & Terrace"
    },
    {
        "name": "The Hub Karen Residences & Suites",
        "building_type": "Retail & Executive Residences",
        "address": "Dagoretti Road, Karen",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Karen",
        "latitude": -1.3204,
        "longitude": 36.7061,
        "landmark": "Near Karen Roundabout & Waterfront",
        "image_url": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 5,
        "units_count": 45,
        "year_built": 2017,
        "description": "Upscale lifestyle residences located adjacent to The Hub Karen with open-air piazza, artificial lake, tranquil Karen greenery, and elite security.",
        "amenities": "Artificial Lake & Walkways, Private Clubhouse, Heated Pool, 24/7 Security, On-Site Gourmet Dining"
    },
    {
        "name": "Garden City Residences",
        "building_type": "Integrated Residential Community",
        "address": "Thika Superhighway, Roysambu / Kasarani",
        "city": "Nairobi",
        "county": "Nairobi",
        "sub_location": "Roysambu",
        "latitude": -1.2335,
        "longitude": 36.8778,
        "landmark": "Next to Garden City Mall on Exit 7 Thika Highway",
        "image_url": "https://images.unsplash.com/photo-1515263487990-61b07816b324?auto=format&fit=crop&w=1200&q=80",
        "total_floors": 11,
        "units_count": 120,
        "year_built": 2018,
        "description": "Modern apartments and townhouses nestled within a 3-acre central park, adjoining Garden City Mall with international schools and IMAX cinema within walking distance.",
        "amenities": "3-Acre Private Park, 2 Swimming Pools, Gym, Solar Hot Water, Dedicated Parking, CCTV Surveillance"
    }
]


def seed_buildings_and_properties():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            admin_user = db.query(User).first()
        owner_id = admin_user.id if admin_user else 1

        print("=== SEEDING REAL BUILDINGS ===")
        building_map = {}
        for b_data in REAL_BUILDINGS:
            existing_b = db.query(Building).filter(Building.name == b_data["name"]).first()
            if not existing_b:
                existing_b = Building(
                    name=b_data["name"],
                    building_type=b_data["building_type"],
                    address=b_data["address"],
                    city=b_data["city"],
                    county=b_data["county"],
                    sub_location=b_data["sub_location"],
                    latitude=b_data["latitude"],
                    longitude=b_data["longitude"],
                    landmark=b_data["landmark"],
                    image_url=b_data["image_url"],
                    total_floors=b_data["total_floors"],
                    units_count=b_data["units_count"],
                    year_built=b_data["year_built"],
                    description=b_data["description"],
                    amenities=b_data["amenities"],
                )
                db.add(existing_b)
                db.commit()
                db.refresh(existing_b)
                print(f"Created building: {existing_b.name} (ID: {existing_b.id})")
            else:
                existing_b.building_type = b_data["building_type"]
                existing_b.address = b_data["address"]
                existing_b.city = b_data["city"]
                existing_b.county = b_data["county"]
                existing_b.sub_location = b_data["sub_location"]
                existing_b.latitude = b_data["latitude"]
                existing_b.longitude = b_data["longitude"]
                existing_b.landmark = b_data["landmark"]
                existing_b.image_url = b_data["image_url"]
                existing_b.total_floors = b_data["total_floors"]
                existing_b.year_built = b_data["year_built"]
                existing_b.description = b_data["description"]
                existing_b.amenities = b_data["amenities"]
                db.add(existing_b)
                db.commit()
                print(f"Updated building: {existing_b.name}")
            building_map[b_data["name"]] = existing_b

        print("\n=== UPDATING & CONNECTING EXISTING PROPERTIES ===")
        existing_props = db.query(Property).all()
        for p in existing_props:
            # Keep the listing's own city. The linked building carries the
            # authoritative address, while changing every city to Nairobi
            # makes city and neighborhood searches misleading.
            p.county = p.county or "Nairobi"
            if not p.sub_location:
                p.sub_location = p.city or "Kilimani"
            
            # Match to nearest building
            if "kilimani" in (p.sub_location or "").lower():
                b = building_map.get("FCB Mihrab") or building_map.get("Yaya Centre & Towers")
                p.building_id = b.id if b else None
                p.latitude = -1.2921
                p.longitude = 36.7937
                p.landmark = "Near Yaya Centre & Lenana Road"
            elif "westlands" in (p.sub_location or "").lower():
                b = building_map.get("The Mirage") or building_map.get("Le'Mac Towers")
                p.building_id = b.id if b else None
                p.latitude = -1.2678
                p.longitude = 36.8078
                p.landmark = "Chiromo Road, Westlands"
            elif "upper hill" in (p.sub_location or "").lower():
                b = building_map.get("Britam Tower")
                p.building_id = b.id if b else None
                p.latitude = -1.2996
                p.longitude = 36.8166
                p.landmark = "Hospital Road, Upper Hill"
            elif "karen" in (p.sub_location or "").lower():
                b = building_map.get("The Hub Karen Residences & Suites")
                p.building_id = b.id if b else None
                p.latitude = -1.3204
                p.longitude = 36.7061
                p.landmark = "Dagoretti Road, Karen"
            elif "ruaka" in (p.sub_location or "").lower():
                b = building_map.get("Two Rivers Riverbank Residences")
                p.building_id = b.id if b else None
                p.latitude = -1.2155
                p.longitude = 36.7944
                p.landmark = "Limuru Road, Two Rivers Precinct"
            else:
                p.latitude = -1.2863
                p.longitude = 36.8095
                p.landmark = "State House Crescent, Nairobi"

            # Set realistic property types
            if p.property_type == "Residential":
                p.property_type = "Apartment"

            db.add(p)
        db.commit()
        print(f"Updated {len(existing_props)} existing properties with coordinates and Nairobi county.")

        print("\n=== CREATING PREMIER PROPERTIES TIED TO BUILDINGS ===")
        NEW_BUILDING_PROPERTIES = [
            {
                "name": "Britam Tower Executive Corporate Penthouse Suite",
                "building_name": "Britam Tower",
                "property_type": "Commercial",
                "purpose": "rent",
                "price": "350000",
                "price_label": "KSh 350,000 / month",
                "deposit": "KSh 700,000",
                "lease_term": "24 months",
                "bedrooms": 0,
                "bathrooms": 4,
                "area": "450 sqm",
                "units_count": 1,
                "status": "active",
                "description": "Spectacular Grade A commercial office suite on the 28th floor of Britam Tower. Offers unmatched 360-degree panoramic views of Nairobi skyline and Nairobi National Park, high-speed fibre, dedicated server room, and 6 reserved executive parking bays.",
                "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
                "amenities": "High-Speed Elevators, 24/7 Security, Backup Generator, 6 Parking Bays, CCTV, Central AC"
            },
            {
                "name": "Le'Mac Towers Sky Horizon 3-Bed Luxury Apartment",
                "building_name": "Le'Mac Towers",
                "property_type": "Apartment",
                "purpose": "rent",
                "price": "220000",
                "price_label": "KSh 220,000 / month",
                "deposit": "KSh 440,000",
                "lease_term": "12 months",
                "bedrooms": 3,
                "bathrooms": 3,
                "area": "210 sqm",
                "units_count": 1,
                "status": "active",
                "description": "Ultra-luxury modern apartment on the 18th floor of Le'Mac Towers in Westlands. Comes with floor-to-ceiling soundproof acoustic glass windows, bespoke Italian kitchen fittings, master jacuzzi, access to the 24th floor sky glass walkway, rooftop heated pool, and sky lounge.",
                "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
                "amenities": "Rooftop Heated Pool, Sky Walkway, Gym & Spa, 2 Reserved Parking, Concierge, Backup Power"
            },
            {
                "name": "Riverbank Residences Two Rivers 2-Bedroom Designer Apartment",
                "building_name": "Two Rivers Riverbank Residences",
                "property_type": "Apartment",
                "purpose": "buy",
                "price": "18500000",
                "price_label": "KSh 18,500,000",
                "deposit": "KSh 1,850,000",
                "lease_term": "Freehold / 99-yr lease",
                "bedrooms": 2,
                "bathrooms": 2,
                "area": "135 sqm",
                "units_count": 1,
                "status": "active",
                "description": "Turnkey designer 2-bedroom residence within the Two Rivers gated community. High rental yield asset for investors (projected 9.5% gross yield). Direct access to Two Rivers Mall, 7-acre nature park, private clubhouse, and heated Olympic pool.",
                "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
                "amenities": "Clubhouse, Olympic Pool, 7-Acre Park, Mall Access, Smart Home Locks, 24/7 Security"
            },
            {
                "name": "FCB Mihrab Prime Corporate Suite",
                "building_name": "FCB Mihrab",
                "property_type": "Commercial",
                "purpose": "invest",
                "price": "42000000",
                "price_label": "KSh 42,000,000",
                "deposit": "KSh 4,200,000",
                "lease_term": "Commercial Title",
                "bedrooms": 0,
                "bathrooms": 2,
                "area": "280 sqm",
                "units_count": 1,
                "status": "active",
                "description": "High-yield commercial office suite on the 11th floor of FCB Mihrab on Lenana Road, Kilimani. Currently leased to an international financial advisory firm with guaranteed 8.2% annual net yield.",
                "image_url": "https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=1200&q=80",
                "amenities": "LEED Certified, High-Speed Lifts, 4 Parking Spaces, Cafeteria, Prayer Rooms, Backup Generator"
            },
            {
                "name": "The Hub Karen Forest Garden Villa",
                "building_name": "The Hub Karen Residences & Suites",
                "property_type": "Villa",
                "purpose": "buy",
                "price": "88000000",
                "price_label": "KSh 88,000,000",
                "deposit": "KSh 8,800,000",
                "lease_term": "Freehold",
                "bedrooms": 4,
                "bathrooms": 4,
                "area": "420 sqm",
                "units_count": 1,
                "status": "active",
                "description": "Exclusive 4-bedroom all-ensuite luxury colonial-modern fusion villa near The Hub Karen. Set on half an acre of manicured English gardens, with private plunge pool, staff quarters for 2, solar inverter system, and electric fencing.",
                "image_url": "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=1200&q=80",
                "amenities": "Half-Acre Garden, Private Pool, Staff Quarters, Solar Power, Electric Fence, Borehole"
            },
            {
                "name": "The Mirage Chiromo High-Exposure Office",
                "building_name": "The Mirage",
                "property_type": "Commercial",
                "purpose": "rent",
                "price": "180000",
                "price_label": "KSh 180,000 / month",
                "deposit": "KSh 360,000",
                "lease_term": "24 months",
                "bedrooms": 0,
                "bathrooms": 2,
                "area": "190 sqm",
                "units_count": 1,
                "status": "active",
                "description": "Premium corner-unit corporate office in Tower 2 of The Mirage, Chiromo Road, Westlands. Offers prominent street visibility, direct access to the Westlands expressway exit, and high client foot traffic.",
                "image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
                "amenities": "Expressway Access, 3 Lifts, Backup Generator, 3 Parking Slots, Fiber Internet"
            },
            {
                "name": "Garden City 3-Bed Family Park Apartment",
                "building_name": "Garden City Residences",
                "property_type": "Apartment",
                "purpose": "buy",
                "price": "24500000",
                "price_label": "KSh 24,500,000",
                "deposit": "KSh 2,450,000",
                "lease_term": "99-yr lease",
                "bedrooms": 3,
                "bathrooms": 3,
                "area": "170 sqm",
                "units_count": 1,
                "status": "active",
                "description": "Spacious contemporary 3-bedroom apartment facing the Garden City 3-acre park. Ideal for modern families looking for security, walking proximity to shopping, top international schools, and sports club.",
                "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
                "amenities": "3-Acre Park, Mall Proximity, 2 Swimming Pools, Gym, Solar Heating, 24/7 Guards"
            }
        ]

        for item in NEW_BUILDING_PROPERTIES:
            b = building_map.get(item["building_name"])
            existing = db.query(Property).filter(Property.name == item["name"]).first()
            if not existing:
                prop = Property(
                    owner_id=owner_id,
                    name=item["name"],
                    building_id=b.id if b else None,
                    property_type=item["property_type"],
                    purpose=item["purpose"],
                    price=item["price"],
                    price_label=item["price_label"],
                    deposit=item.get("deposit"),
                    lease_term=item.get("lease_term"),
                    bedrooms=item.get("bedrooms"),
                    bathrooms=item.get("bathrooms"),
                    area=item.get("area"),
                    units_count=item.get("units_count", 1),
                    status=item["status"],
                    description=item["description"],
                    image_url=item["image_url"],
                    amenities=item["amenities"],
                    address=b.address if b else "Nairobi, Kenya",
                    city="Nairobi",
                    county="Nairobi",
                    sub_location=b.sub_location if b else "Westlands",
                    country="Kenya",
                    latitude=b.latitude if b else -1.2863,
                    longitude=b.longitude if b else 36.8172,
                    landmark=b.landmark if b else "Nairobi City",
                    is_verified=True,
                    allow_direct_contact=True
                )
                db.add(prop)
                db.commit()
                print(f"Created listing: {item['name']} linked to {item['building_name']}")
            else:
                existing.building_id = b.id if b else None
                existing.latitude = b.latitude if b else existing.latitude
                existing.longitude = b.longitude if b else existing.longitude
                existing.landmark = b.landmark if b else existing.landmark
                existing.city = existing.city or b.city if b else existing.city
                existing.county = existing.county or (b.county if b else "Nairobi")
                existing.sub_location = b.sub_location if b else existing.sub_location
                db.add(existing)
                db.commit()
                print(f"Updated listing: {item['name']}")

        print("\n=== SUCCESS: All real buildings and real properties seeded! ===")
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error seeding: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_buildings_and_properties()
