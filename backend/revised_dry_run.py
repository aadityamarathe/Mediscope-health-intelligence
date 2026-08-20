from backend.database.mongo_connection import get_db

db = get_db()
v2_records = list(db["outbreaks_v2"].find({}))

changed_count = 0
unchanged_count = 0
improved_records = []
degraded_records = []
changes = []

def get_source_rank(source_type):
    # Map sources to ranks
    # disease.sh -> 4
    # who_gho -> 3
    # extracted -> 2
    # missing / unavailable -> 1
    
    st = str(source_type).lower().strip()
    if st == "disease.sh" or st == "disease_sh": return 4
    if "gho" in st: return 3
    if "extracted" in st: return 2
    return 1

def is_valid_coord(lat, lng):
    if lat is None or lng is None: return False
    try:
        lat, lng = float(lat), float(lng)
        return -90 <= lat <= 90 and -180 <= lng <= 180 and not (lat == 0.0 and lng == 0.0)
    except:
        return False

for current in v2_records:
    disease = current.get("disease")
    country = current.get("country")
    
    simulated = dict(current)
    incoming_records = list(db["outbreaks"].find({"disease": disease, "country": country}))
    
    old_cc = current.get("case_count")
    old_date = current.get("date")
    old_source = current.get("case_count_source") or "missing"
    old_source_name = current.get("source")
    
    for inc in incoming_records:
        inc_date = inc.get("date")
        inc_cc = inc.get("case_count")
        inc_source_type = inc.get("case_count_source") or "missing"
        
        sim_date = simulated.get("date")
        sim_cc = simulated.get("case_count")
        sim_source_type = simulated.get("case_count_source") or "missing"
        
        # 1. Date always advances to most recent (proving outbreak is still active)
        if inc_date and (not sim_date or inc_date > sim_date):
            simulated["date"] = inc_date
            
        # 2. Source-aware Case Count Survivor
        inc_rank = get_source_rank(inc_source_type)
        sim_rank = get_source_rank(sim_source_type)
        
        if inc_rank > sim_rank:
            # Higher priority source overrides lower priority, period.
            simulated["case_count"] = inc_cc
            simulated["source"] = inc.get("source")
            simulated["source_url"] = inc.get("source_url")
            simulated["case_count_source"] = inc_source_type
        elif inc_rank == sim_rank:
            # Same priority source, highest number wins
            # Handle None cases
            inc_cc_val = inc_cc if inc_cc is not None else -1
            sim_cc_val = sim_cc if sim_cc is not None else -1
            if inc_cc_val > sim_cc_val:
                simulated["case_count"] = inc_cc
                simulated["source"] = inc.get("source")
                simulated["source_url"] = inc.get("source_url")
                simulated["case_count_source"] = inc_source_type
                
        # 3. Coordinates
        if is_valid_coord(inc.get("lat"), inc.get("lng")) and not is_valid_coord(simulated.get("lat"), simulated.get("lng")):
            simulated["lat"] = inc.get("lat")
            simulated["lng"] = inc.get("lng")
            
    # Check changes
    if (simulated.get("case_count") != old_cc or 
        simulated.get("date") != old_date or 
        simulated.get("case_count_source") != old_source):
        
        changed_count += 1
        changes.append({
            "disease": disease,
            "country": country,
            "old_cc": old_cc,
            "new_cc": simulated.get("case_count"),
            "old_date": str(old_date),
            "new_date": str(simulated.get("date")),
            "old_source": old_source,
            "new_source": simulated.get("case_count_source")
        })
        
        # Check if improved or degraded
        # Improved: We got rid of a massive hallucination (e.g. 68M went down to a realistic number via higher source rank)
        # or we gained a higher case count from an equal/better source
        old_val = old_cc if old_cc is not None else -1
        new_val = simulated.get("case_count") if simulated.get("case_count") is not None else -1
        
        if old_val == 68466353 and new_val < 68466353:
            improved_records.append(f"{disease} in {country}: Shed hallucination ({old_val} -> {new_val}) via {simulated.get('case_count_source')}")
        elif get_source_rank(simulated.get("case_count_source")) > get_source_rank(old_source):
            improved_records.append(f"{disease} in {country}: Source rank improved ({old_source} -> {simulated.get('case_count_source')})")
        elif get_source_rank(simulated.get("case_count_source")) < get_source_rank(old_source):
            degraded_records.append(f"{disease} in {country}: Source rank degraded")
            
    else:
        unchanged_count += 1

print(f"Total V2 Records: {len(v2_records)}")
print(f"Changed: {changed_count}")
print(f"Unchanged: {unchanged_count}")

print(f"\nImproved Records: {len(improved_records)}")
for r in improved_records[:10]:
    print("  " + r)
    
print(f"\nDegraded Records: {len(degraded_records)}")
for r in degraded_records[:10]:
    print("  " + r)

print("\n--- SAMPLE OF CHANGES (up to 20) ---")
for c in changes[:20]:
    print(f"{c['disease'].upper()} in {c['country'].upper()}:")
    print(f"  Cases: {c['old_cc']} -> {c['new_cc']}")
    print(f"  Date:  {c['old_date']} -> {c['new_date']}")
    print(f"  Source Type: {c['old_source']} -> {c['new_source']}")
