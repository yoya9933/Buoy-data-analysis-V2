import schedule
import time
import requests
import json
import csv
import os
from os import makedirs, path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional

# 加載 .env 文件
load_dotenv()

OUTPUT = "dataset/buoy/"
DATA_SOURCE = os.getenv("DATA_SOURCE", "nodass").strip().lower()
NODASS_BASE_URL = "https://nodass.namr.gov.tw"
CWA_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0075-002"
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

CWA_WEATHER_ELEMENTS = [
    "TideHeight",
    "TideLevel",
    "WaveHeight",
    "WaveDirection",
    "WaveDirectionDescription",
    "WavePeriod",
    "SeaTemperature",
    "Temperature",
    "StationPressure",
    "PrimaryAnemometer",
    "SeaCurrents",
]


def build_headers(source: str):
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "User-Agent": "BuoyDataFetcher/1.0",
    }
    if source == "nodass":
        api_key = os.getenv("NAMR_API_KEY", "").strip()
        if api_key:
            # Keep both common formats to maximize compatibility with gateway rules.
            headers["Authorization"] = f"Bearer {api_key}"
            headers["X-API-Key"] = api_key
    return headers


def build_params(source: str, params: Optional[dict] = None):
    query = dict(params or {})
    if source == "cwa":
        api_key = os.getenv("CWA_AUTHORIZATION", os.getenv("CWA_API_KEY", "")).strip()
        if api_key:
            query["Authorization"] = api_key
    return query


def request_json(url: str, source: str = "nodass", params: Optional[dict] = None):
    last_error = None
    headers = build_headers(source)
    query = build_params(source, params)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, params=query, timeout=REQUEST_TIMEOUT)
            if response.status_code == 403:
                detail = ""
                try:
                    detail = response.json().get("error", {}).get("detail", "")
                except ValueError:
                    detail = response.text[:200]
                env_hint = "NAMR_API_KEY" if source == "nodass" else "CWA_AUTHORIZATION"
                raise requests.HTTPError(
                    f"403 Forbidden. {detail} If this API now requires credentials, set env var {env_hint}.",
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


def iter_time_windows(start_time: datetime, end_time: datetime, max_hours: int = 24):
    current = start_time
    while current < end_time:
        window_end = min(current + timedelta(hours=max_hours), end_time)
        yield current, window_end
        current = window_end


def normalize_key(value):
    return "".join(ch.lower() for ch in str(value) if ch.isalnum())


def flatten_payload(payload, parent_key="", flat=None):
    if flat is None:
        flat = {}

    if isinstance(payload, dict):
        for key, value in payload.items():
            next_key = f"{parent_key}.{key}" if parent_key else str(key)
            flatten_payload(value, next_key, flat)
    elif isinstance(payload, list):
        if payload and isinstance(payload[0], dict):
            for index, item in enumerate(payload):
                flatten_payload(item, f"{parent_key}[{index}]", flat)
        else:
            flat[parent_key] = payload
    else:
        flat[parent_key] = payload

    return flat


def lookup_value(flat_payload, candidates):
    normalized_items = [(normalize_key(key), value) for key, value in flat_payload.items()]
    for candidate in candidates:
        normalized_candidate = normalize_key(candidate)
        for normalized_key, value in normalized_items:
            if normalized_candidate == normalized_key or normalized_candidate in normalized_key or normalized_key in normalized_candidate:
                if value not in (None, ""):
                    return value
    return ""


def stringify_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def extract_cwa_rows(payload, station_id: str):
    """
    Extract rows from CWA API response.
    CWA structure: Records.SeaSurfaceObs.Location[].StationObsTimes.StationObsTime[].WeatherElements
    """
    rows = []
    
    try:
        records = payload.get("Records", {})
        sea_surface = records.get("SeaSurfaceObs", {})
        locations = sea_surface.get("Location", [])
        
        if not isinstance(locations, list):
            locations = [locations]
        
        for location in locations:
            # Extract station ID from Location.Station.StationID
            station_info = location.get("Station", {})
            actual_station_id = station_info.get("StationID", station_id)
            
            # Get observation times for this location
            station_obs_times = location.get("StationObsTimes", {})
            obs_time_list = station_obs_times.get("StationObsTime", [])
            
            if not isinstance(obs_time_list, list):
                obs_time_list = [obs_time_list]
            
            for obs_time in obs_time_list:
                datetime_str = obs_time.get("DateTime", "")
                weather_elements = obs_time.get("WeatherElements", {})
                
                if datetime_str:
                    row = {key: "" for key in CSV_COLUMNS}
                    row["StationID"] = str(actual_station_id)
                    row["time"] = datetime_str
                    
                    # Extract weather data from WeatherElements
                    row["Tide_Height"] = stringify_value(weather_elements.get("TideHeight", ""))
                    row["Wave_Height_Significant"] = stringify_value(weather_elements.get("WaveHeight", ""))
                    row["Wave_Main_Direction"] = stringify_value(weather_elements.get("WaveDirection", ""))
                    row["Wave_Mean_Period"] = stringify_value(weather_elements.get("WavePeriod", ""))
                    row["Sea_Temperature"] = stringify_value(weather_elements.get("SeaTemperature", ""))
                    row["Air_Temperature"] = stringify_value(weather_elements.get("Temperature", ""))
                    row["Air_Pressure"] = stringify_value(weather_elements.get("StationPressure", ""))
                    
                    # Extract wind data from PrimaryAnemometer if present
                    primary_anem = weather_elements.get("PrimaryAnemometer", {})
                    if isinstance(primary_anem, dict):
                        row["Wind_Speed"] = stringify_value(primary_anem.get("WindSpeed", ""))
                        row["Wind_Gust_Speed"] = stringify_value(primary_anem.get("MaximumWindSpeed", ""))
                        row["Wind_Direction"] = stringify_value(primary_anem.get("WindDirection", ""))
                    
                    # Extract current data if present
                    row["Current_Speed"] = stringify_value(weather_elements.get("CurrentSpeed", ""))
                    row["Current_Direction"] = stringify_value(weather_elements.get("CurrentDirection", ""))
                    row["Current_Speed_knot"] = stringify_value(weather_elements.get("CurrentSpeedInKnots", ""))
                    
                    rows.append(row)
    
    except Exception as e:
        print(f"❌ Error parsing CWA response: {e}")
    
    return rows


def fetch_data(device_id: str):
    now = datetime.now()
    start_time = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
    end_time = now.strftime("%Y-%m-%dT%H:%M:%S")

    if DATA_SOURCE == "cwa":
        all_rows = []
        for window_start, window_end in iter_time_windows(now - timedelta(days=2), now, 24):
            params = {
                "timeFrom": window_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeTo": window_end.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            print(f"[{now}] Requesting CWA window: {params['timeFrom']} -> {params['timeTo']}")
            try:
                data = request_json(CWA_BASE_URL, source="cwa", params=params)
                all_rows.extend(extract_cwa_rows(data, device_id))
            except Exception as e:
                print(f"❌ Failed to fetch CWA data: {e}")

        if all_rows:
            parse_to_csv(all_rows, device_id)
            print("✅ Fetch complete")
        else:
            print(f"⚠️ No data returned for CWA")
        return

    # Format the URL with query parameters
    api_url = f"{NODASS_BASE_URL}/noapi/namr/v1/obs/{device_id}/data?date1={start_time}&date2={end_time}"

    print(f"[{now}] Requesting: {api_url}")
    try:
        data = request_json(api_url, source="nodass")
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
        if DATA_SOURCE == "cwa":
            # Try to get all available stations from a single CWA query
            print("🔍 Fetching CWA stations from API...")
            try:
                params = {
                    "timeFrom": (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeTo": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                }
                response_data = request_json(CWA_BASE_URL, source="cwa", params=params)
                
                # Extract unique station IDs from API response
                station_ids = set()
                records = response_data.get("Records", {})
                sea_surface = records.get("SeaSurfaceObs", {})
                locations = sea_surface.get("Location", [])
                
                if not isinstance(locations, list):
                    locations = [locations]
                
                for location in locations:
                    station_info = location.get("Station", {})
                    station_id = station_info.get("StationID")
                    if station_id:
                        station_ids.add(str(station_id))
                
                if station_ids:
                    devices_data = [
                        {"StationID": sid, "Title": sid}
                        for sid in sorted(station_ids)
                    ]
                    print(f"✅ Found {len(devices_data)} CWA stations: {[d['StationID'] for d in devices_data]}")
                else:
                    raise ValueError("No stations found in CWA response")
            
            except Exception as api_error:
                # Fall back to CWA_STATION_IDS env var
                print(f"⚠️ Could not fetch stations from API: {api_error}")
                station_ids = os.getenv("CWA_STATION_IDS", "").strip()
                if station_ids:
                    devices_data = [
                        {"StationID": station_id.strip(), "Title": station_id.strip()}
                        for station_id in station_ids.split(",")
                        if station_id.strip()
                    ]
                    print(f"📝 Using CWA_STATION_IDS env var: {[d['StationID'] for d in devices_data]}")
                elif path.exists(devices_output):
                    with open(devices_output, "r", encoding="utf-8") as f:
                        devices_data = json.load(f)
                    print(f"📝 Using existing devices.json: {[d['StationID'] for d in devices_data]}")
                else:
                    raise RuntimeError("CWA 模式需要先設定 CWA_STATION_IDS 環境變數或 dataset/buoy/devices.json")
        else:
            # Write a devices data file
            api_url = f"{NODASS_BASE_URL}/noapi/query/OBS?StationChargeID[]=OCA&StationChargeID[]=CWA&StationChargeID[]=WRA&StationChargeID[]=IHMT&StationChargeID[]=NAMR"
            print(f"Fetching devices data from {api_url}")
            response_data = request_json(api_url, source="nodass")

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
            devices_data = json.load(f)

    device_ids = [device["StationID"] for device in devices_data]
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
