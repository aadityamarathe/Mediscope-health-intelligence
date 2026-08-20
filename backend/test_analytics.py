import requests

r = requests.get("http://127.0.0.1:5000/api/analytics/activity")
if r.status_code == 200:
    print("SUCCESS")
else:
    print(f"FAILED: {r.status_code}")
    print(r.text)
