from ..database.mongo_connection import get_db
import re

def enrich_case_count(disease, country):
    if not disease:
        return None
        
    db = get_db()
    
    disease_lower = disease.lower().strip()
    
    if country:
        country_lower = country.lower().strip()
        
        country_regex = re.compile(f"^{re.escape(country_lower)}$", re.IGNORECASE)
        
        stat = db["disease_stats"].find_one({
            "disease": disease_lower,
            "country": country_regex
        })
        
        if stat and "case_count" in stat:
            return int(stat["case_count"])

    # Fallback to finding max cases for this disease globally
    # Removed due to unsafe enrichment (e.g. assigning Nigeria's malaria count to Switzerland)
    print(f"  -> enrich_case_count_failed: no exact match in disease_stats for {disease} in {country}")
    return None
