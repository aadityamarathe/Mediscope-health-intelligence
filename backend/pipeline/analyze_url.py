from backend.database.mongo_connection import get_db

db = get_db()
url = "https://www.who.int/news/item/24-03-2026-who-recommends-new-diagnostic-tools-to-help-end-tb"

outbreaks = list(db["outbreaks"].find({"source_url": url}))
print(f"Total outbreaks for this URL: {len(outbreaks)}")

for o in outbreaks[:10]:
    print(f"Disease: {o.get('disease')}, Country: {o.get('country')}, Date: {o.get('date')}, Cases: {o.get('case_count')}")

raw_articles = list(db["raw_articles"].find({"url": url}))
print(f"\nTotal raw_articles for this URL: {len(raw_articles)}")

# Is disease.sh producing duplicates?
disease_sh_outbreaks = list(db["outbreaks"].find({"source": "disease.sh"}))
print(f"\nTotal outbreaks from disease.sh: {len(disease_sh_outbreaks)}")

disease_sh_groups = {}
for o in disease_sh_outbreaks:
    key = (o.get("disease"), o.get("country"))
    disease_sh_groups[key] = disease_sh_groups.get(key, 0) + 1

dupes = {k: v for k, v in disease_sh_groups.items() if v > 1}
print(f"disease.sh duplicate groups: {len(dupes)}")
for k, v in list(dupes.items())[:5]:
    print(f"  {k}: {v} records")
