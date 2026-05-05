# 🌊 NODASS / CWA API 數據串接指南

## 快速開始

### 1️⃣ 獲取 API 密鑰

如果你要繼續用原本資料源，請訪問 [NODASS 平台](https://nodass.namr.gov.tw) 並申請 API 密鑰：

```
https://nodass.namr.gov.tw/api-service
```

如果你想使用你剛找到的 CWA 資料集，則需要氣象開放資料平台的授權碼：

```bash
CWA_AUTHORIZATION=你的授權碼
```

### 2️⃣ 配置 API 密鑰

編輯 `.env` 文件並添加您的 API 密鑰：

```bash
# .env 文件
NAMR_API_KEY=your_api_key_here
CWA_AUTHORIZATION=your_cwa_authorization_here
DATA_SOURCE=cwa
FETCH_INTERVAL_HOURS=2
FETCH_DAYS_RANGE=2
```

如果你暫時還是用原本資料源，把 `DATA_SOURCE` 改回 `nodass`。

> ⚠️ **重要**：不要將 `.env` 文件提交到版本控制中！

### 3️⃣ 測試 API 連接

```bash
python test_api.py
```

CWA 端點有一個重要限制：`timeFrom` / `timeTo` 每次最多回傳 24 小時資料。程式會自動把 2 天切成兩段請求。

### 4️⃣ 查看爬取的數據

數據將保存在：
```
dataset/buoy/
├── devices.json          # 測站信息
├── Vector_NAMR_FB_35A0004/
│   └── 202605.csv       # 測站數據
├── Vector_NAMR_FB_35A0005/
│   └── 202605.csv
└── Vector_NAMR_FB_35A0006/
    └── 202605.csv
```

## 可用的浮標測站

| 測站編號 | 測站名稱 | 緯度 | 經度 | 可用數據 |
|---------|--------|------|------|---------|
| Vector_NAMR_FB_35A0004 | 高雄前鎮測站 | 23.24 | 119.66 | 風速、波高、溫度等 |
| Vector_NAMR_FB_35A0005 | 台灣海峽測站 | 23.50 | 119.50 | 風速、波高、溫度等 |
| Vector_NAMR_FB_35A0006 | 巴士海峽測站 | 22.80 | 120.80 | 風速、波高、溫度等 |

如果你改用 CWA 資料集，`StationID` 必須換成 CWA 的站號；可以把站號直接寫進 `CWA_STATION_IDS`，例如：

```bash
CWA_STATION_IDS=STATION_A,STATION_B,STATION_C
```

## API 文檔參考

- 查詢測站資訊 API：
  ```
  https://nodass.namr.gov.tw/noapi/query/OBS?StationChargeID[]=NAMR
  ```

- 查詢測站數據 API（最近2天）：
  ```
  https://nodass.namr.gov.tw/noapi/namr/v1/obs/{station_id}/data?date1=2026-05-03&date2=2026-05-05
  ```

- CWA 海象監測資料 API：
  ```
  https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0075-002?Authorization=你的授權碼&StationID[]=站號&timeFrom=2026-05-03T00:00:00&timeTo=2026-05-04T00:00:00
  ```

## 故障排除

### ❌ 403 Forbidden 錯誤

**原因**：API 密鑰無效或未配置

**解決方案**：
1. 確認 `.env` 文件中有有效的 API 密鑰
2. 檢查 API 密鑰是否已過期
3. 訪問 NODASS 平台重新申請

如果是 CWA，請確認 `CWA_AUTHORIZATION` 與 `CWA_STATION_IDS` 是否正確。

### ❌ 連接超時

**原因**：網絡連接問題

**解決方案**：
1. 檢查網絡連接
2. 增加超時時間（編輯 `fetch.py` 中的 `REQUEST_TIMEOUT`）
3. 檢查防火牆設置

## 手動爬取數據

```bash
# 執行一次完整爬取
python -c "from fetch import fetch_all_devices; fetch_all_devices()"

# 或運行定時任務（每2天爬取一次）
python fetch.py
```

## 在應用中使用數據

1. ✅ 確認 `dataset/buoy/` 中有 CSV 文件
2. ✅ 啟動 Streamlit 應用：
   ```bash
   streamlit run app.py
   ```
3. ✅ 在應用中選擇測站進行分析

---

**需要幫助？** 參考 [NODASS 官方文檔](https://nodass.namr.gov.tw/api-service)
