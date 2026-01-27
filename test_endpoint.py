import requests
import time

print("Waiting for backend to start...")
time.sleep(8)

try:
    print("\nTesting /api/v1/patients/dashboard...")
    r = requests.get('http://127.0.0.1:8001/api/v1/patients/dashboard', timeout=15)
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        count = len(data) if isinstance(data, list) else 0
        print(f"✅ Success! Returned {count} patients")
        if count > 0:
            print(f"   First patient: {data[0].get('patient_id', 'N/A')}")
    else:
        print(f"❌ Error: {r.status_code}")
        print(f"   Response: {r.text[:500]}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend. Is it running?")
except Exception as e:
    print(f"❌ Error: {e}")
