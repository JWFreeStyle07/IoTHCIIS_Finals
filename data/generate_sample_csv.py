"""
generate_sample_csv.py
----------------------
Generates a realistic synthetic ed-hourly-clean.csv for testing.
Replace this file with your actual dataset — same column names are required:
  timestamp, count, hour, dow, valid

Run once:  python data/generate_sample_csv.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parent / "ed-hourly-clean.csv"

np.random.seed(42)
rng = pd.date_range("2014-01-01", "2017-12-31 23:00", freq="h")

hour    = rng.hour.to_numpy()
dow     = rng.day_of_week.to_numpy()   # 0=Mon
month   = rng.month.to_numpy()

# Hourly arrival intensity – busier midday, quieter overnight
hour_effect = np.clip(np.sin((hour - 6) * np.pi / 12), 0, None) * 8 + 2
dow_effect  = np.where(dow < 5, 1.0, 0.7)              # weekdays busier
month_effect = 1 + 0.1 * np.sin((month - 1) * 2 * np.pi / 12).astype(float)  # slight seasonal

lam = hour_effect * dow_effect * month_effect
count = np.random.poisson(lam).astype(int)

df = pd.DataFrame({
    "timestamp": rng.strftime("%Y-%m-%d %H:%M:%S"),
    "count"    : count,
    "hour"     : hour,
    "dow"      : dow,
    "valid"    : 1,
})

df.to_csv(OUT, index=False)
print(f"Saved {len(df):,} rows to {OUT}")
