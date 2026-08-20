from backend.database.mongo_connection import get_db
from backend.pipeline.processor import process_articles
from backend.crawler.spiders.disease_api_spider import DiseaseAPISpider
import time
import json

db = get_db()

# Capture before state
old_outbreaks_before = db["outbreaks"].count_documents({})
v2_outbreaks_before = db["outbreaks_v2"].count_documents({})
v2_records_before = {f"{r['disease']}_{r['country']}": r for r in db["outbreaks_v2"].find({})}

print("--- BEFORE RUN ---")
print(f"outbreaks count: {old_outbreaks_before}")
print(f"outbreaks_v2 count: {v2_outbreaks_before}")

# 1. Run processor
print("\n--- RUNNING processor.py ---")
process_articles()

# 2. Run disease api spider
print("\n--- RUNNING disease_api_spider.py ---")
spider = DiseaseAPISpider()
spider.run()

# Capture after state
old_outbreaks_after = db["outbreaks"].count_documents({})
v2_outbreaks_after = db["outbreaks_v2"].count_documents({})
v2_records_after = {f"{r['disease']}_{r['country']}": r for r in db["outbreaks_v2"].find({})}

print("\n--- AFTER RUN ---")
print(f"outbreaks count: {old_outbreaks_after}")
print(f"outbreaks_v2 count: {v2_outbreaks_after}")

if old_outbreaks_after > old_outbreaks_before:
    print(f"WARNING: outbreaks collection grew by {old_outbreaks_after - old_outbreaks_before} records!")
else:
    print("SUCCESS: No new records in old outbreaks collection.")

# Analyze changes
records_inserted = v2_outbreaks_after - v2_outbreaks_before
records_updated = 0
records_skipped = 0
improved_ranks = 0

def get_rank(st):
    st = str(st).lower()
    if "disease.sh" in st or "disease_sh" in st: return 4
    if "gho" in st: return 3
    if "extracted" in st: return 2
    return 1

for key, after_rec in v2_records_after.items():
    if key not in v2_records_before:
        # Inserted
        continue
    
    before_rec = v2_records_before[key]
    
    b_cc = before_rec.get("case_count")
    a_cc = after_rec.get("case_count")
    b_src = before_rec.get("case_count_source")
    a_src = after_rec.get("case_count_source")
    b_date = before_rec.get("date")
    a_date = after_rec.get("date")
    
    if b_cc != a_cc or b_src != a_src or b_date != a_date:
        records_updated += 1
        if get_rank(a_src) > get_rank(b_src):
            improved_ranks += 1
            print(f"Improved rank for {key}: {b_src} -> {a_src}")
    else:
        records_skipped += 1

print(f"\nRecords Inserted: {records_inserted}")
print(f"Records Updated: {records_updated}")
print(f"Records Skipped: {records_skipped}")
print(f"Source Ranks Improved: {improved_ranks}")

print("\n--- Final Disease Distribution ---")
for disease_name in sorted(db["outbreaks_v2"].distinct("disease")):
    count = db["outbreaks_v2"].count_documents({"disease": disease_name})
    print(disease_name, count)

# Write output to json so we can format report
report = {
    "old_outbreaks_diff": old_outbreaks_after - old_outbreaks_before,
    "records_inserted": records_inserted,
    "records_updated": records_updated,
    "records_skipped": records_skipped,
    "improved_ranks": improved_ranks,
    "final_count": v2_outbreaks_after
}
with open("migration_stats.json", "w") as f:
    json.dump(report, f)
