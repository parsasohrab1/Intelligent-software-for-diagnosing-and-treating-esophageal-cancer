import requests
import json

try:
    print("Calling seed-data endpoint...")
    r = requests.post('http://127.0.0.1:8001/api/v1/patients/seed-data', timeout=120)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)}")
    
    # Also check patients
    print("\nChecking patients endpoint...")
    r2 = requests.get('http://127.0.0.1:8001/api/v1/patients', timeout=10)
    print(f"Status Code: {r2.status_code}")
    if r2.status_code == 200:
        data = r2.json()
        count = len(data) if isinstance(data, list) else 0
        print(f"Patients count: {count}")
    else:
        print(f"Error: {r2.text}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
