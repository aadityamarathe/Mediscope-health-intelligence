from datetime import datetime, timezone

import requests

from ...database.mongo_connection import get_db
from ...utils.severity import calculate_outbreak_severity


class DiseaseAPISpider:
    api_url = "https://disease.sh/v3/covid-19/countries"

    def __init__(self):
        self.db = get_db()
        self.item_count = 0

    def run(self):
        try:
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            countries = response.json()
        except Exception as exc:
            print(f"DiseaseAPISpider error: {exc}")
            return

        outbreaks_v2 = self.db["outbreaks_v2"]
        crawled_at = datetime.now(timezone.utc)
        
        def get_source_rank(st):
            if not st: return 1
            st = str(st).lower().strip()
            if "disease.sh" in st or "disease_sh" in st: return 4
            if "gho" in st: return 3
            if "extracted" in st: return 2
            return 1
            
        def is_valid_coord(lt, lg):
            if lt is None or lg is None: return False
            try:
                lt, lg = float(lt), float(lg)
                return -90 <= lt <= 90 and -180 <= lg <= 180 and not (lt == 0.0 and lg == 0.0)
            except: return False

        for country_data in countries:
            disease = "covid-19"
            country = country_data.get("country")
            if not country: continue
            
            country_info = country_data.get("countryInfo") or {}
            lat = country_info.get("lat")
            lng = country_info.get("long")
            case_count = country_data.get("cases")
            source = "disease.sh"
            source_url = self.api_url
            case_count_source = "disease.sh"
            
            existing = outbreaks_v2.find_one({"disease": disease, "country": country})
            
            try:
                if existing:
                    updates = {"updated_at": datetime.utcnow()}
                    
                    # Date
                    sim_date = existing.get("date")
                    sim_date_aware = sim_date.replace(tzinfo=timezone.utc) if sim_date and sim_date.tzinfo is None else sim_date

                    if crawled_at and (not sim_date_aware or crawled_at > sim_date_aware):
                        if sim_date and sim_date.tzinfo is None:
                            updates["date"] = crawled_at.replace(tzinfo=None)
                        else:
                            updates["date"] = crawled_at
                    
                    inc_rank = get_source_rank(case_count_source)
                    sim_rank = get_source_rank(existing.get("case_count_source") or "missing")
                    inc_cc = case_count if case_count is not None else -1
                    sim_cc = existing.get("case_count") if existing.get("case_count") is not None else -1
                    
                    if inc_rank > sim_rank or (inc_rank == sim_rank and inc_cc > sim_cc):
                        updates["case_count"] = case_count
                        updates["severity"] = calculate_outbreak_severity(case_count)
                        updates["case_count_estimated"] = False
                        updates["case_count_source"] = case_count_source
                        updates["source"] = source
                        updates["source_url"] = source_url
                    
                    if is_valid_coord(lat, lng) and not is_valid_coord(existing.get("lat"), existing.get("lng")):
                        updates["lat"] = float(lat)
                        updates["lng"] = float(lng)
                        updates["location"] = {"type": "Point", "coordinates": [float(lng), float(lat)]}
                        
                    if len(updates) > 1:
                        outbreaks_v2.update_one({"_id": existing["_id"]}, {"$set": updates})
                        self.item_count += 1
                else:
                    now_utc = datetime.utcnow()
                    document = {
                        "disease": disease,
                        "country": country,
                        "lat": float(lat) if lat is not None else 0.0,
                        "lng": float(lng) if lng is not None else 0.0,
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                float(lng) if lng is not None else 0.0,
                                float(lat) if lat is not None else 0.0,
                            ],
                        },
                        "date": crawled_at.replace(tzinfo=None),
                        "case_count": case_count,
                        "severity": calculate_outbreak_severity(case_count),
                        "case_count_estimated": False,
                        "case_count_source": case_count_source,
                        "source": source,
                        "source_url": source_url,
                        "created_at": now_utc,
                        "updated_at": now_utc
                    }
                    outbreaks_v2.insert_one(document)
                    self.item_count += 1
            except Exception as exc:
                print(f"DiseaseAPISpider upsert error: {exc}")

        print(f"DiseaseAPISpider synced {self.item_count} items to outbreaks_v2.")
