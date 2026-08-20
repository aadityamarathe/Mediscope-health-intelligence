from backend.config import MONGODB_URI
from pymongo import MongoClient

client = MongoClient(MONGODB_URI)
db = client['mediscope']

# Check outbreak creation by date
pipeline = [
    {"$group": {
        "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
        "count": {"$sum": 1}
    }},
    {"$sort": {"_id": -1}},
    {"$limit": 7}
]

print("=== Outbreaks created by date ===")
for r in db.outbreaks.aggregate(pipeline):
    print(r)

# Check for duplicates: same disease+country+date
print("\n=== Checking for duplicate disease+country combos ===")
pipeline2 = [
    {"$group": {
        "_id": {"disease": "$disease", "country": "$country"},
        "count": {"$sum": 1}
    }},
    {"$match": {"count": {"$gt": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]
dupes = list(db.outbreaks.aggregate(pipeline2))
if dupes:
    for r in dupes:
        print(r)
else:
    print("No duplicates found.")

print(f"\nTotal outbreaks: {db.outbreaks.count_documents({})}")