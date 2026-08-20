from backend.database.mongo_connection import get_db
import collections
import datetime
from backend.pipeline.enricher import enrich_case_count

def migrate_and_validate():
    db = get_db()
    
    print("--- 1. Fetching current outbreaks ---")
    old_outbreaks = list(db["outbreaks"].find({}))
    
    print("--- 2. Re-evaluating enrichments ---")
    fixed_outbreaks = []
    for o in old_outbreaks:
        o_copy = o.copy()
        
        # If it was enriched by WHO GHO, re-evaluate it to strip false global fallbacks
        if o_copy.get("case_count_source") == "who_gho":
            new_count = enrich_case_count(o_copy.get("disease"), o_copy.get("country"))
            if new_count is None:
                o_copy["case_count"] = None
                o_copy["case_count_source"] = "missing"
                o_copy["case_count_estimated"] = True
            else:
                o_copy["case_count"] = new_count
                
        fixed_outbreaks.append(o_copy)
    
    print("--- 3. Applying Survivor Logic ---")
    groups = collections.defaultdict(list)
    for o in fixed_outbreaks:
        groups[(o.get("disease", "unknown"), o.get("country", "unknown"))].append(o)
        
    survivors = []
    min_date = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    
    for key, records in groups.items():
        def score(r):
            cases = r.get("case_count") or 0
            date = r.get("date") or min_date
            has_url = 1 if r.get("source_url") and r.get("source") != "disease.sh" else 0
            return (cases, date, has_url)
            
        records.sort(key=score, reverse=True)
        survivor = records[0].copy()
        
        if "_id" in survivor:
            del survivor["_id"]
            
        survivors.append(survivor)
        
    print("--- 4. Building outbreaks_v2 ---")
    db["outbreaks_v2"].drop()
    if survivors:
        db["outbreaks_v2"].insert_many(survivors)
        
    new_outbreaks = list(db["outbreaks_v2"].find({}))
    
    print("\n=== Validation Report Data ===")
    
    def calc_stats(data):
        disease_dist = collections.Counter(d.get("disease", "unknown") for d in data)
        country_dist = collections.Counter(d.get("country", "unknown") for d in data)
        source_dist = collections.Counter(d.get("source", "unknown") for d in data)
        # Note: missing or 0 counts should still be valid if lat/lng are there, but let's count valid cases
        missing_cases = sum(1 for d in data if d.get("case_count") is None)
        return {
            "total": len(data),
            "disease_dist": disease_dist,
            "country_dist": country_dist,
            "source_dist": source_dist,
            "missing_cases": missing_cases
        }
        
    old_stats = calc_stats(old_outbreaks)
    new_stats = calc_stats(new_outbreaks)
    
    print(f"\nTotal Records: v1={old_stats['total']} | v2={new_stats['total']}")
    print(f"Missing Case Counts: v1={old_stats['missing_cases']} | v2={new_stats['missing_cases']}")
    
    print("\nDisease Distribution (v1 -> v2):")
    all_diseases = set(old_stats['disease_dist'].keys()) | set(new_stats['disease_dist'].keys())
    for d in sorted(all_diseases):
        print(f"  {d}: {old_stats['disease_dist'].get(d, 0)} -> {new_stats['disease_dist'].get(d, 0)}")

    print("\nSource Distribution (v1 -> v2):")
    all_sources = set(old_stats['source_dist'].keys()) | set(new_stats['source_dist'].keys())
    for s in sorted(all_sources):
        print(f"  {s}: {old_stats['source_dist'].get(s, 0)} -> {new_stats['source_dist'].get(s, 0)}")
        
    print("\nTop 20 Survivor Records (by case count):")
    top_20 = sorted(new_outbreaks, key=lambda x: x.get("case_count") or 0, reverse=True)[:20]
    for i, s in enumerate(top_20, 1):
        print(f"  {i}. {s.get('disease')} | {s.get('country')} | Cases: {s.get('case_count')} | Source: {s.get('source')}")

if __name__ == "__main__":
    migrate_and_validate()
