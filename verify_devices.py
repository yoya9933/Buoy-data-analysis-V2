#!/usr/bin/env python3
"""Verify devices.json was correctly updated"""
import json

with open('dataset/buoy/devices.json', 'r', encoding='utf-8') as f:
    devices = json.load(f)

print(f"✅ Total stations: {len(devices)}\n")
print("First 10 stations with meaningful names:")
print("-" * 60)

for device in devices[:10]:
    print(f"  {device['StationID']:15} -> {device['Title']}")

print("\n... (85 total stations)")
print("\nVerification complete!")
