#!/usr/bin/env python3
"""Debug CWA API response structure"""
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

CWA_AUTH = os.getenv("CWA_AUTHORIZATION", "")
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0075-002"

def debug_cwa_response():
    """Request CWA data and inspect response structure"""
    
    # Use a 24-hour window (CWA limit)
    now = datetime.utcnow()
    end_time = now
    start_time = now - timedelta(hours=12)
    
    params = {
        "Authorization": CWA_AUTH,
        "timeFrom": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "timeTo": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "stationId": "46704"
    }
    
    print(f"🔍 CWA API Debug")
    print(f"Endpoint: {BASE_URL}")
    print(f"Auth header: {CWA_AUTH[:20]}...")
    print(f"Time window: {params['timeFrom']} -> {params['timeTo']}")
    print(f"StationId: {params['stationId']}")
    print()
    
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        print(f"Status Code: {resp.status_code}")
        print(f"Response Headers: {dict(resp.headers)}")
        print()
        
        data = resp.json()
        print(f"Top-level keys: {list(data.keys())}")
        print()
        
        if "Records" in data:
            print(f"Records type: {type(data['Records'])}")
            print(f"Number of records: {len(data['Records']) if isinstance(data['Records'], list) else 'N/A'}")
            
            if data['Records']:
                first_record = data['Records'][0] if isinstance(data['Records'], list) else data['Records']
                print(f"\n📋 First record keys: {list(first_record.keys()) if isinstance(first_record, dict) else 'N/A'}")
                print(f"📋 First record (formatted):\n{json.dumps(first_record, indent=2, ensure_ascii=False)[:1000]}")
        
        print("\n✅ Full response (first 2000 chars):")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_cwa_response()
