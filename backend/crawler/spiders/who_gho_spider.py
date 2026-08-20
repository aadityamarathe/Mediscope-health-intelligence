import requests
from datetime import datetime, timezone
from ...database.mongo_connection import get_db
from ...pipeline.processor import _normalize_country

class WHOGHOSpider:
    def __init__(self):
        self.db = get_db()
        self.base_url = "https://ghoapi.azureedge.net/api/"
        
        self.disease_mapping = {
            "cholera": "cholera",
            "malaria": "malaria",
            "tuberculosis": "tuberculosis",
            "measles": "measles",
            "hiv/aids": "hiv",
            "hepatitis b": "hepatitis b",
            "leprosy": "leprosy",
            "dengue": "dengue",
            "typhoid": "typhoid",
            "monkeypox": "monkeypox",
            "mpox": "mpox",
            "influenza": "influenza"
        }

    def fetch_indicators(self):
        url = self.base_url + "Indicator"
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json().get("value", [])
            
            indicators = {}
            for target_disease, keyword in self.disease_mapping.items():
                if target_disease == "malaria":
                    indicators[target_disease] = "MALARIA_EST_CASES"
                    continue
                if target_disease == "influenza":
                    indicators[target_disease] = "WHS3_51"
                    continue
                    
                matches = [x for x in data if keyword in x.get('IndicatorName', '').lower()]
                
                bad_words = ['deaths', 'mortality', 'coverage', 'fatality', 'rate', 'percentage', '%', 'vaccination', 'prevalence', 'carrier', 'living with', 'success rate', 'screening']
                valid = [x for x in matches if not any(bad in x.get('IndicatorName', '').lower() for bad in bad_words)]
                
                good_words = ['cases', 'incidence', 'infections', 'number']
                best = [x for x in valid if any(good in x.get('IndicatorName', '').lower() for good in good_words)]
                
                if best:
                    indicators[target_disease] = best[0]['IndicatorCode']
                elif valid:
                    indicators[target_disease] = valid[0]['IndicatorCode']
                elif matches:
                    indicators[target_disease] = matches[0]['IndicatorCode']
                    
            return indicators
        except Exception as e:
            print(f"Error fetching WHO GHO indicators: {e}")
            return {}

    def fetch_countries(self):
        url = self.base_url + "DIMENSION/COUNTRY/DimensionValues"
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json().get("value", [])
            
            country_map = {}
            for c in data:
                code = c.get("Code")
                title = c.get("Title")
                if code and title:
                    country_map[code] = title
            return country_map
        except Exception as e:
            print(f"Error fetching WHO GHO countries: {e}")
            return {}

    def run(self):
        indicators = self.fetch_indicators()
        countries_map = self.fetch_countries()
        
        if not indicators or not countries_map:
            print("Failed to initialize WHO GHO mapping. Aborting.")
            return

        total_inserted = 0

        for disease, indicator_code in indicators.items():
            if not indicator_code:
                print(f"Skipping {disease}, no WHO GHO indicator found.")
                continue
                
            url = self.base_url + indicator_code
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                data = r.json().get("value", [])
                
                country_data = {}
                for record in data:
                    country_code = record.get("SpatialDim")
                    year = record.get("TimeDim")
                    value = record.get("NumericValue") or record.get("Value")
                    
                    if not country_code or not year or value is None:
                        continue
                        
                    try:
                        if isinstance(value, str):
                            value = value.split(' ')[0].replace(',', '').replace('<', '').strip()
                        case_count = int(float(value))
                    except ValueError:
                        continue

                    who_country_name = countries_map.get(country_code)
                    if not who_country_name:
                        continue
                        
                    canonical_country = _normalize_country(who_country_name)
                    if not canonical_country:
                        continue

                    existing = country_data.get(canonical_country)
                    if not existing or existing['year'] < year:
                        country_data[canonical_country] = {
                            "case_count": case_count,
                            "year": year
                        }

                count = 0
                for country, stats in country_data.items():
                    doc = {
                        "disease": disease.lower(),
                        "country": country,
                        "case_count": stats["case_count"],
                        "year": stats["year"],
                        "source": "WHO GHO",
                        "fetched_at": datetime.now(timezone.utc)
                    }
                    self.db["disease_stats"].update_one(
                        {"disease": disease.lower(), "country": country},
                        {"$set": doc},
                        upsert=True
                    )
                    count += 1
                
                print(f"Fetched {count} records for {disease}")
                total_inserted += count
                
            except Exception as e:
                print(f"Error fetching data for {disease} ({indicator_code}): {e}")

        print(f"WHOGHOSpider complete: {total_inserted} total records")

if __name__ == "__main__":
    spider = WHOGHOSpider()
    spider.run()
