"""Seed script for the Zameen Real Estate API.

Usage:
    python -m app.seed
"""
import asyncio
import uuid
import json

from app.db.base import AsyncSessionLocal, Base, engine
from app.models.user import User
from app.models.property import City, Area, Property, PropertyImage
from app.core.security import get_password_hash
from sqlalchemy import select


# Pakistani cities with popular areas
CITIES = {
    "Karachi": {
        "province": "Sindh",
        "areas": ["DHA Phase 6", "Clifton", "Gulshan-e-Iqbal", "Bahadurabad", "Gulistan-e-Johar",
                  "North Nazimabad", "Shah Faisal Colony", "Korangi", "Malir", "PECHS", "F.B. Area",
                  "Saddar", "Nazimabad", "Landhi", "Surjani Town", "DHA Phase 8", "Defence View", "KDA Scheme 1",
                  "Askari 4", "Model Colony"],
    },
    "Lahore": {
        "province": "Punjab",
        "areas": ["DHA Phase 5", "Bahria Town", "Gulberg", "Model Town", "Johar Town", "Wapda Town",
                  "DHA Phase 6", "Cantt", "Askari 10", "Faisal Town", "Iqbal Town", "Samnabad",
                  "Garden Town", "Township", "Valencia Town", "Lake City", "Eden Housing", "Shahdara",
                  "Mughalpura", "Allama Iqbal Town"],
    },
    "Islamabad": {
        "province": "ICT",
        "areas": ["F-8", "F-7", "G-9", "DHA Phase 2", "Bahria Enclave", "E-11", "G-11", "I-8",
                  "G-13", "F-11", "DHA Phase 1", "Gulberg Greens", "Park View City", "Capital Smart City",
                  "Blue World City", "Lakeside", "Bani Gala", "NARC", "Top City", "Airport Enclave"],
    },
    "Rawalpindi": {
        "province": "Punjab",
        "areas": ["Bahria Town Phase 4", "DHA Phase 2", "Satellite Town", "Chaklala Scheme 3", "Gulraiz Housing",
                  "Askari 11", "Adiala Road", "Saddar", "Westridge", "Pirwadhai", "Sixth Road", "Bhabra Bazar",
                  "Airport Road", "New City Housing", "Cantt", "Race Course", "Jinnah Colony", "Khyaban-e-Sir Syed",
                  "Sadiqabad", "Dhoke Hassu"],
    },
    "Faisalabad": {
        "province": "Punjab",
        "areas": ["D Ground", "Peoples Colony", "Madina Town", "Jaranwala Road", "Sargodha Road",
                  "Canal Road", "Sahiwal Road", "Gulberg", "Railway Road", "Satiana Road", "Samundri Road",
                  "Kohinoor City", "Askari 9", "Faisal Town", "Millat Town", "Jinnah Colony", "Raza Abad",
                  "Bismillah Housing", "State Life Road", "Karkhana Bazar"],
    },
    "Peshawar": {
        "province": "KPK",
        "areas": ["Hayatabad Phase 6", "University Town", "DHA Phase 2", "Regi Model Town", "Gulbahar",
                  "Kohat Road", "Ring Road", "Saddar", "Charsadda Road", "Pishtakhara", "Bagh-e-Naran",
                  "Haryana", "Shah Dhand", "Bara Road", "Hashtnagri", "Qayyumabad", "Cantt", "Tehkal Bala",
                  "Muhammadi Housing", "Warsak Road"],
    },
    "Quetta": {
        "province": "Balochistan",
        "areas": ["Model Town", "Jinnah Town", "Airport Road", "Sariab Road", "Brewery Road", "Kechi Baig",
                  "Samungli Road", "Chiltan Housing", "Nawab Town", "Spinny Road", "Patel Bagh", "Killi Gul Muhammad",
                  "Sheikh Manda", "Shahbaz Town", "Cantt", "Gawalmandi", "City", "Kirani Road", "Sabzal Road",
                  "Garden Colony"],
    },
    "Multan": {
        "province": "Punjab",
        "areas": ["Bosan Road", "Gulgasht Colony", "Shah Rukn-e-Alam Colony", "Cantt", "Shah Shamas Colony",
                  "DHA Multan", "Model Town", "Garden Town", "Chowk Kumharanwala", "Shahzad Colony",
                  "Basti Malook", "Jalilabad", "Qadirpur Raan", "Sher Shah", "Khanewal Road", "Vehari Road",
                  "Lodhran Road", "Abdali Road", "Sultan Colony", "New Multan City"],
    },
    "Hyderabad": {
        "province": "Sindh",
        "areas": ["Latifabad", "Qasimabad", "Auto Bhan Road", "Saddar", "Gulistan-e-Sarmast", "Hirabad",
                  "Market Tower", "City", "Unit 1-9", "Shah Latif Town", "Semi Park", "Bhatti Colony",
                  "Hyderabad Bypass", "Wadhu Wah", "Kohsar", "Model Town", "Phase 1 Latifabad",
                  "Hussainabad", "Bhittai Abad", "Al-Madina Housing"],
    },
    "Gujranwala": {
        "province": "Punjab",
        "areas": ["Wapda Town", "Cantt", "Satellite Town", "Model Town", "Rasoolpura", "Sialkot Road",
                  "G.T. Road", "Nowshera Road", "Ghakhar Mandi", "Eminabad Road", "Shahbaz Pura", "Madina Town",
                  "Dhayali Road", "Gulshan-e-Iqbal Town", "Jinnah Park", "Marala Road", "Saidpur", "Islam Pura",
                  "Faisalabad Road", "Hafizabad Road"],
    },
}

# Sample property descriptions
PROPERTY_SAMPLES = [
    {
        "title": "Modern 5 Marla House for Sale",
        "type": "HOUSE",
        "status": "FOR_SALE",
        "price": 18500000,
        "bedrooms": 5,
        "bathrooms": 4,
        "kitchens": 1,
        "area_size": 1250,
        "furnished": True,
        "description": "Beautiful modern house with spacious rooms, a lovely lawn and secure gated community. "
                       "Close to schools, mosques and main boulevard. Perfect for a growing family.",
        "amenities": ["Lawn", "Parking", "Security", "Central AC", "UPS"],
        "images": [
            "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=1200",
            "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=1200",
        ],
    },
    {
        "title": "Luxury 10 Marla Double Story House",
        "type": "HOUSE",
        "status": "FOR_SALE",
        "price": 42000000,
        "bedrooms": 7,
        "bathrooms": 6,
        "kitchens": 2,
        "area_size": 2500,
        "furnished": True,
        "description": "Premium double storey house with high-end finishes, marble floors, designer kitchen "
                       "and a rooftop terrace. Ideally located in a posh neighbourhood with wide roads.",
        "amenities": ["Elevator", "Terrace", "Marble Flooring", "Attached Bathrooms", "Kitchen Cabinets", "Parking"],
        "images": [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200",
        ],
    },
    {
        "title": "Spacious 3 Bed Apartment for Rent",
        "type": "APARTMENT",
        "status": "FOR_RENT",
        "price": 85000,
        "bedrooms": 3,
        "bathrooms": 3,
        "kitchens": 1,
        "area_size": 1450,
        "furnished": False,
        "description": "Bright and airy apartment on the 8th floor with panoramic city views. Building offers "
                       "24/7 security, backup power and covered parking. Ideal for professionals.",
        "amenities": ["Lift", "Security", "Backup Power", "Parking"],
        "images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1200",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1200",
        ],
    },
    {
        "title": "Commercial Plot for Sale",
        "type": "PLOT",
        "status": "FOR_SALE",
        "price": 9500000,
        "bedrooms": None,
        "bathrooms": None,
        "kitchens": None,
        "area_size": 250,
        "furnished": False,
        "description": "Corner commercial plot on a main boulevard with excellent visibility and high footfall. "
                       "Perfect for a bank, restaurant or office building. Clear title and ready to build.",
        "amenities": ["Corner Plot", "Main Road", "Clear Title"],
        "images": [
            "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200",
        ],
    },
    {
        "title": "Brand New Villa in Gated Community",
        "type": "VILLA",
        "status": "FOR_SALE",
        "price": 78000000,
        "bedrooms": 6,
        "bathrooms": 7,
        "kitchens": 2,
        "area_size": 4500,
        "furnished": True,
        "description": "Stunning Mediterranean-style villa with private pool, landscaped garden and servant quarters. "
                       "World-class community amenities including clubhouse, gym and parks.",
        "amenities": ["Private Pool", "Garden", "Servant Quarters", "Clubhouse Access", "Gym", "Security"],
        "images": [
            "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200",
            "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=1200",
        ],
    },
    {
        "title": "Upper Portion for Rent",
        "type": "APARTMENT",
        "status": "FOR_RENT",
        "price": 45000,
        "bedrooms": 2,
        "bathrooms": 2,
        "kitchens": 1,
        "area_size": 900,
        "furnished": False,
        "description": "Newly constructed upper portion with separate entrance, tiled floors and good light. "
                       "Quiet family neighbourhood, 5 minutes from main market.",
        "amenities": ["Separate Entrance", "Parking", "Tiled Floors"],
        "images": [
            "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200",
            "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=1200",
        ],
    },
]


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("_", "-").replace("&", "and")


async def seed() -> None:
    # Ensure tables exist (dev convenience; production uses migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # --- Admin user ---
        result = await db.execute(select(User).where(User.email == "admin@zameen.com"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@zameen.com",
                password=get_password_hash("admin123"),
                name="Zameen Admin",
                role="ADMIN",
                is_active=True,
            )
            db.add(admin)
            await db.flush()
            print("Created admin user: admin@zameen.com / admin123")

        # --- Demo agent ---
        result = await db.execute(select(User).where(User.email == "agent@zameen.com"))
        agent = result.scalar_one_or_none()
        if not agent:
            agent = User(
                id=str(uuid.uuid4()),
                email="agent@zameen.com",
                password=get_password_hash("agent123"),
                name="Demo Agent",
                role="AGENT",
                is_active=True,
            )
            db.add(agent)
            await db.flush()
            print("Created demo agent: agent@zameen.com / agent123")

        # --- Demo buyer (for testing the mobile/web app) ---
        result = await db.execute(select(User).where(User.email == "buyer@zameen.com"))
        buyer = result.scalar_one_or_none()
        if not buyer:
            buyer = User(
                id=str(uuid.uuid4()),
                email="buyer@zameen.com",
                password=get_password_hash("buyer123"),
                name="Test Buyer",
                phone="+92 300 0000000",
                role="BUYER",
                is_active=True,
            )
            db.add(buyer)
            await db.flush()
            print("Created demo buyer: buyer@zameen.com / buyer123")

        # --- Cities & areas ---
        city_map = {}
        area_map = {}
        for city_name, data in CITIES.items():
            result = await db.execute(select(City).where(City.name == city_name))
            city = result.scalar_one_or_none()
            if not city:
                city = City(
                    id=str(uuid.uuid4()),
                    name=city_name,
                    slug=slugify(city_name),
                    province=data["province"],
                    featured=city_name in ("Karachi", "Lahore", "Islamabad"),
                )
                db.add(city)
                await db.flush()
                print(f"Created city: {city_name}")
            city_map[city_name] = city

            for area_name in data["areas"]:
                result = await db.execute(
                    select(Area).where(Area.city_id == city.id, Area.name == area_name)
                )
                area = result.scalar_one_or_none()
                if not area:
                    area = Area(
                        id=str(uuid.uuid4()),
                        name=area_name,
                        slug=slugify(area_name),
                        city_id=city.id,
                    )
                    db.add(area)
                    await db.flush()
                area_map[area_name] = area

        # --- Sample properties ---
        result = await db.execute(select(Property))
        existing_count = len(list(result.scalars().all()))
        if existing_count == 0:
            for i, sample in enumerate(PROPERTY_SAMPLES):
                city_name = list(CITIES.keys())[i % len(CITIES)]
                city = city_map[city_name]
                city_areas = CITIES[city_name]["areas"]
                area_name = city_areas[i % len(city_areas)]
                area = area_map.get(area_name)
                if not area:
                    continue

                prop = Property(
                    id=str(uuid.uuid4()),
                    title=sample["title"],
                    slug=slugify(sample["title"]) + "-" + str(uuid.uuid4())[:8],
                    description=sample["description"],
                    type=sample["type"],
                    status=sample["status"],
                    listing_status="APPROVED",
                    city_id=city.id,
                    area_id=area.id,
                    address=f"{area.name}, {city.name}",
                    price=sample["price"],
                    bedrooms=sample["bedrooms"],
                    bathrooms=sample["bathrooms"],
                    kitchens=sample["kitchens"],
                    area_size=sample["area_size"],
                    amenities=json.dumps(sample["amenities"]),
                    furnished=sample["furnished"],
                    owner_id=agent.id,
                    contact_phone="+92 300 1234567",
                    contact_email="agent@zameen.com",
                    views=0,
                    featured=i % 2 == 0,
                )
                db.add(prop)
                await db.flush()

                for j, img_url in enumerate(sample["images"]):
                    db.add(PropertyImage(
                        id=str(uuid.uuid4()),
                        property_id=prop.id,
                        url=img_url,
                        caption=sample["title"],
                        is_primary=j == 0,
                        order=j,
                    ))
                print(f"Created property: {sample['title']} ({city_name})")

        await db.commit()
        print("\nSeed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
