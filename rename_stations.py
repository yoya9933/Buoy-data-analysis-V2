#!/usr/bin/env python3
"""Rename buoy folders and update devices.json"""
import json
import os
import shutil
from pathlib import Path

# Load station name mappings
with open("station_names_mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

# Load current devices.json
with open("dataset/buoy/devices.json", "r", encoding="utf-8") as f:
    devices = json.load(f)

# Update devices with meaningful names
updated_devices = []
for device in devices:
    station_id = device["StationID"]
    new_title = mapping.get(station_id, station_id)  # Use mapping or fallback to code
    
    updated_device = {
        "StationID": station_id,
        "Title": new_title
    }
    updated_devices.append(updated_device)
    
    print(f"✏️  {station_id:15} -> {new_title}")

# Save updated devices.json
with open("dataset/buoy/devices.json", "w", encoding="utf-8") as f:
    json.dump(updated_devices, f, ensure_ascii=False, indent=2)

print("\n✅ Updated dataset/buoy/devices.json")

# Rename folders
buoy_dir = Path("dataset/buoy")
for device in updated_devices:
    old_path = buoy_dir / device["StationID"]
    new_path = buoy_dir / device["Title"]
    
    if old_path.exists() and old_path != new_path:
        try:
            # Rename folder
            shutil.move(str(old_path), str(new_path))
            print(f"📁 Renamed: {device['StationID']} -> {device['Title']}")
        except Exception as e:
            print(f"⚠️  Could not rename {device['StationID']}: {e}")
    elif new_path.exists():
        print(f"ℹ️  {device['Title']} already exists")

print("\n✅ Folder renaming complete!")
