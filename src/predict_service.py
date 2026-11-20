"""
predict_service.py
------------------
Flask micro-service that serves 24-hour-ahead forecasts.

Endpoints:
  POST /predict
    Body (JSON):
      {
        "date": "YYYY-MM-DD",          # the TARGET date to forecast
        "history": [                   # last 14 days of hourly counts (336 values)
          {"timestamp": "YYYY-MM-DDTHH:00:00", "count": <int>},
          ...
        ]
      }
    Response (JSON):
      {
        "date": "YYYY-MM-DD",
        "forecasts": [
          {"hour": 0, "predicted_count": 3.2},
          ...
          {"hour": 23, "predicted_count": 7.1}
        ]
      }

  GET /health   →  {"status": "ok"}

Usage:
  python src/predict_service.py
  # or with the venv:
  .\\venv\\Scripts\\python src\\predict_service.py
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify

ROOT   = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "lgbm_model.joblib"

app = Flask(__name__)

# ── Load model once at startup ────────────────────────────────────────────────
print(f"Loading model from {MODEL_PATH} …")
artifact = joblib.load(MODEL_PATH)
MODEL    = artifact["model"]
FEATURES = artifact["features"]
print("Model loaded.")

# ── Philippine public holidays (same list as in prepare_data.py) ─────────────
PH_HOLIDAYS = {
    "2014-01-01","2014-04-09","2014-04-17","2014-04-18","2014-05-01",
    "2014-06-12","2014-08-25","2014-11-01","2014-11-30","2014-12-25",
    "2014-12-30","2014-12-31","2015-01-01","2015-04-02","2015-04-03",
    "2015-05-01","2015-06-12","2015-08-31","2015-11-01","2015-11-30",
    "2015-12-25","2015-12-30","2015-12-31","2016-01-01","2016-03-24",
    "2016-03-25","2016-04-09","2016-05-01","2016-06-12","2016-08-29",
    "2016-11-01","2016-11-30","2016-12-25","2016-12-30","2016-12-31",
    "2017-01-01","2017-04-13","2017-04-14","2017-04-15","2017-05-01",
    "2017-06-12","2017-08-28","2017-11-01","2017-11-30","2017-12-25",
    "2017-12-30","2017-12-31",
}


def build_feature_row(target_ts: pd.Timestamp, history: pd.Series) -> dict:
    """
    Build one feature row for a single target timestamp.
    history: pd.Series indexed by hourly timestamps, values = counts.
    """
    date_str = target_ts.normalize().strftime("%Y-%m-%d")
    row = {
        "hour"              : target_ts.hour,
        "day_of_week"       : target_ts.day_of_week,
        "is_weekend"        : int(target_ts.day_of_week >= 5),
        "month"             : target_ts.month,
        "is_holiday"        : int(date_str in PH_HOLIDAYS),
        "lag_24h"           : _lag(history, target_ts, 24),
        "lag_48h"           : _lag(history, target_ts, 48),
        "lag_168h"          : _lag(history, target_ts, 168),
        "lag_336h"          : _lag(history, target_ts, 336),
        "mean_same_hour_4wk": _rolling_same_hour(history, target_ts),
        "prev_day_total"    : _prev_day_total(history, target_ts),
    }
    return row


def _lag(history: pd.Series, ts: pd.Timestamp, hours: int):
    lag_ts = ts - pd.Timedelta(hours=hours)
    return float(history.get(lag_ts, history.mean()))


def _rolling_same_hour(history: pd.Series, ts: pd.Timestamp):
    """Mean of same-hour counts over the previous 4 weeks."""
    vals = []
    for w in range(1, 5):
        lag_ts = ts - pd.Timedelta(weeks=w)
        if lag_ts in history.index:
            vals.append(history[lag_ts])
    return float(np.mean(vals)) if vals else float(history.mean())


def _prev_day_total(history: pd.Series, ts: pd.Timestamp):
    """Sum of counts for the previous calendar day."""
    prev_day_start = (ts - pd.Timedelta(days=1)).normalize()
    prev_day_end   = ts.normalize()
    mask = (history.index >= prev_day_start) & (history.index < prev_day_end)
    sub  = history[mask]
    return float(sub.sum()) if len(sub) == 24 else float(history.sum() / len(history) * 24)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)

    if "date" not in data or "history" not in data:
        return jsonify({"error": "Request must include 'date' and 'history'."}), 400

    target_date = pd.Timestamp(data["date"])

    # Build history series
    try:
        hist_records = data["history"]
        hist = pd.Series(
            {pd.Timestamp(r["timestamp"]): float(r["count"]) for r in hist_records}
        ).sort_index()
    except Exception as e:
        return jsonify({"error": f"Invalid history format: {e}"}), 400

    # Generate 24 forecasts (hour 0 … 23 of target_date)
    forecasts = []
    for h in range(24):
        ts  = target_date + pd.Timedelta(hours=h)
        row = build_feature_row(ts, hist)
        X   = pd.DataFrame([row])[FEATURES]
        pred = float(np.maximum(MODEL.predict(X)[0], 0))
        forecasts.append({"hour": h, "predicted_count": round(pred, 2)})

    return jsonify({"date": str(target_date.date()), "forecasts": forecasts})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
