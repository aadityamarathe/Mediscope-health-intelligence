from backend.database.mongo_connection import get_db
import collections

def dry_run():
    db = get_db()
    outbreaks = list(db["outbreaks"].find({}))
    
    current_count = len(outbreaks)
    
    # Group by (disease, country)
    groups = collections.defaultdict(list)
    for o in outbreaks:
        groups[(o.get("disease", "unknown"), o.get("country", "unknown"))].append(o)
        
    expected_count = len(groups)
    merged_count = current_count - expected_count
    
    print(f"Current outbreak count: {current_count}")
    print(f"Expected outbreak count: {expected_count}")
    print(f"Records to be merged (deleted): {merged_count}")
    print(f"Records that will remain: {expected_count}\n")
    
    # Disease level stats
    disease_stats = collections.defaultdict(lambda: {"current": 0, "expected": set()})
    
    for (disease, country), records in groups.items():
        disease_stats[disease]["current"] += len(records)
        disease_stats[disease]["expected"].add(country)
        
    print("| Disease | Current Records | Expected Records After Migration |")
    print("| ------- | --------------- | -------------------------------- |")
    for disease, stats in sorted(disease_stats.items()):
        print(f"| {disease.capitalize()} | {stats['current']} | {len(stats['expected'])} |")

if __name__ == "__main__":
    dry_run()
