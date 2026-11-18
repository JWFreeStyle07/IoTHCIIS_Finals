"""
prepare_data.py
---------------
Loads ed-hourly-clean.csv, builds a complete hourly time series,
fills any gaps, and engineers all features used by the LightGBM model.

Outputs:
  data/features_train.parquet  (2014-2015)
  data/features_val.parquet    (2016)
  data/features_test.parquet   (2017)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "ed-hourly-clean.csv"
OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(exist_ok=True)

# ── Philippine public holidays (static list – extend as needed) ───────────────
PH_HOLIDAYS = {
    # Format: "YYYY-MM-DD"
    "2014-01-01", "2014-04-09", "2014-04-17", "2014-04-18",
    "2014-05-01", "2014-06-12", "2014-08-25", "2014-11-01",
    "2014-11-30", "2014-12-25", "2014-12-30", "2014-12-31",
    "2015-01-01", "2015-04-02", "2015-04-03", "2015-05-01",
    "2015-06-12", "2015-08-31", "2015-11-01", "2015-11-30",
    "2015-12-25", "2015-12-30", "2015-12-31",
    "2016-01-01", "2016-03-24", "2016-03-25", "2016-04-09",
    "2016-05-01", "2016-06-12", "2016-08-29", "2016-11-01",
    "2016-11-30", "2016-12-25", "2016-12-30", "2016-12-31",
    "2017-01-01", "2017-04-13", "2017-04-14", "2017-04-15",
    "2017-05-01", "2017-06-12", "2017-08-28", "2017-11-01",
    "2017-11-30", "2017-12-25", "2017-12-30", "2017-12-31",
}


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Expect columns: timestamp, count  (plus optional hour, dow, valid)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    # Keep only the target column
    df = df[["count"]].copy()
    return df


def build_complete_index(df: pd.DataFrame) -> pd.DataFrame:
    """Fill gaps so we have every hour from first to last."""
    full_idx = pd.date_range(df.index.min(), df.index.max(), freq="h")
    df = df.reindex(full_idx)
    # Fill missing counts with the mean of the same hour across the dataset
    df["count"] = df["count"].fillna(
        df.groupby(df.index.hour)["count"].transform("median")
    )
    df["count"] = df["count"].fillna(0).clip(lower=0)
    df.index.name = "timestamp"
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ts = df.index

    # ── Calendar ──────────────────────────────────────────────────────────────
    df["hour"] = ts.hour
    df["day_of_week"] = ts.day_of_week          # 0=Mon … 6=Sun
    df["is_weekend"] = (ts.day_of_week >= 5).astype(int)
    df["month"] = ts.month
    df["is_holiday"] = ts.normalize().strftime("%Y-%m-%d").isin(PH_HOLIDAYS).astype(int)

    # ── Lag features ──────────────────────────────────────────────────────────
    df["lag_24h"]  = df["count"].shift(24)
    df["lag_48h"]  = df["count"].shift(48)
    df["lag_168h"] = df["count"].shift(168)   # 1 week
    df["lag_336h"] = df["count"].shift(336)   # 2 weeks

    # ── Rolling features ──────────────────────────────────────────────────────
    # Same hour over last 4 weeks (use a 28-day window, step = 24h, take mean)
    # Approximated as rolling mean over 4 × 168 hours shifted by 24
    df["mean_same_hour_4wk"] = (
        df["count"]
        .shift(24)
        .rolling(window=4 * 7 * 24, min_periods=1)
        .mean()
    )

    # Previous day total
    df["prev_day_total"] = (
        df["count"]
        .shift(24)
        .rolling(window=24, min_periods=24)
        .sum()
    )

    df = df.dropna()
    return df


def split_and_save(df: pd.DataFrame) -> None:
    train = df[df.index.year.isin([2014, 2015])]
    val   = df[df.index.year == 2016]
    test  = df[df.index.year == 2017]

    train.to_parquet(OUT_DIR / "features_train.parquet")
    val.to_parquet(OUT_DIR / "features_val.parquet")
    test.to_parquet(OUT_DIR / "features_test.parquet")

    print(f"Train rows : {len(train)}")
    print(f"Val   rows : {len(val)}")
    print(f"Test  rows : {len(test)}")
    print("Saved to data/features_*.parquet")


def main():
    print("Loading raw data …")
    df = load_raw(RAW_CSV)
    print(f"Raw rows: {len(df)}  |  range: {df.index.min()} → {df.index.max()}")

    print("Building complete hourly index …")
    df = build_complete_index(df)

    print("Engineering features …")
    df = engineer_features(df)

    print("Splitting and saving …")
    split_and_save(df)
    print("Done.")


if __name__ == "__main__":
    main()
