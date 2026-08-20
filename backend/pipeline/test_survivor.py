from backend.database.mongo_connection import get_db
import collections
import datetime

def test_survivor_logic():
    db = get_db()
    outbreaks = list(db["outbreaks"].find({}))
    
    groups = collections.defaultdict(list)
    for o in outbreaks:
        groups[(o.get("disease", "unknown"), o.get("country", "unknown"))].append(o)
        
    survivors = []
    min_date = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    
    for key, records in groups.items():
        # Enhanced survivor selection logic
        # 1. Highest case count
        # 2. Most recent date
        # 3. Prefer non-empty source_url
        
        def score(r):
            cases = r.get("case_count") or 0
            date = r.get("date") or min_date
            has_url = 1 if r.get("source_url") and r.get("source") != "disease.sh" else 0
            return (cases, date, has_url)
            
        records.sort(key=score, reverse=True)
        survivors.append(records[0])
        
    print(f"Total survivors: {len(survivors)}")
    
    # Print samples for major diseases
    targets = ["covid-19", "cholera", "malaria", "tuberculosis"]
    print("\n=== Sample Survivors ===")
    for target in targets:
        print(f"\n--- {target.capitalize()} ---")
        # Find top 3 countries by highest case count for this disease
        disease_survivors = [s for s in survivors if s.get("disease") == target]
        disease_survivors.sort(key=lambda x: x.get("case_count") or 0, reverse=True)
        
        for s in disease_survivors[:3]:
            date_str = s.get("date").strftime("%Y-%m-%d") if s.get("date") else "Unknown"
            cases = s.get("case_count")
            url = s.get("source_url", "No URL")
            print(f"Country: {s.get('country')}")
            print(f"  Cases: {cases} | Date: {date_str} | URL: {url}")

if __name__ == "__main__":
    test_survivor_logic()
