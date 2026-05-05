#!/usr/bin/env python3
"""Fetch CWA GIS data for station locations"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

CWA_AUTH = os.getenv("CWA_AUTHORIZATION", "")

def fetch_gis_data():
    """Fetch GIS data from CWA that might have station names"""
    
    # CWA usually provides GIS datasets with location information
    gis_endpoints = [
        # Try to get the data resource list first
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore",
        # Direct GIS endpoints
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0020-001",  # Tide station locations
    ]
    
    # First, let's try the general info endpoint
    print("🔍 Fetching available datasets...")
    try:
        resp = requests.get(
            "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0020-001",
            params={"Authorization": CWA_AUTH},
            timeout=10
        )
        data = resp.json()
        print(f"Success: {data.get('Success')}")
        
        if data.get('Success') == 'true':
            records = data.get('Records', {})
            print(f"Available records: {list(records.keys())}")
            
            # Look for location data
            for key, value in records.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"\n📍 {key}:")
                    sample = value[0]
                    print(json.dumps(sample, indent=2, ensure_ascii=False)[:800])
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_gis_data()
