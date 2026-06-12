# 浮標資料分析與航道風險評估平台

這是一個以 Streamlit 建立的海洋浮標資料分析平台。專案目前的核心功能是讀取本機浮標觀測資料，讓使用者選擇測站、海象參數與時間範圍，透過 LSTM 時間序列模型預測未來趨勢，並依設定門檻輔助判讀風險。

目前主要入口：

- `app.py`：Streamlit 主頁與全域初始化。
- `pages/10_🌊_LSTM模型預測(beta).py`：LSTM 模型預測頁面。
- `dataset/buoy/`：浮標資料來源。
- `trained_models/`：已訓練模型、Scaler 與訓練歷史快取。
- `config.json`：資料路徑、參數資訊、風險門檻與中文字型設定。

## 模型是什麼

本專案使用的是 LSTM, Long Short-Term Memory, 長短期記憶神經網路。LSTM 適合處理時間序列資料，因為它會使用前一段時間的觀測值來預測下一個時間點的值。

在這個平台中，LSTM 被用來做單變量預測：

- 一次選擇一個浮標測站。
- 一次選擇一個可預測的數值參數，例如示性波高、風速、流速等。
- 使用該參數過去一段時間的序列，預測未來數個時間點的數值。

模型結構目前為：

1. 輸入層：接收 `look_back` 長度的歷史序列。
2. 第一層 LSTM：可由介面設定單元數，並輸出序列。
3. Dropout：降低過擬合風險。
4. 第二層 LSTM：輸出單一狀態。
5. Dropout。
6. Dense(1)：輸出下一個時間點的預測值。

模型使用 `Adam` optimizer 與 `mean_squared_error` 作為 loss。數值會先透過 `MinMaxScaler` 縮放到 0 到 1，再送入模型訓練；輸出結果會再轉回原始單位。

## 模型怎麼訓練

使用者在介面按下「執行 LSTM 預測」後，系統會依下列流程處理：

1. 讀取資料
   - 從 `config.json` 的 `base_data_path` 讀取浮標資料。
   - 目前預設資料位置是 `dataset/buoy/`。
   - 系統支援測站資料夾格式，也支援單一 CSV 浮標檔案格式。

2. 選取訓練資料
   - 依使用者選擇的測站、參數、開始日期與結束日期篩選資料。
   - 只保留時間欄位與目標參數欄位。

3. 重新取樣
   - 使用者可選擇預測頻率：
     - 小時
     - 日
     - 週
     - 月
     - 年
   - 系統會用 Pandas `resample().mean()` 將原始資料聚合到指定時間尺度。

4. 缺值處理
   - 可選前向填補 `ffill`。
   - 可選後向填補 `bfill`。
   - 可選線性插值 `interpolate`。
   - 可選移除缺值 `dropna`。

5. 平滑處理
   - 可選用移動平均平滑。
   - 平滑視窗大小可在介面調整。

6. 建立時間序列樣本
   - `look_back` 代表模型每次要看幾個歷史時間點。
   - 例如 `look_back = 6` 時，模型會用連續 6 筆資料預測第 7 筆。

7. 切分訓練集與驗證集
   - 依介面中的「驗證集比例」切分。
   - 前段資料作為訓練集，後段資料作為驗證集。
   - 這是時間序列切分，不是隨機切分。

8. 訓練模型
   - 可調整 LSTM 單元數、Epochs、Batch Size、Dropout、驗證集比例與 Early Stopping patience。
   - Early Stopping 監控 `val_loss`，並回復最佳權重。

9. 快取模型
   - 系統會依測站、參數、頻率、日期範圍、模型參數與前處理設定產生 hash。
   - 若相同設定已有模型，會直接從 `trained_models/` 讀取：
     - `lstm_model_<hash>.keras`
     - `lstm_scaler_<hash>.joblib`
     - `lstm_history_<hash>.json`
   - 若沒有快取，才會重新訓練。

## Interface 怎麼用

啟動後進入 Streamlit 介面，左側側欄是主要操作區。

### 1. 啟動系統

建議使用 Python 3.9 到 3.12。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

瀏覽器開啟：

```text
http://localhost:8501
```

### 2. 進入 LSTM 預測頁

在 Streamlit 左側頁面清單選擇：

```text
🌊 LSTM模型預測(beta)
```

### 3. 選擇資料與預測目標

在側欄設定：

- 測站：選擇要分析的浮標站。
- 預測參數：選擇要預測的數值欄位。
- 預測頻率：選擇小時、日、週、月或年。
- 預測期數：設定要往未來預測幾個時間點。
- 訓練開始日期與結束日期：設定模型要使用的歷史資料範圍。

### 4. 設定資料前處理

可調整：

- 缺值處理方式。
- 是否套用平滑。
- 平滑視窗大小。
- 誤差容忍值 epsilon。

epsilon 用於計算自訂準確率：當 `abs(預測值 - 實際值) <= epsilon` 時，該筆會被視為預測正確。

### 5. 設定模型參數

可調整：

- `look_back`：模型回看多少筆歷史資料。
- LSTM 層單元數。
- Epochs。
- Batch Size。
- Dropout 比率。
- 驗證集比例。
- Patience。

資料量不足時，`look_back` 不宜設定太大；資料震盪很大時，可嘗試增加資料時間範圍或使用平滑。

### 6. 執行預測

按下：

```text
執行 LSTM 預測
```

系統會先檢查是否已有相同設定的快取模型。若有，會直接載入；若沒有，會開始訓練新模型。

## 產出的結果怎麼解讀

預測完成後，頁面會顯示數個區塊。

### 訓練資料摘要

這裡會顯示：

- 實際使用的資料起訖時間。
- 資料總時間跨度。
- 重新取樣後的資料筆數。
- 使用的預測頻率。

若資料筆數太少，模型結果可信度會下降。通常需要至少明顯多於 `look_back` 的資料量，才足以訓練與驗證。

### 資料品質摘要

這裡會顯示：

- 總筆數。
- 有效筆數。
- 缺值比例。
- 零值、負值與 IQR 離群值數量。

解讀方式：

- 缺值比例高：預測可能高度依賴填補策略。
- 離群值多：模型可能被極端值影響。
- 負值出現在不應為負的參數中：代表原始資料可能需要清理。

### 模型評估指標

系統會分別顯示訓練集與驗證集結果。

- RMSE：均方根誤差，越低越好。單位與原始參數相同。
- 相關係數 R：越接近 1，代表預測趨勢越接近實際資料；接近 0 代表關聯弱。
- 準確率：以 epsilon 判定的自訂命中率，不是分類模型的 accuracy。

建議解讀：

- 訓練 RMSE 很低，但驗證 RMSE 很高：可能過擬合。
- 訓練 R 高、驗證 R 低：模型記住歷史資料，但泛化能力不足。
- 驗證資料太少時，驗證指標波動會很大，不能單獨作為模型好壞結論。

### 訓練歷史圖

訓練歷史會顯示：

- Loss / Val Loss。
- 訓練與驗證準確率。
- 訓練與驗證相關係數。

解讀方式：

- Val Loss 持續下降：模型仍在學習。
- Val Loss 停滯或上升，而 Loss 持續下降：可能過擬合。
- 指標劇烈震盪：資料量不足、資料噪音高或 batch size / learning dynamics 不穩定。

### 預測趨勢圖

圖中通常包含：

- 實際歷史資料。
- 訓練區間預測。
- 驗證區間預測。
- 未來預測。

解讀方式：

- 未來預測線是模型依最近 `look_back` 筆資料遞迴產生的結果。
- 預測越往後，誤差累積風險越高。
- LSTM 預測反映歷史型態，不代表能預知突發天氣、颱風、儀器異常或外部事件。

### 風險判讀

目前風險門檻主要來自 `config.json`：

```json
"RISK_THRESHOLDS": {
  "Wave_Height_Significant": {
    "warning": 2.5,
    "danger": 4.0
  },
  "Wind_Speed": {
    "warning": 10.0,
    "danger": 17.0
  }
}
```

一般解讀：

- 正常：預測值低於警告門檻。
- 警告：預測值達到或高於 warning。
- 危險：預測值達到或高於 danger。

風險判讀只能作為輔助參考。實際航行與作業決策仍應搭配官方氣象、海象預報、現場規範與人工判斷。

### 可下載輸出

完成後可下載：

- CSV：未來預測資料與風險等級。
- HTML：互動式 Plotly 預測圖。
- TXT：模型設定、訓練摘要與評估報告。
- ZIP：一次打包下載上述檔案。

## 資料與設定

### 資料路徑

目前 `config.json` 設定：

```json
{
  "dataset_path": "dataset/",
  "base_data_path": "dataset/buoy/"
}
```

浮標資料可放在：

```text
dataset/buoy/
```

系統會嘗試讀取：

- 測站資料夾內的 CSV。
- 或 `dataset/buoy/` 下面的單一浮標 CSV。

### 參數設定

`PARAMETER_INFO` 定義可用參數、顯示名稱、單位、型態與資料欄位名稱。只有 `type` 為 `linear` 的數值參數會作為 LSTM 預測候選。

### 模型快取

訓練完成的模型會存到：

```text
trained_models/
```

若要強制重新訓練相同設定，可刪除對應的 `.keras`、`.joblib` 與 `.json` 快取檔，或改變模型參數與日期範圍。

## 專案結構

```text
.
├── app.py
├── config.json
├── requirements.txt
├── dataset/
│   ├── buoy/
│   └── radar/
├── pages/
│   └── 10_🌊_LSTM模型預測(beta).py
├── trained_models/
│   ├── lstm_model_<hash>.keras
│   ├── lstm_scaler_<hash>.joblib
│   └── lstm_history_<hash>.json
├── utils/
│   ├── helpers.py
│   └── radar.py
└── fonts/
```

## 注意事項

- 目前此頁面仍標示為 beta，結果適合用於探索與輔助分析。
- 若原始 CSV 欄位名稱或編碼異常，系統可能無法正確辨識欄位。
- 現有部分程式註解與舊 README 曾出現編碼亂碼；若要長期維護，建議統一使用 UTF-8。
- 風險門檻應依實際航道、船型、作業規範與主管機關標準校正。

## License

本專案使用 MIT License。詳見 `LICENSE`。
