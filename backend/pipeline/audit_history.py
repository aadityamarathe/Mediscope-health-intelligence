from backend.database.mongo_connection import get_db
import collections
import datetime

db = get_db()
outbreaks = list(db["outbreaks"].find({}))

# Phase 2: verify counts
groups = collections.defaultdict(list)
for o in outbreaks:
    groups[(o.get("disease", "unknown"), o.get("country", "unknown"))].append(o)

categories = {
    "original_preserved": 0,
    "true_duplicate": 0,
    "pipeline_artifact": 0,
    "historical_snapshot": 0,
    "unknown": 0
}

for (disease, country), records in groups.items():
    records.sort(key=lambda x: x.get("date") or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    seen_source_urls = {}
    seen_case_counts = set()
    
    for i, r in enumerate(records):
        source_url = r.get("source_url", "")
        case_count = r.get("case_count")
        category = ""
        
        if source_url and source_url in seen_source_urls:
            first_r = seen_source_urls[source_url]
            if case_count == first_r.get("case_count"):
                category = "true_duplicate"
            else:
                category = "pipeline_artifact"
        else:
            if source_url:
                seen_source_urls[source_url] = r
            if i == 0:
                category = "original_preserved"
            else:
                if case_count not in seen_case_counts and case_count is not None:
                    category = "historical_snapshot"
                elif r.get("source") == "disease.sh":
                    if case_count in seen_case_counts:
                        category = "true_duplicate"
                    else:
                        category = "historical_snapshot"
                else:
                    category = "unknown"
        
        seen_case_counts.add(case_count)
        if category:
            categories[category] += 1
        else:
            categories["unknown"] += 1

print("--- Phase 2 Counts ---")
for k, v in categories.items():
    print(f"{k}: {v}")

print("\n--- Phase 3 Historical Data Reality Check ---")

targets = ["cholera", "malaria", "influenza", "tuberculosis", "dengue", "monkeypox"]

for target in targets:
    # Find a country with multiple records for this disease
    country_groups = [(c, recs) for (d, c), recs in groups.items() if d == target and len(recs) > 3]
    if country_groups:
        country_groups.sort(key=lambda x: len(x[1]), reverse=True) # Pick the one with the most records
        country, recs = country_groups[0]
        
        print(f"Disease: {target.capitalize()}")
        print(f"Country: {country}\n")
        
        for r in recs[:10]: # Print first 10
            date_str = r.get("date").strftime("%Y-%m-%d") if r.get("date") else "Unknown"
            print(f"{date_str} | {r.get('case_count')} | {r.get('source_url')}")
        print()
