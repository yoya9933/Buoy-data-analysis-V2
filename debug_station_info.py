#!/usr/bin/env python3
"""Debug CWA API response structure for station info"""
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

CWA_AUTH = os.getenv("CWA_AUTHORIZATION", "")
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0075-002"

def debug_station_info():
    """Inspect all available fields in station response"""
    
    now = datetime.utcnow()
    params = {
        "timeFrom": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
        "timeTo": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "Authorization": CWA_AUTH,
    }
    
    resp = requests.get(BASE_URL, params=params, timeout=15)
    data = resp.json()
    
    records = data.get("Records", {})
    sea_surface = records.get("SeaSurfaceObs", {})
    locations = sea_surface.get("Location", [])
    
    if not isinstance(locations, list):
        locations = [locations]
    
    print(f"Found {len(locations)} locations\n")
    
    # Show details for first 3 stations
    for i, location in enumerate(locations[:3]):
        print(f"\n{'='*60}")
        print(f"Station {i+1}")
        print(f"{'='*60}")
        
        # Print full station structure
        print(json.dumps(location, indent=2, ensure_ascii=False)[:1500])

if __name__ == "__main__":
    debug_station_info()
