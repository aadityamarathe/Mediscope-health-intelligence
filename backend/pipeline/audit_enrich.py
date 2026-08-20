from backend.database.mongo_connection import get_db
import random

db = get_db()

# 1. Inspect disease_stats for Malaria to find the 68m record
malaria_max = db["disease_stats"].find_one({"disease": "malaria"}, sort=[("case_count", -1)])
print("--- Malaria Max Record ---")
print(malaria_max)

# 2. Inspect lookup paths for requested diseases
diseases = ["malaria", "tuberculosis", "cholera", "dengue", "measles", "monkeypox"]

print("\n--- Lookup Paths & Max Globals ---")
for d in diseases:
    # Get max
    max_rec = db["disease_stats"].find_one({"disease": d}, sort=[("case_count", -1)])
    if max_rec:
        print(f"Disease: {d} | Max Global Case Count: {max_rec.get('case_count')} (from {max_rec.get('country')})")
    else:
        print(f"Disease: {d} | No data in disease_stats")

# 3. Fetch 10 random outbreak records and trace their case_count origin
print("\n--- 10 Random Outbreak Records ---")
outbreaks = list(db["outbreaks"].find({}))
random.seed(42)
sample = random.sample(outbreaks, min(10, len(outbreaks)))

for i, o in enumerate(sample, 1):
    disease = o.get("disease", "unknown").lower()
    country = o.get("country", "unknown").lower()
    cases = o.get("case_count")
    
    # Check if exact match exists in disease_stats
    exact = db["disease_stats"].find_one({"disease": disease, "country": country})
    if exact and int(exact.get("case_count", 0)) == cases:
        origin = "Country-specific exact match from WHO GHO (disease_stats)"
    else:
        max_rec = db["disease_stats"].find_one({"disease": disease}, sort=[("case_count", -1)])
        if max_rec and int(max_rec.get("case_count", 0)) == cases:
            origin = f"Global maximum fallback from WHO GHO (inherited from {max_rec.get('country')})"
        else:
            origin = "Extracted directly from article text / disease.sh / other"
            
    print(f"{i}. Disease: {o.get('disease')} | Country: {o.get('country')} | Cases: {cases}")
    print(f"   Origin: {origin}")
