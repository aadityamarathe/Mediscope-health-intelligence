from backend.database.mongo_connection import get_db

db = get_db()
v2_records = list(db["outbreaks_v2"].find({}))

changed_count = 0
unchanged_count = 0
lost_info = []
source_decreased = []
changes = []

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
    
    # Simulate processing all old records against the current v2
    simulated = dict(current)
    
    incoming_records = list(db["outbreaks"].find({"disease": disease, "country": country}))
    
    changed = False
    old_cc = current.get("case_count")
    old_date = current.get("date")
    old_source = current.get("source")
    
    for inc in incoming_records:
        inc_date = inc.get("date")
        inc_cc = inc.get("case_count")
        
        sim_date = simulated.get("date")
        sim_cc = simulated.get("case_count") or 0
        
        # Newest date wins
        if inc_date and (not sim_date or inc_date > sim_date):
            simulated["date"] = inc_date
            
        # Highest case_count wins, source follows case_count
        if inc_cc is not None and inc_cc > sim_cc:
            simulated["case_count"] = inc_cc
            simulated["source"] = inc.get("source")
            simulated["source_url"] = inc.get("source_url")
            simulated["case_count_source"] = inc.get("case_count_source")
            
        # Coordinates update only if valid and currently missing/invalid
        if is_valid_coord(inc.get("lat"), inc.get("lng")) and not is_valid_coord(simulated.get("lat"), simulated.get("lng")):
            simulated["lat"] = inc.get("lat")
            simulated["lng"] = inc.get("lng")
            
    # Check if simulated is different from current in meaningful ways
    if (simulated.get("case_count") != old_cc or 
        simulated.get("date") != old_date or 
        simulated.get("source") != old_source):
        
        changed_count += 1
        changes.append({
            "disease": disease,
            "country": country,
            "old_cc": old_cc,
            "new_cc": simulated.get("case_count"),
            "old_date": str(old_date),
            "new_date": str(simulated.get("date")),
            "old_source": old_source,
            "new_source": simulated.get("source")
        })
        
        # Check if source quality decreased (e.g. who_gho -> disease.sh or something)
        # Actually if highest case count wins, source follows. But we can check manually.
        if str(old_source) != str(simulated.get("source")):
            source_decreased.append(f"{disease} in {country}: {old_source} -> {simulated.get('source')}")
            
    else:
        unchanged_count += 1

print(f"Total V2 Records: {len(v2_records)}")
print(f"Changed: {changed_count}")
print(f"Unchanged: {unchanged_count}")

print("\n--- SAMPLE OF CHANGES (up to 20) ---")
for c in changes[:20]:
    print(f"{c['disease'].upper()} in {c['country'].upper()}:")
    print(f"  Cases: {c['old_cc']} -> {c['new_cc']}")
    print(f"  Date:  {c['old_date']} -> {c['new_date']}")
    print(f"  Source: {c['old_source']} -> {c['new_source']}")

print(f"\nPotential Source Quality Shifts: {len(source_decreased)}")
for s in source_decreased[:10]:
    print("  " + s)

