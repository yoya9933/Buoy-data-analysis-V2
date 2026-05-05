#!/usr/bin/env python3
"""Fetch CWA station metadata for naming"""
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

CWA_AUTH = os.getenv("CWA_AUTHORIZATION", "")
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0075-002"

def fetch_station_metadata():
    """Get station names and locations from CWA"""
    
    # Get a sample of recent data with all stations
    now = datetime.utcnow()
    params = {
        "timeFrom": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
        "timeTo": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "Authorization": CWA_AUTH,
    }
    
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        data = resp.json()
        
        # Extract station metadata
        station_map = {}
        records = data.get("Records", {})
        sea_surface = records.get("SeaSurfaceObs", {})
        locations = sea_surface.get("Location", [])
        
        if not isinstance(locations, list):
            locations = [locations]
        
        for location in locations:
            station_info = location.get("Station", {})
            station_id = station_info.get("StationID")
            station_name = station_info.get("StationName")
            
            if station_id and station_name:
                station_map[station_id] = station_name
                print(f"{station_id:15} -> {station_name}")
        
        return station_map
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

if __name__ == "__main__":
    print("🔍 Fetching CWA station metadata...")
    metadata = fetch_station_metadata()
    
    # Save to file for reference
    with open("station_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Found {len(metadata)} stations")
    print("📝 Saved to station_metadata.json")
