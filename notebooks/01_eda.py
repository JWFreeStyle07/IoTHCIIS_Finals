"""
01_eda.py  –  Exploratory Data Analysis for ed-hourly-clean.csv
Run with:  .\\venv\\Scripts\\python notebooks\\01_eda.py
Plots are saved to outputs/eda_*.png
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
DATA    = ROOT / "data" / "ed-hourly-clean.csv"
OUT     = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.set_index("timestamp").sort_index()

print("=== Basic Info ===")
print(df.info())
print("\n=== Head ===")
print(df.head())
print("\n=== Describe ===")
print(df["count"].describe())

# ── Missing-value check ───────────────────────────────────────────────────────
n_missing = df["count"].isna().sum()
full_range = pd.date_range(df.index.min(), df.index.max(), freq="h")
n_gaps     = len(full_range) - len(df)
print(f"\nMissing count values : {n_missing}")
print(f"Gaps in hourly index : {n_gaps}")

# ── 1. Full time-series overview ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 3))
df["count"].plot(ax=ax, lw=0.5, alpha=0.8)
ax.set_title("Hourly ED arrivals – full dataset (2014-2017)")
ax.set_ylabel("Count")
fig.tight_layout()
fig.savefig(OUT / "eda_full_series.png", dpi=150)
print("Saved eda_full_series.png")

# ── 2. Average by hour of day ─────────────────────────────────────────────────
hourly_avg = df.groupby(df.index.hour)["count"].mean()
fig, ax = plt.subplots(figsize=(8, 4))
hourly_avg.plot(kind="bar", ax=ax, color="steelblue")
ax.set_title("Average arrivals by hour of day")
ax.set_xlabel("Hour")
ax.set_ylabel("Mean count")
fig.tight_layout()
fig.savefig(OUT / "eda_hourly_avg.png", dpi=150)
print("Saved eda_hourly_avg.png")

# ── 3. Average by day of week ─────────────────────────────────────────────────
dow_avg = df.groupby(df.index.day_of_week)["count"].mean()
dow_avg.index = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
fig, ax = plt.subplots(figsize=(7, 4))
dow_avg.plot(kind="bar", ax=ax, color="coral")
ax.set_title("Average arrivals by day of week")
ax.set_xlabel("Day")
ax.set_ylabel("Mean count")
fig.tight_layout()
fig.savefig(OUT / "eda_dow_avg.png", dpi=150)
print("Saved eda_dow_avg.png")

# ── 4. Monthly totals ─────────────────────────────────────────────────────────
monthly = df["count"].resample("ME").sum()
fig, ax = plt.subplots(figsize=(12, 4))
monthly.plot(ax=ax, marker="o", color="green")
ax.set_title("Monthly total arrivals")
ax.set_ylabel("Total count")
fig.tight_layout()
fig.savefig(OUT / "eda_monthly_totals.png", dpi=150)
print("Saved eda_monthly_totals.png")

# ── 5. Distribution of hourly counts ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
df["count"].hist(bins=40, ax=ax, color="slategray", edgecolor="white")
ax.set_title("Distribution of hourly arrivals")
ax.set_xlabel("Count")
ax.set_ylabel("Frequency")
fig.tight_layout()
fig.savefig(OUT / "eda_distribution.png", dpi=150)
print("Saved eda_distribution.png")

print("\nEDA complete. All plots saved to outputs/")
