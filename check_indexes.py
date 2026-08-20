from backend.database.mongo_connection import get_db

db = get_db()
collections = db.list_collection_names()
for coll in collections:
    indexes = db[coll].index_information()
    print(f"Indexes for {coll}:")
    for name, info in indexes.items():
        print(f"  {name}: {info['key']}")
