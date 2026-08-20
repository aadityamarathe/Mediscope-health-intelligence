from backend.database.mongo_connection import get_db
import collections
import datetime

def migrate_and_validate():
    db = get_db()
    
    print("--- 1. Fetching current outbreaks ---")
    old_outbreaks = list(db["outbreaks"].find({}))
    
    # Survivor Logic
    groups = collections.defaultdict(list)
    for o in old_outbreaks:
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
        
        # Remove old _id
        if "_id" in survivor:
            del survivor["_id"]
            
        survivors.append(survivor)
        
    print("--- 2. Building outbreaks_v2 ---")
    db["outbreaks_v2"].drop()
    if survivors:
        db["outbreaks_v2"].insert_many(survivors)
        
    # Read back to confirm
    new_outbreaks = list(db["outbreaks_v2"].find({}))
    
    print("\n=== Validation Report Data ===")
    
    # Helper to calculate stats
    def calc_stats(data):
        disease_dist = collections.Counter(d.get("disease", "unknown") for d in data)
        country_dist = collections.Counter(d.get("country", "unknown") for d in data)
        source_dist = collections.Counter(d.get("source", "unknown") for d in data)
        map_coverage = sum(1 for d in data if d.get("lat") is not None and d.get("lng") is not None)
        return {
            "total": len(data),
            "disease_dist": disease_dist,
            "country_dist": country_dist,
            "source_dist": source_dist,
            "map_coverage": map_coverage
        }
        
    old_stats = calc_stats(old_outbreaks)
    new_stats = calc_stats(new_outbreaks)
    
    print(f"\nTotal Records: v1={old_stats['total']} | v2={new_stats['total']}")
    print(f"Map Coverage (Valid Lat/Lng): v1={old_stats['map_coverage']} | v2={new_stats['map_coverage']}")
    
    print("\nDisease Distribution (v1 -> v2):")
    all_diseases = set(old_stats['disease_dist'].keys()) | set(new_stats['disease_dist'].keys())
    for d in sorted(all_diseases):
        print(f"  {d}: {old_stats['disease_dist'].get(d, 0)} -> {new_stats['disease_dist'].get(d, 0)}")

    print("\nSource Distribution (v1 -> v2):")
    all_sources = set(old_stats['source_dist'].keys()) | set(new_stats['source_dist'].keys())
    for s in sorted(all_sources):
        print(f"  {s}: {old_stats['source_dist'].get(s, 0)} -> {new_stats['source_dist'].get(s, 0)}")

    print("\nCountry Distribution (v1 -> v2) [Top 10 most impacted]:")
    top_countries = sorted(old_stats['country_dist'].items(), key=lambda x: x[1], reverse=True)[:10]
    for c, old_cnt in top_countries:
        print(f"  {c}: {old_cnt} -> {new_stats['country_dist'].get(c, 0)}")
        
    # For each disease, show source distribution of survivors
    print("\nDisease Survivor Sources (v2 only):")
    disease_survivor_sources = collections.defaultdict(collections.Counter)
    for s in new_outbreaks:
        disease_survivor_sources[s.get("disease", "unknown")][s.get("source", "unknown")] += 1
        
    for d, counts in sorted(disease_survivor_sources.items()):
        source_str = ", ".join(f"{src}: {cnt}" for src, cnt in counts.items())
        print(f"  {d}: {source_str}")
        
    print("\nTop 20 Survivor Records (by case count):")
    top_20 = sorted(new_outbreaks, key=lambda x: x.get("case_count") or 0, reverse=True)[:20]
    for i, s in enumerate(top_20, 1):
        print(f"  {i}. {s.get('disease')} | {s.get('country')} | Cases: {s.get('case_count')} | Source: {s.get('source')}")

if __name__ == "__main__":
    migrate_and_validate()
