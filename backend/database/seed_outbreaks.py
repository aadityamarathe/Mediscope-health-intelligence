from datetime import datetime
from .mongo_connection import get_db


def seed_outbreaks():
    db = get_db()

    # Clear old data
    db.outbreaks.delete_many({})
    print("Old outbreaks deleted")

    outbreaks = [
        {
            "disease": "Dengue",
            "country": "India",
            "region": "India",
            "case_count": 120000,
            "date": datetime.utcnow(),
            "lat": 20.5937,
            "lng": 78.9629,
            "source": "WHO",
            "source_url": "https://www.who.int"
        },
        {
            "disease": "Cholera",
            "country": "Yemen",
            "region": "Yemen",
            "case_count": 50000,
            "date": datetime.utcnow(),
            "lat": 15.5527,
            "lng": 48.5164,
            "source": "WHO",
            "source_url": "https://www.who.int"
        },
        {
            "disease": "Malaria",
            "country": "Nigeria",
            "region": "Nigeria",
            "case_count": 200000,
            "date": datetime.utcnow(),
            "lat": 9.0820,
            "lng": 8.6753,
            "source": "WHO",
            "source_url": "https://www.who.int"
        },
        {
            "disease": "Tuberculosis",
            "country": "South Africa",
            "region": "South Africa",
            "case_count": 80000,
            "date": datetime.utcnow(),
            "lat": -30.5595,
            "lng": 22.9375,
            "source": "WHO",
            "source_url": "https://www.who.int"
        },
        {
            "disease": "Measles",
            "country": "Pakistan",
            "region": "Pakistan",
            "case_count": 30000,
            "date": datetime.utcnow(),
            "lat": 30.3753,
            "lng": 69.3451,
            "source": "WHO",
            "source_url": "https://www.who.int"
        },
        {
            "disease": "Monkeypox",
            "country": "DR Congo",
            "region": "DR Congo",
            "case_count": 10000,
            "date": datetime.utcnow(),
            "lat": -4.0383,
            "lng": 21.7587,
            "source": "WHO",
            "source_url": "https://www.who.int"
        }
    ]

    db.outbreaks.insert_many(outbreaks)
    print("New outbreaks inserted successfully")


if __name__ == "__main__":
    seed_outbreaks()
