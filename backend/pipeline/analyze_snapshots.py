from backend.database.mongo_connection import get_db
import collections
import datetime

db = get_db()
outbreaks = list(db["outbreaks"].find({}))

groups = collections.defaultdict(list)
for o in outbreaks:
    groups[(o.get("disease", "unknown"), o.get("country", "unknown"))].append(o)

historical_snapshots = []

for (disease, country), records in groups.items():
    records.sort(key=lambda x: x.get("date") or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    seen_source_urls = {}
    seen_case_counts = set()
    
    for i, r in enumerate(records):
        source_url = r.get("source_url", "")
        case_count = r.get("case_count")
        
        category = ""
        
        if source_url and source_url in seen_source_urls:
            pass # true_duplicate or pipeline_artifact
        else:
            if source_url:
                seen_source_urls[source_url] = r
            if i == 0:
                pass # original
            else:
                if case_count not in seen_case_counts and case_count is not None:
                    category = "historical_snapshot"
                elif r.get("source") == "disease.sh":
                    if case_count not in seen_case_counts:
                        category = "historical_snapshot"
                        
        seen_case_counts.add(case_count)
        
        if category == "historical_snapshot":
            historical_snapshots.append(r)

# Analyze the 71 snapshots
source_counts = collections.Counter(r.get("source") for r in historical_snapshots)

print(f"Total Historical Snapshots found: {len(historical_snapshots)}")
print("\n--- Sources ---")
for source, count in source_counts.items():
    print(f"{source}: {count}")

# Print a sample of non-disease.sh snapshots to see what they are
print("\n--- Sample of non-disease.sh snapshots ---")
for r in historical_snapshots:
    if r.get("source") != "disease.sh":
        print(f"Disease: {r.get('disease')}, Country: {r.get('country')}, Source: {r.get('source')}, URL: {r.get('source_url')}, Cases: {r.get('case_count')}")
