from backend.database.mongo_connection import get_db
import random

db = get_db()

# Get pairs from outbreaks_v2 that have at least 2 records in outbreaks
pipeline = [
    {"$group": {"_id": {"disease": "$disease", "country": "$country"}, "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}},
    {"$sample": {"size": 20}}
]
pairs_in_old = list(db["outbreaks"].aggregate(pipeline))

print(f"Found {len(pairs_in_old)} pairs with multiple records in old collection.")

for idx, pair_data in enumerate(pairs_in_old, 1):
    disease = pair_data["_id"]["disease"]
    country = pair_data["_id"]["country"]
    
    # Current survivor in v2
    v2_record = db["outbreaks_v2"].find_one({"disease": disease, "country": country})
    if not v2_record:
        continue
        
    print(f"\n--- [{idx}] {disease.upper()} in {country.upper()} ---")
    print("V2 SURVIVOR:")
    print(f"  Date: {v2_record.get('date')}")
    print(f"  Cases: {v2_record.get('case_count')} (Source: {v2_record.get('case_count_source')})")
    print(f"  Source: {v2_record.get('source')} | URL: {v2_record.get('source_url')}")
    
    # Old records
    old_records = list(db["outbreaks"].find({"disease": disease, "country": country}))
    print(f"OLD RECORDS ({len(old_records)} found):")
    for r_idx, old_r in enumerate(old_records, 1):
        print(f"  [{r_idx}] Date: {old_r.get('date')}")
        print(f"      Cases: {old_r.get('case_count')} (Source: {old_r.get('case_count_source')})")
        print(f"      Source: {old_r.get('source')} | URL: {old_r.get('source_url')}")
