import requests

def test_endpoints():
    base = "http://127.0.0.1:5000/api"
    try:
        print("Testing /api/outbreaks/map...")
        r = requests.get(f"{base}/outbreaks/map", timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json().get("data", [])
            print(f"Items: {len(data)}")
            
        print("\nTesting /api/outbreaks/summary...")
        r = requests.get(f"{base}/outbreaks/summary", timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json().get("data", [])
            print(f"Items: {len(data)}")
            if data: print(f"Top 1: {data[0]['disease']} ({data[0]['total_cases']} cases)")
            
        print("\nTesting /api/diseases/covid-19...")
        r = requests.get(f"{base}/diseases/covid-19", timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json().get("data", {})
            print(f"Severity: {data.get('severity')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoints()
