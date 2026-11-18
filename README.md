# BalikBisita – ML Forecasting Component

LightGBM (Poisson) model that forecasts **hourly patient check-in volume** for the next 24 hours, connected to a live Node-RED simulation dashboard.

---

## Project structure

```
IoT_FinalProject/
├── data/                   ← put ed-hourly-clean.csv here
│   ├── ed-hourly-clean.csv
│   ├── features_train.parquet
│   ├── features_val.parquet
│   └── features_test.parquet
├── models/
│   └── lgbm_model.joblib   ← saved after training
├── notebooks/
│   └── 01_eda.py           ← exploratory data analysis
├── nodered/
│   └── flow.json           ← import this into Node-RED
├── outputs/                ← plots & evaluation CSVs
├── src/
│   ├── prepare_data.py     ← feature engineering + train/val/test split
│   ├── train_model.py      ← LightGBM training with grid search
│   ├── evaluate_model.py   ← MAE, RMSE, peak-hour, skill, high-load metrics
│   └── predict_service.py  ← Flask REST API (:5000/predict)
├── venv/                   ← Python virtual environment
└── requirements.txt
```

---

## Step-by-step usage

### 1 – Activate the virtual environment
```
.\venv\Scripts\Activate.ps1
```
*(PowerShell)*  or  `venv\Scripts\activate.bat`  *(CMD)*

### 2 – Place the dataset
Copy `ed-hourly-clean.csv` into the `data/` folder.

### 3 – Run EDA (optional but recommended)
```
python notebooks\01_eda.py
```
Plots are saved to `outputs/`.

### 4 – Prepare features
```
python src\prepare_data.py
```
Creates `data/features_train.parquet`, `features_val.parquet`, `features_test.parquet`.

### 5 – Train the model
```
python src\train_model.py
```
Runs a grid search and saves the best model to `models/lgbm_model.joblib`.

### 6 – Evaluate the model
```
python src\evaluate_model.py
```
Prints MAE, RMSE, peak-hour MAE, skill score, and high-load precision/recall/F1.
Saves plots to `outputs/`.

### 7 – Start the Flask prediction service
```
python src\predict_service.py
```
Runs on `http://localhost:5000`.  Test with:
```
curl -X GET http://localhost:5000/health
```

### 8 – Start Node-RED
Open a **new terminal** and run:
```
node-red
```
Then open `http://localhost:1880` in your browser.

### 9 – Import the Node-RED flow
1. Click the ☰ menu → **Import**
2. Choose **select a file to import**
3. Select `nodered/flow.json`
4. Click **Import**, then **Deploy**

### 10 – Open the dashboard
Go to `http://localhost:1880/ui`

The flow will simulate a check-in every 10 seconds and call `/predict` to show the 24-hour forecast bar chart.

---

## API reference

### POST http://localhost:5000/predict
```json
{
  "date": "2017-03-15",
  "history": [
    {"timestamp": "2017-03-01T00:00:00", "count": 4},
    {"timestamp": "2017-03-01T01:00:00", "count": 2},
    "..."
  ]
}
```
Returns:
```json
{
  "date": "2017-03-15",
  "forecasts": [
    {"hour": 0, "predicted_count": 3.4},
    "..."
  ]
}
```

---

## Features used by the model

| Feature | Description |
|---|---|
| `hour` | Hour of day (0–23) |
| `day_of_week` | 0=Monday … 6=Sunday |
| `is_weekend` | 1 if Sat/Sun |
| `month` | Month (1–12) |
| `is_holiday` | 1 if PH public holiday |
| `lag_24h` | Count 24 h ago |
| `lag_48h` | Count 48 h ago |
| `lag_168h` | Count 1 week ago |
| `lag_336h` | Count 2 weeks ago |
| `mean_same_hour_4wk` | Avg same hour over previous 4 weeks |
| `prev_day_total` | Total count from the previous calendar day |
