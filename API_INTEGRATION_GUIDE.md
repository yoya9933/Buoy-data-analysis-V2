# 🌊 API 數據集成完整指南

## 現狀

您已經有：
- ✅ 完整的 `fetch.py` 數據爬取腳本
- ✅ 3 個浮標測站的示例數據（2026-05-03 至 2026-05-05）
- ✅ `.env` 配置文件支持
- ✅ `test_api.py` API 連接測試工具

## 下一步：集成真實 API 數據

### 1. 申請 NAMR API 密鑰

訪問：https://nodass.namr.gov.tw

填寫表單並申請 API 密鑰。完成後您會收到類似下面的密鑰：

```
NAMR_API_KEY = abc123def456ghi789jkl
```

### 2. 配置 .env 文件

編輯 `.env` 文件：

```bash
# 您的 NAMR API 密鑰
NAMR_API_KEY=abc123def456ghi789jkl

# 可選配置
FETCH_INTERVAL_HOURS=2
FETCH_DAYS_RANGE=2
```

### 3. 測試 API 連接

```bash
python test_api.py
```

您應該會看到：
```
✅ API 密鑰已設置
✅ 成功取得 XX 個測站，其中 XX 個浮標
✅ 成功取得 XXX 筆數據記錄
✅ API 連接測試完成！所有測試通過 🎉
```

### 4. 爬取完整數據

一次性爬取：
```bash
python fetch.py
```

自動定時爬取（每 2 天一次）：
```bash
python fetch.py &
```

### 5. 驗證數據

檢查 `dataset/buoy/` 目錄：

```
dataset/buoy/
├── devices.json          # 自動下載的測站信息
├── Vector_NAMR_FB_35A0004/
│   ├── 202605.csv       # 5月數據
│   ├── 202604.csv       # 4月數據
│   └── ...
├── Vector_NAMR_FB_35A0005/
│   └── ...
└── Vector_NAMR_FB_35A0006/
    └── ...
```

### 6. 在應用中查看數據

重新啟動應用，應用會自動加載新數據：

```bash
streamlit run app.py
```

## 可用的浮標測站

NODASS 平台提供的所有浮標測站都會自動下載。常見的包括：

- **台灣西部沿海**：高雄、新竹、宜蘭
- **台灣東部**：花蓮、台東  
- **外島**：澎湖、蘭嶼、綠島
- **台灣海峽**：中央區域
- **南部海域**：巴士海峽

## 數據欄位說明

每個數據記錄包含：

| 欄位名稱 | 單位 | 說明 |
|--------|------|------|
| Wind_Speed | m/s | 風速 |
| Wind_Gust_Speed | m/s | 陣風速 |
| Wind_Direction | ° | 風向 |
| Wave_Height_Significant | m | 示性波高 |
| Wave_Mean_Period | sec | 平均波週期 |
| Wave_Peak_Period | sec | 波浪尖峰週期 |
| Wave_Main_Direction | ° | 波向 |
| Current_Speed | m/s | 流速 |
| Current_Direction | ° | 流向 |
| Air_Temperature | °C | 氣溫 |
| Sea_Temperature | °C | 海面溫度 |
| Air_Pressure | hPa | 氣壓 |

## 常見問題

### Q: 如何更改爬取頻率？

編輯 `fetch.py` 的最後一行：

```python
# 原始：每 2 天爬取一次
schedule.every(2).days.at("08:00").do(fetch_all_devices)

# 修改為每 1 天爬取一次
schedule.every(1).days.at("08:00").do(fetch_all_devices)

# 修改為每 1 小時爬取一次
schedule.every(1).hours.do(fetch_all_devices)
```

### Q: 如何爬取特定測站的數據？

編輯 `fetch.py` 中的 `fetch_all_devices()` 函數，添加過濾邏輯：

```python
def fetch_all_devices():
    # ... 前面的代碼 ...
    
    device_ids = [d["StationID"] for d in response_data 
                  if d.get("StationID") in ["Vector_NAMR_FB_35A0004", "Vector_NAMR_FB_35A0005"]]
    
    for device_id in device_ids:
        # ...
```

### Q: 如何處理 API 速率限制？

在 `fetch.py` 中調整重試延遲：

```python
REQUEST_TIMEOUT = 15      # 超時時間（秒）
MAX_RETRIES = 3          # 重試次數
time.sleep(10)           # 重試之間的延遲（秒）
```

### Q: 如何备份數據？

```bash
# 壓縮打包所有數據
tar -czf buoy_data_backup.tar.gz dataset/buoy/
```

## 監控日誌

`fetch.py` 運行時會輸出詳細日誌：

```
[2026-05-05 15:17:24] Requesting: https://nodass.namr.gov.tw/...
✅ Fetch complete
📝 Appended row: {'StationID': '...', 'time': '...', ...}
```

監控爬取進度：

```bash
# 在另一個終端查看日誌
tail -f fetch.log
```

---

✨ **準備好開始了嗎？** 現在就申請 API 密鑰，配置 `.env` 文件，運行 `test_api.py` 進行測試吧！
