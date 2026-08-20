from backend.database.mongo_connection import get_db

db = get_db()
collections = db.list_collection_names()
print(f"Collections: {collections}")

for coll in collections:
    count = db[coll].count_documents({})
    print(f"{coll}: {count} documents")
    if count > 0:
        sample = db[coll].find_one()
        print(f"Sample keys from {coll}: {list(sample.keys())}")
        
# Check for null coordinates in outbreaks_v2
null_coords = db["outbreaks_v2"].count_documents({"$or": [{"lat": None}, {"lng": None}]})
print(f"Null coordinates in outbreaks_v2: {null_coords}")

