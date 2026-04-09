import schedule
import time
import requests
import json
import csv
import os
from os import makedirs, path
from datetime import datetime, timedelta

OUTPUT = "dataset/buoy/"
CSV_COLUMNS = [
    "StationID",
    "time",
    "Wind_Gust_Speed",
    "Wind_Speed",
    "Wind_Direction",
    "Air_Pressure",
    "Air_Temperature",
    "Sea_Temperature",
    "Wave_Height_Significant",
    "Wave_Mean_Period",
    "Wave_Main_Direction",
    "Wave_Peak_Period",
    "Current_Speed",
    "Current_Speed_Layer",
    "Current_Direction",
    "Current_Direction_Layer",
    "Current_Speed_knot",
    "Tide_Height"
]

CSV_CHINESE_COLUMNS = [
    "測站編號",
    "時間",
    "陣風_風速",
    "風速",
    "風向",
    "氣壓",
    "氣溫",
    "海面溫度",
    "示性波高",
    "平均週期",
    "波向",
    "波浪尖峰週期",
    "流速",
    "分層流速{深度:流速}",
    "流向",
    "分層流向{深度:流向}",
    "流速(節)",
    "潮高"
]

CSV_UNITS = [
    "",
    "UTC+8",
    "m/s",
    "m/s",
    "degree",
    "hPa",
    "C",
    "C",
    "m",
    "sec",
    "degree",
    "sec",
    "m/s",
    "m/s",
    "degree",
    "degree",
    "knot",
    "m"
]

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3


def build_headers():
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "User-Agent": "BuoyDataFetcher/1.0",
    }
    api_key = os.getenv("NAMR_API_KEY", "").strip()
    if api_key:
        # Keep both common formats to maximize compatibility with gateway rules.
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-Key"] = api_key
    return headers


def request_json(url: str):
    last_error = None
    headers = build_headers()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code == 403:
                detail = ""
                try:
                    detail = response.json().get("error", {}).get("detail", "")
                except ValueError:
                    detail = response.text[:200]
                raise requests.HTTPError(
                    f"403 Forbidden. {detail} If this API now requires credentials, set env var NAMR_API_KEY.",
                    response=response,
                )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            print(f"⚠️ Attempt {attempt} failed: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(5)
    raise RuntimeError(f"All retries failed for URL: {url}") from last_error


def fetch_data(device_id: str):
    now = datetime.now()
    start_time = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
    end_time = now.strftime("%Y-%m-%dT%H:%M:%S")

    # Format the URL with query parameters
    API_URL = f"https://nodass.namr.gov.tw/noapi/namr/v1/obs/{device_id}/data?date1={start_time}&date2={end_time}"

    print(f"[{now}] Requesting: {API_URL}")
    try:
        data = request_json(API_URL)
        parse_to_csv(data, device_id)
        print("✅ Fetch complete")
    except Exception as e:
        print(f"❌ Failed to fetch station {device_id}: {e}")


def parse_to_csv(data, device_id):
    if not data:
        print(f"⚠️ No data returned for station {device_id}")
        return

    rows = data if isinstance(data, list) else [data]
    # TODO: The beginning of the month may contain data from the previous month
    filename = f"{datetime.now().strftime('%Y%m')}.csv"
    output = path.join(OUTPUT, device_id, filename)
    makedirs(path.dirname(output), exist_ok=True)

    with open(output, mode="a+", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)

        if file.tell() == 0:
            # Header have 3 lines: Chinese names, English names, and units
            chinese_header = {key: value for key, value in zip(CSV_COLUMNS, CSV_CHINESE_COLUMNS)}
            writer.writerow(chinese_header)

            writer.writeheader()  # Write English header

            header_units = {key: value for key, value in zip(CSV_COLUMNS, CSV_UNITS)}
            writer.writerow(header_units)

        for row in rows:
            filtered = {key: row.get(key, "") for key in CSV_COLUMNS}
            writer.writerow(filtered)
            print(f"📝 Appended row: {filtered}")


def fetch_all_devices():
    makedirs(OUTPUT, exist_ok=True)
    devices_output = path.join(OUTPUT, "devices.json")

    try:
        # Write a devices data file
        API_URL = "https://nodass.namr.gov.tw/noapi/query/OBS?StationChargeID[]=OCA&StationChargeID[]=CWA&StationChargeID[]=WRA&StationChargeID[]=IHMT&StationChargeID[]=NAMR"
        print(f"Fetching devices data from {API_URL}")
        response_data = request_json(API_URL)

        # Filter StationTypeID to only include "FB" (Floating Buoy)
        devices_data = [device for device in response_data if device.get("StationTypeID") == "FB"]
        # Write the devices data to a file (dataset/buoy/devices.json)
        with open(devices_output, "w", encoding="utf-8") as f:
            json.dump(devices_data, f, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Failed to fetch devices data: {e}")
        if not path.exists(devices_output):
            print("⚠️ No local devices data file found. Skip this run.")
            return
        # If the request fails, try to read from the local file
        with open(devices_output, "r", encoding="utf-8") as f:
            response_data = json.load(f)

    device_ids = [device["StationID"] for device in response_data]
    for device_id in device_ids:
        makedirs(path.join(OUTPUT, device_id), exist_ok=True)
        fetch_data(device_id)


if __name__ == "__main__":
    # Schedule every 2 days at 08:00
    # TODO: Maybe every 2 days is too long, consider changing to 1 day
    schedule.every(2).days.at("08:00").do(fetch_all_devices)

    # Run immediately on startup
    fetch_all_devices()
    print("🔄 Scheduler started. Will run every 2 days.")
    while True:
        schedule.run_pending()
        time.sleep(3600)
