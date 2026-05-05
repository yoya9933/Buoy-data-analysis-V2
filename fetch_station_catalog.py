#!/usr/bin/env python3
"""Fetch station info from CWA station list API"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

CWA_AUTH = os.getenv("CWA_AUTHORIZATION", "")

def fetch_from_cwa_catalog():
    """Try different CWA API endpoints for station metadata"""
    
    # Try station catalog API
    endpoints = [
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0075-001",  # Station list
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0061-001",  # Buoy data
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Trying: {endpoint}")
        try:
            params = {"Authorization": CWA_AUTH}
            resp = requests.get(endpoint, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                success = data.get("Success")
                print(f"Success: {success}")
                
                if success:
                    # Print available fields
                    result = data.get("Result", {})
                    fields = result.get("Fields", [])
                    print(f"Fields: {[f.get('Id') for f in fields]}")
                    
                    # Print first record sample
                    records = data.get("Records", {})
                    if records:
                        print(f"Records keys: {list(records.keys())}")
                        first_key = list(records.keys())[0] if records else None
                        if first_key:
                            sample = records[first_key]
                            if isinstance(sample, list) and sample:
                                print(f"\nSample record:\n{json.dumps(sample[0], indent=2, ensure_ascii=False)[:500]}")
                            elif isinstance(sample, dict):
                                print(f"\nSample:\n{json.dumps(sample, indent=2, ensure_ascii=False)[:500]}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fetch_from_cwa_catalog()
