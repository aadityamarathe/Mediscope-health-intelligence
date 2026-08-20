from backend.database.mongo_connection import get_db

db = get_db()
v2 = db["outbreaks_v2"]

total_records = v2.count_documents({})
missing_case_count = v2.count_documents({"case_count": None})

print(f"outbreaks_v2 record count: {total_records}")
print(f"outbreaks_v2 missing case_count count: {missing_case_count}")

print("outbreaks_v2 disease distribution:")
pipeline = [
    {"$group": {"_id": "$disease", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
for doc in v2.aggregate(pipeline):
    print(f"  {doc['_id']}: {doc['count']}")
