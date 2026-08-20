from backend.database.mongo_connection import get_db
from collections import defaultdict
import datetime

def classify_records():
    db = get_db()
    outbreaks = list(db["outbreaks"].find({}))
    
    # Group by (disease, country)
    groups = defaultdict(list)
    for o in outbreaks:
        disease = o.get("disease", "unknown")
        country = o.get("country", "unknown")
        groups[(disease, country)].append(o)
        
    categories = {
        "original_preserved": 0,
        "true_duplicate": 0,
        "pipeline_artifact": 0,
        "historical_snapshot": 0,
        "unknown": 0
    }
    
    safe_to_delete = 0
    manual_review = 0
    must_preserve = 0
    
    for (disease, country), records in groups.items():
        # Sort by date ascending
        records.sort(key=lambda x: x.get("date") or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
        
        # Keep track of what we've seen in this group
        seen_source_urls = {} # URL -> first record
        seen_case_counts = set()
        
        for i, r in enumerate(records):
            source_url = r.get("source_url", "")
            case_count = r.get("case_count")
            
            # If it's the very first record for this disease/country, we must preserve it
            # Wait, disease.sh has multiple historical snapshots. 
            # The first observation of a source_url or a genuine historical snapshot should be preserved.
            
            # Let's classify:
            category = ""
            
            if source_url and source_url in seen_source_urls:
                # We have already seen this exact article.
                # Why is there another record?
                first_r = seen_source_urls[source_url]
                if case_count == first_r.get("case_count"):
                    category = "true_duplicate"
                else:
                    # Same article, different case count. 
                    # This happens when pipeline re-runs and WHO GHO data updated.
                    category = "pipeline_artifact"
            else:
                # First time seeing this source_url in this group
                if source_url:
                    seen_source_urls[source_url] = r
                
                # Is it a historical snapshot?
                # If i == 0, it's the first record (original)
                if i == 0:
                    category = "original_preserved"
                else:
                    # It's a new source_url (or empty source_url like disease.sh)
                    # If it has a different case_count, it's a historical snapshot
                    if case_count not in seen_case_counts and case_count is not None:
                        category = "historical_snapshot"
                    elif r.get("source") == "disease.sh":
                        # disease.sh data with same case count as before -> true duplicate
                        # Wait, if case_count is the same as previous day, it's just a repeated ingestion
                        if case_count in seen_case_counts:
                            category = "true_duplicate"
                        else:
                            category = "historical_snapshot"
                    else:
                        # Different article, but same case count?
                        # Could be two news articles reporting the same outbreak.
                        category = "unknown"
            
            seen_case_counts.add(case_count)
            
            # Increment category
            if category:
                categories[category] += 1
            else:
                categories["unknown"] += 1
                
            # Actions
            if category in ["true_duplicate", "pipeline_artifact"]:
                safe_to_delete += 1
            elif category in ["original_preserved", "historical_snapshot"]:
                must_preserve += 1
            else:
                manual_review += 1

    print("=== Category Counts ===")
    for k, v in categories.items():
        print(f"{k}: {v}")
        
    print("\n=== Estimates ===")
    print(f"Safe to delete immediately: {safe_to_delete}")
    print(f"Must be preserved: {must_preserve}")
    print(f"Requires manual review: {manual_review}")
    
    print("\n=== Extra info ===")
    print(f"Total processed: {len(outbreaks)}")

if __name__ == "__main__":
    classify_records()
