"""
Audits duplicate outbreak records to answer:
1. How many are true duplicates vs legitimate historical snapshots?
2. How many are caused by datetime.now() fallback (artificial duplicates)?
3. What would the trends endpoint lose if we deduplicated?
"""
from backend.config import MONGODB_URI
from pymongo import MongoClient
from datetime import datetime, timezone
from collections import defaultdict

client = MongoClient(MONGODB_URI)
db = client['mediscope']

total = db.outbreaks.count_documents({})
print(f"Total records: {total}")
print(f"Unique disease+country pairs: 367 (already known)\n")

# ── Q1: Categorize duplicates ──────────────────────────────────────
print("=" * 60)
print("Q1: TRUE DUPLICATES vs HISTORICAL SNAPSHOTS")
print("=" * 60)

pipeline = [
    {"$group": {
        "_id": {"disease": "$disease", "country": "$country"},
        "ids": {"$push": "$_id"},
        "dates": {"$push": "$date"},
        "case_counts": {"$push": "$case_count"},
        "record_count": {"$sum": 1}
    }},
    {"$match": {"record_count": {"$gt": 1}}}
]

true_dupes = 0        # same date AND same case_count
datetime_now_dupes = 0  # date is today (fallback artifact)
historical = 0        # different dates, different case_counts (legitimate)
ambiguous = 0         # different dates, same case_count

now_date = datetime.now(timezone.utc).date()
today_str = now_date.isoformat()

for group in db.outbreaks.aggregate(pipeline, allowDiskUse=True):
    dates = [d for d in group["dates"] if d is not None]
    case_counts = group["case_counts"]
    
    date_strs = []
    for d in dates:
        if hasattr(d, 'date'):
            date_strs.append(d.date().isoformat())
        else:
            date_strs.append(str(d))
    
    unique_dates = set(date_strs)
    unique_cases = set(c for c in case_counts if c is not None)
    
    # Count how many records have today's date (datetime.now() fallback)
    today_count = sum(1 for d in date_strs if d == today_str)
    
    if today_count > 1:
        # Multiple records with today's date = pipeline re-run artifacts
        datetime_now_dupes += (today_count - 1)
    
    if len(unique_dates) == 1 and len(unique_cases) <= 1:
        # Same date, same case count = pure duplicate
        true_dupes += (group["record_count"] - 1)
    elif len(unique_dates) > 1 and len(unique_cases) > 1:
        # Different dates AND different case counts = potential historical value
        historical += (group["record_count"] - 1)
    else:
        # Different dates, same case count = probably dupes but ambiguous
        ambiguous += (group["record_count"] - 1)

print(f"  Pure duplicates (same date + same cases):     {true_dupes}")
print(f"  datetime.now() artifacts (today's date):      {datetime_now_dupes}")
print(f"  Potential historical snapshots (diff date+cases): {historical}")
print(f"  Ambiguous (diff date, same cases):            {ambiguous}")
print(f"  Safe to delete without risk:                  {true_dupes + datetime_now_dupes}")

# ── Q2: Trends endpoint impact ─────────────────────────────────────
print("\n" + "=" * 60)
print("Q2: TRENDS ENDPOINT — what does it actually query?")
print("=" * 60)

# Check date distribution for top diseases
for disease in ['covid-19', 'tuberculosis', 'malaria', 'cholera']:
    records = list(db.outbreaks.find(
        {"disease": disease},
        {"date": 1, "case_count": 1, "country": 1}
    ).sort("date", 1))
    
    dates = [r.get("date") for r in records if r.get("date")]
    date_strs = set()
    for d in dates:
        if hasattr(d, 'date'):
            date_strs.add(d.date().isoformat())
    
    print(f"\n  {disease}: {len(records)} records, {len(date_strs)} unique dates")
    if date_strs:
        sorted_dates = sorted(date_strs)
        print(f"    Earliest: {sorted_dates[0]}")
        print(f"    Latest:   {sorted_dates[-1]}")
        print(f"    Span: {len(sorted_dates)} distinct dates")

# ── Q3: Publication date fallback analysis ─────────────────────────
print("\n" + "=" * 60)
print("Q3: DATETIME.NOW() FALLBACK — how many records affected?")
print("=" * 60)

# Records where date == created_at (strong signal of fallback)
today_records = db.outbreaks.count_documents({
    "date": {"$gte": datetime(2026, 6, 23, 0, 0, 0),
             "$lt":  datetime(2026, 6, 24, 0, 0, 0)}
})
print(f"  Records with date on 2026-06-23 (backfill day): {today_records}")
print(f"  These are likely fallback artifacts from processor re-runs")

# Records with no source_url (can't verify origin)
no_url = db.outbreaks.count_documents({"source_url": None})
print(f"  Records with no source_url:                    {no_url}")

print("\n" + "=" * 60)
print("RECOMMENDATION")
print("=" * 60)
print("""
Based on this audit:
  - If true_dupes + datetime_now_dupes > 1000: safe batch to delete
  - If historical > 500: trends endpoint has real data worth keeping
  - Decision: split into current_outbreaks + outbreak_history, OR
    fix upsert key and accept losing pre-fix history
""")