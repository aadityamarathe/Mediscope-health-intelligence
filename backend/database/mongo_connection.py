from pymongo import MongoClient

from ..config import DATABASE_NAME, MONGODB_URI
_client = None
_db = None


def get_db():
    global _client, _db

    if _db is None:
        if not MONGODB_URI:
            raise ValueError("MONGODB_URI is not set.")

        if _client is None:
            _client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            _client.admin.command("ping")

        _db = _client[DATABASE_NAME]

    return _db
