from backend.database.mongo_connection import get_db
from collections import defaultdict
from pprint import pprint

db = get_db()
outbreaks = list(db["outbreaks"].find({}))

print(f"Total outbreaks: {len(outbreaks)}")

# Group by (disease, country)
groups = defaultdict(list)
for o in outbreaks:
    disease = o.get("disease", "unknown")
    country = o.get("country", "unknown")
    groups[(disease, country)].append(o)

total_groups = len(groups)
print(f"Total unique (disease, country) pairs: {total_groups}")

# Analyze duplicates
perfect_dupes = 0
varying_cases = 0
varying_dates = 0

for key, records in groups.items():
    if len(records) > 1:
        # Check if dates vary
        dates = {r.get("date").strftime("%Y-%m-%d") for r in records if r.get("date")}
        if len(dates) > 1:
            varying_dates += len(records) - 1
            
        # Check if case counts vary
        cases = {r.get("case_count") for r in records}
        if len(cases) > 1:
            varying_cases += len(records) - 1
        
        if len(dates) > 1 and len(cases) == 1:
            # Same case count, different date -> likely identical data reingested
            perfect_dupes += len(records) - 1

print(f"Total redundant records (beyond 1 per group): {len(outbreaks) - total_groups}")
print(f"Records with same disease/country but varying dates: {varying_dates}")
print(f"Records with same disease/country but varying case counts: {varying_cases}")
print(f"Records with same disease/country, varying dates, but IDENTICAL case counts (true duplicates): {perfect_dupes}")

print("\n--- Example of duplicates ---")
example_key = None
for key, records in groups.items():
    if len(records) > 5 and key[0] != "covid-19":  # Find a non-covid example with many dupes
        example_key = key
        break

if not example_key:
    for key, records in groups.items():
        if len(records) > 5:
            example_key = key
            break

if example_key:
    print(f"Disease: {example_key[0]}, Country: {example_key[1]}")
    for r in groups[example_key][:5]:
        print(f"  Date: {r.get('date')}, Cases: {r.get('case_count')}, Source URL: {r.get('source_url')}")
    print(f"  ... and {len(groups[example_key]) - 5} more")

