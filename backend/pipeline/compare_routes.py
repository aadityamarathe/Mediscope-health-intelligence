from backend.database.mongo_connection import get_db

def compare():
    db = get_db()
    
    print("=== /api/outbreaks ===")
    v1_count = db["outbreaks"].count_documents({})
    v2_count = db["outbreaks_v2"].count_documents({})
    print(f"v1 Returns up to 100 records (Total existing: {v1_count})")
    print(f"v2 Returns up to 100 records (Total existing: {v2_count})")
    
    print("\n=== /api/outbreaks/map ===")
    v1_map = list(db["outbreaks"].find({"lat": {"$ne": None}, "lng": {"$ne": None}}))
    v2_map = list(db["outbreaks_v2"].find({"lat": {"$ne": None}, "lng": {"$ne": None}}))
    print(f"v1 Map Pins: {len(v1_map)}")
    print(f"v2 Map Pins: {len(v2_map)}")
    
    print("\n=== /api/outbreaks/summary ===")
    def get_summary(coll_name):
        pipeline = [
            {"$group": {"_id": "$disease", "total_cases": {"$sum": "$case_count"}, "occurrences": {"$sum": 1}}},
            {"$sort": {"total_cases": -1}},
            {"$limit": 5}
        ]
        return list(db[coll_name].aggregate(pipeline))
        
    v1_sum = get_summary("outbreaks")
    v2_sum = get_summary("outbreaks_v2")
    
    print("v1 Top 5 Summaries:")
    for doc in v1_sum:
        print(f"  {doc['_id']}: Cases={doc['total_cases']}, Occurrences={doc['occurrences']}")
    print("v2 Top 5 Summaries:")
    for doc in v2_sum:
        print(f"  {doc['_id']}: Cases={doc['total_cases']}, Occurrences={doc['occurrences']}")
        
    print("\n=== Disease Explorer (/api/diseases Severity Calculation) ===")
    def get_severity(coll_name, d_name):
        res = list(db[coll_name].aggregate([
            {"$match": {"disease": d_name}},
            {"$group": {"_id": "$disease", "total_cases": {"$sum": "$case_count"}, "occurrences": {"$sum": 1}}}
        ]))
        if not res: return "low", 0, 0
        cases = res[0].get("total_cases", 0)
        occ = res[0].get("occurrences", 0)
        if cases > 100000 or occ > 50: return "high", cases, occ
        if cases > 10000 or occ > 10: return "medium", cases, occ
        return "low", cases, occ
        
    for target in ["covid-19", "malaria", "tuberculosis"]:
        v1_sev, v1_c, v1_o = get_severity("outbreaks", target)
        v2_sev, v2_c, v2_o = get_severity("outbreaks_v2", target)
        print(f"{target.capitalize()}:")
        print(f"  v1: {v1_sev} (Cases: {v1_c}, Occ: {v1_o})")
        print(f"  v2: {v2_sev} (Cases: {v2_c}, Occ: {v2_o})")
        
    print("\n=== Home Dashboard (/api/outbreaks/trends for Covid-19) ===")
    def get_trends(coll_name):
        pipeline = [
            {"$match": {"disease": "covid-19"}},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "case_count": {"$sum": "$case_count"}}},
            {"$sort": {"_id": 1}}
        ]
        return list(db[coll_name].aggregate(pipeline))
        
    v1_trends = get_trends("outbreaks")
    v2_trends = get_trends("outbreaks_v2")
    print(f"v1 Data Points: {len(v1_trends)}")
    print(f"v2 Data Points: {len(v2_trends)}")
    if v2_trends:
        print(f"v2 Dates available: {[d['_id'] for d in v2_trends[:3]]} ...")

if __name__ == "__main__":
    compare()
