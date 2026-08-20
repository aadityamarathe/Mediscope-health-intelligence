from datetime import datetime, timezone
from uuid import uuid4

from .mongo_connection import get_db


COLLECTIONS = [
    "raw_articles",
    "processed_articles",
    "diseases",
    "outbreaks",
    "subscribers",
]


def create_collections():
    db = get_db()
    existing = set(db.list_collection_names())

    for name in COLLECTIONS:
        if name not in existing:
            db.create_collection(name)

    return db


def create_indexes():
    db = create_collections()

    db["raw_articles"].create_index("url", unique=True, name="raw_articles_url_unique")
    db["raw_articles"].create_index("crawled_at", name="raw_articles_crawled_at")

    db["processed_articles"].create_index(
        "url",
        unique=True,
        name="processed_articles_url_unique",
    )
    db["processed_articles"].create_index(
        "diseases_found",
        name="processed_articles_diseases_found",
    )
    db["processed_articles"].create_index(
        "locations_found",
        name="processed_articles_locations_found",
    )
    db["processed_articles"].create_index(
        "is_relevant",
        name="processed_articles_is_relevant",
    )

    db["diseases"].create_index("name", unique=True, name="diseases_name_unique")

    db["outbreaks"].create_index("disease", name="outbreaks_disease")
    db["outbreaks"].create_index("country", name="outbreaks_country")
    db["outbreaks"].create_index("date", name="outbreaks_date")
    db["outbreaks"].create_index([("location", "2dsphere")], name="outbreaks_location_2dsphere")

    try:
        db["subscribers"].drop_index("subscribers_email_unique")
    except Exception:
        pass
        
    # One-time migration: Clean up legacy invalid subscriptions if any exist
    if db["subscribers"].count_documents({"region": ""}, limit=1) > 0:
        db["subscribers"].delete_many({"region": ""})

    db["subscribers"].create_index([("email", 1), ("region", 1)], unique=True, name="subscribers_email_region_unique")
    db["subscribers"].create_index("region", name="subscribers_region")

    return db


def initialize_database():
    return create_indexes()


def test_database_connection():
    db = initialize_database()
    sample_url = f"https://example.com/raw-article/{uuid4()}"
    sample_document = {
        "url": sample_url,
        "title": "Connection test",
        "crawled_at": datetime.now(timezone.utc),
    }

    insert_result = db["raw_articles"].insert_one(sample_document)
    fetched_document = db["raw_articles"].find_one({"_id": insert_result.inserted_id})

    print(f"Database setup successful. Sample raw article fetched: {fetched_document is not None}")
    return fetched_document
