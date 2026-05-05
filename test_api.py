#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NODASS / CWA API 連接測試腳本
用於驗證 API 密鑰和連接狀態
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

DATA_SOURCE = os.getenv("DATA_SOURCE", "nodass").strip().lower()
NODASS_BASE_URL = "https://nodass.namr.gov.tw"
CWA_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0075-002"


def build_headers():
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "User-Agent": "BuoyDataFetcher/1.0",
    }

    if DATA_SOURCE == "nodass":
        api_key = os.getenv("NAMR_API_KEY", "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            headers["X-API-Key"] = api_key

    return headers


def build_query_params(params=None):
    query = dict(params or {})
    if DATA_SOURCE == "cwa":
        api_key = os.getenv("CWA_AUTHORIZATION", os.getenv("CWA_API_KEY", "")).strip()
        if api_key:
            query["Authorization"] = api_key
    return query


def load_station_ids():
    if DATA_SOURCE == "cwa":
        station_ids = os.getenv("CWA_STATION_IDS", "").strip()
        if station_ids:
            return [station_id.strip() for station_id in station_ids.split(",") if station_id.strip()]

    devices_path = os.path.join("dataset", "buoy", "devices.json")
    if os.path.exists(devices_path):
        try:
            with open(devices_path, "r", encoding="utf-8") as f:
                devices = json.load(f)
            return [device.get("StationID") for device in devices if device.get("StationID")]
        except Exception:
            pass
    return []

def test_api_connection():
    """測試 API 連接"""
    
    print("=" * 60)
    print(f"🌊 {DATA_SOURCE.upper()} API 連接測試")
    print("=" * 60)
    
    headers = build_headers()

    if DATA_SOURCE == "nodass":
        api_key = os.getenv("NAMR_API_KEY", "").strip()
        print("\n1️⃣  檢查 API 密鑰...")
        if not api_key:
            print("❌ API 密鑰未設置")
            print("💡 請在 .env 文件中設置 NAMR_API_KEY")
            return False
        print(f"✅ API 密鑰已設置: {api_key[:10]}...{'*' * 10}")

        print("\n2️⃣  測試查詢測站列表...")
        try:
            devices_url = f"{NODASS_BASE_URL}/noapi/query/OBS?StationChargeID[]=OCA&StationChargeID[]=CWA&StationChargeID[]=WRA&StationChargeID[]=IHMT&StationChargeID[]=NAMR"
            response = requests.get(devices_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                buoy_stations = [d for d in data if d.get("StationTypeID") == "FB"]
                print(f"✅ 成功取得 {len(data)} 個測站，其中 {len(buoy_stations)} 個浮標")
                print("\n   浮標測站列表:")
                for station in buoy_stations[:5]:
                    print(f"   - {station.get('StationID')}: {station.get('Title', 'N/A')}")
                if len(buoy_stations) > 5:
                    print(f"   ... 還有 {len(buoy_stations) - 5} 個測站")
            else:
                print(f"❌ API 返回錯誤: {response.status_code}")
                print(f"   原因: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
            return False

        print("\n3️⃣  測試查詢測站數據...")
        if buoy_stations:
            test_station = buoy_stations[0]["StationID"]
            print(f"   使用測站: {test_station}")
            try:
                now = datetime.now()
                start_time = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
                end_time = now.strftime("%Y-%m-%dT%H:%M:%S")
                data_url = f"{NODASS_BASE_URL}/noapi/namr/v1/obs/{test_station}/data?date1={start_time}&date2={end_time}"
                response = requests.get(data_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"✅ 成功取得 {len(data)} 筆數據記錄")
                        if data:
                            sample = data[0]
                            print("\n   數據樣本 (第一筆):")
                            print(f"   - 時間: {sample.get('time', 'N/A')}")
                            print(f"   - 風速: {sample.get('Wind_Speed', 'N/A')} m/s")
                            print(f"   - 示性波高: {sample.get('Wave_Height_Significant', 'N/A')} m")
                            print(f"   - 海面溫度: {sample.get('Sea_Temperature', 'N/A')} °C")
                    else:
                        print(f"⚠️  返回數據格式異常: {type(data)}")
                else:
                    print(f"❌ API 返回錯誤: {response.status_code}")
                    print(f"   原因: {response.text[:200]}")
                    if response.status_code == 404:
                        print("   💡 可能該測站在指定時間範圍內無數據")
                    return False
            except Exception as e:
                print(f"❌ 查詢失敗: {e}")
                return False
    else:
        api_key = os.getenv("CWA_AUTHORIZATION", os.getenv("CWA_API_KEY", "")).strip()
        print("\n1️⃣  檢查 API 授權碼...")
        if not api_key:
            print("❌ API 授權碼未設置")
            print("💡 請在 .env 文件中設置 CWA_AUTHORIZATION")
            return False
        print(f"✅ API 授權碼已設置: {api_key[:10]}...{'*' * 10}")

        station_ids = load_station_ids()
        if not station_ids:
            print("❌ 找不到可測試的 StationID")
            print("💡 請先在 CWA_STATION_IDS 設定測站代碼，或保留 dataset/buoy/devices.json")
            return False

        test_station = station_ids[0]
        print(f"\n2️⃣  使用測站: {test_station}")

        now = datetime.now()
        start_time = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
        end_time = now.strftime("%Y-%m-%dT%H:%M:%S")
        params = {
            "Authorization": api_key,
            "format": "json",
            "StationID": [test_station],
            "WeatherElement": [
                "TideHeight",
                "WaveHeight",
                "WaveDirection",
                "WavePeriod",
                "SeaTemperature",
                "Temperature",
                "StationPressure",
                "PrimaryAnemometer",
                "SeaCurrents",
            ],
            "sort": "DataTime",
            "timeFrom": start_time,
            "timeTo": end_time,
        }

        try:
            response = requests.get(CWA_BASE_URL, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ 成功收到 CWA 回應")
                print(f"   回應型態: {type(data).__name__}")
                if isinstance(data, dict):
                    print(f"   最上層欄位: {', '.join(list(data.keys())[:8])}")
            else:
                print(f"❌ API 返回錯誤: {response.status_code}")
                print(f"   原因: {response.text[:300]}")
                return False
        except Exception as e:
            print(f"❌ 查詢失敗: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ API 連接測試完成！所有測試通過 🎉")
    print("=" * 60)
    print("\n📝 後續步驟:")
    print("   1. 運行 'python fetch.py' 爬取完整數據")
    print("   2. 運行 'streamlit run app.py' 啟動應用")
    print("   3. 在應用中選擇測站進行分析")
    
    return True


if __name__ == "__main__":
    success = test_api_connection()
    exit(0 if success else 1)
