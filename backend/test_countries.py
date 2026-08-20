from backend.database.mongo_connection import get_db
import json

db = get_db()
pipeline = [
    {"$group": {"_id": "$country", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 20}
]
results = list(db["outbreaks_v2"].aggregate(pipeline))

print("Top 20 Countries Aggregation:")
for idx, doc in enumerate(results, 1):
    print(f"{idx}. {doc['_id']}: {doc['count']}")
