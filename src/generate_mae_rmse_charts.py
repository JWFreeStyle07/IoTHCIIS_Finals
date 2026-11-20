"""
generate_mae_rmse_charts.py
----------------------------
Produces three charts that were missing from the results:
  1. overall_mae_rmse.png        – MAE vs RMSE side-by-side bar chart
  2. peak_vs_offpeak_mae.png     – Peak-hour vs off-peak MAE comparison
  3. mae_rmse_error_bands.png    – Actual vs predicted with ±MAE and ±RMSE
                                   error-band ribbons on the sample week

Run:  .\\venv\\Scripts\\python src\\generate_mae_rmse_charts.py
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT    = Path(__file__).resolve().parent.parent
OUT     = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

# ── Load model and test data ──────────────────────────────────────────────────
art      = joblib.load(ROOT / "models" / "lgbm_model.joblib")
model    = art["model"]
features = art["features"]
df_te    = pd.read_parquet(ROOT / "data" / "features_test.parquet")
preds    = np.maximum(model.predict(df_te[features]), 0)
y_te     = df_te["count"].values

PEAK_HOURS  = list(range(10, 20))
peak_mask   = df_te["hour"].isin(PEAK_HOURS).values
mae_overall = mean_absolute_error(y_te, preds)
rmse_overall= np.sqrt(mean_squared_error(y_te, preds))
mae_peak    = mean_absolute_error(y_te[peak_mask],  preds[peak_mask])
mae_offpeak = mean_absolute_error(y_te[~peak_mask], preds[~peak_mask])

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Overall MAE vs RMSE
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 4.5))

metrics = ["MAE", "RMSE"]
values  = [mae_overall, rmse_overall]
colors  = ["#1565C0", "#E53935"]
bars    = ax.bar(metrics, values, color=colors, width=0.45,
                 edgecolor="white", linewidth=1.2, zorder=3)

# Value labels
for bar, v in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2,
            v + 0.03, f"{v:.4f}",
            ha="center", va="bottom", fontsize=12, fontweight="bold",
            color="#1A237E")

# Difference annotation arrow
diff = rmse_overall - mae_overall
ax.annotate(
    f"Δ = {diff:.4f}\n(RMSE − MAE)",
    xy=(1, rmse_overall / 2 + mae_overall / 2),
    xytext=(1.35, (rmse_overall + mae_overall) / 2),
    fontsize=9, color="#555",
    arrowprops=dict(arrowstyle="->", color="#999", lw=1.2),
    va="center"
)

ax.set_ylim(0, max(values) * 1.25)
ax.set_ylabel("Error  (arrivals / hour)", fontsize=11)
ax.set_title("Overall MAE and RMSE — Test Set (2017)", fontsize=13, fontweight="bold", pad=10)
ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
ax.set_axisbelow(True)

# Explanation text box
note = (
    "MAE = average absolute error per hour\n"
    "RMSE penalises large misses more heavily\n"
    "Gap shows peak-hour prediction errors"
)
ax.text(0.98, 0.04, note, transform=ax.transAxes,
        fontsize=8, color="#555", va="bottom", ha="right",
        bbox=dict(boxstyle="round,pad=0.4", fc="#F5F5F5", ec="#BDBDBD"))

fig.tight_layout()
fig.savefig(OUT / "overall_mae_rmse.png", dpi=150)
print("Saved overall_mae_rmse.png")
plt.close(fig)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Peak-hour vs Off-peak MAE
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

# ── Left: grouped bar ────────────────────────────────────────────────────────
ax = axes[0]
categories = ["Peak Hours\n(10:00–19:00)", "Off-Peak Hours\n(all other hours)"]
vals       = [mae_peak, mae_offpeak]
bar_colors = ["#C62828", "#1565C0"]
bars = ax.bar(categories, vals, color=bar_colors, width=0.42,
              edgecolor="white", linewidth=1.2, zorder=3)

for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2,
            v + 0.025, f"{v:.4f}",
            ha="center", va="bottom", fontsize=12, fontweight="bold",
            color="#1A237E")

# Overall MAE reference line
ax.axhline(mae_overall, color="#FB8C00", linestyle="--", linewidth=1.5,
           label=f"Overall MAE = {mae_overall:.4f}", zorder=4)
ax.legend(fontsize=9, loc="upper right")
ax.set_ylim(0, max(vals) * 1.25)
ax.set_ylabel("MAE  (arrivals / hour)", fontsize=11)
ax.set_title("Peak-Hour vs Off-Peak MAE", fontsize=12, fontweight="bold")
ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
ax.set_axisbelow(True)

diff_pct = (mae_peak - mae_offpeak) / mae_offpeak * 100
ax.text(0.5, 0.06,
        f"Peak hours are {diff_pct:.1f}% harder to predict",
        transform=ax.transAxes, ha="center", fontsize=9,
        color="#B71C1C",
        bbox=dict(boxstyle="round,pad=0.35", fc="#FFEBEE", ec="#EF9A9A"))

# ── Right: horizontal comparison with hour count context ────────────────────
ax2 = axes[1]
n_peak    = peak_mask.sum()
n_offpeak = (~peak_mask).sum()
n_total   = len(y_te)

y_pos  = [1.4, 0.6]
widths = [mae_peak, mae_offpeak]
clrs   = ["#C62828", "#1565C0"]
labels = [
    f"Peak (10–19h)\n{n_peak:,} hrs ({n_peak/n_total*100:.0f}%)",
    f"Off-peak (0–9h, 20–23h)\n{n_offpeak:,} hrs ({n_offpeak/n_total*100:.0f}%)"
]

ax2.barh(y_pos, widths, height=0.5, color=clrs, edgecolor="white", zorder=3)
for y, v, lbl in zip(y_pos, widths, labels):
    ax2.text(v + 0.02, y, f"{v:.4f}", va="center", fontsize=11,
             fontweight="bold", color="#1A237E")
    ax2.text(-0.05, y, lbl, va="center", ha="right", fontsize=9, color="#444")

ax2.axvline(mae_overall, color="#FB8C00", linestyle="--", linewidth=1.5,
            label=f"Overall MAE ({mae_overall:.4f})", zorder=4)
ax2.set_xlim(-1.6, max(widths) * 1.4)
ax2.set_yticks([])
ax2.set_xlabel("MAE  (arrivals / hour)", fontsize=11)
ax2.set_title("MAE by Hour Category", fontsize=12, fontweight="bold")
ax2.xaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
ax2.set_axisbelow(True)
ax2.legend(fontsize=9, loc="lower right")

fig.suptitle("Peak-Hour vs Off-Peak MAE Comparison — Test Set (2017)",
             fontsize=13, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(OUT / "peak_vs_offpeak_mae.png", dpi=150, bbox_inches="tight")
print("Saved peak_vs_offpeak_mae.png")
plt.close(fig)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Actual vs Predicted with ±MAE and ±RMSE error bands
# ═══════════════════════════════════════════════════════════════════════════════
week_mask = (df_te.index >= "2017-01-02") & (df_te.index < "2017-01-09")
ts_week   = df_te.index[week_mask]
y_week    = y_te[week_mask]
p_week    = preds[week_mask]

fig, ax = plt.subplots(figsize=(14, 5))

# Error band: ±RMSE (wider, lighter)
ax.fill_between(ts_week,
                p_week - rmse_overall,
                p_week + rmse_overall,
                alpha=0.15, color="#E53935",
                label=f"±RMSE band (±{rmse_overall:.2f})")

# Error band: ±MAE (narrower, more visible)
ax.fill_between(ts_week,
                p_week - mae_overall,
                p_week + mae_overall,
                alpha=0.25, color="#1565C0",
                label=f"±MAE band (±{mae_overall:.2f})")

# Lines
ax.plot(ts_week, y_week,  color="#0D47A1", lw=1.8, label="Actual arrivals")
ax.plot(ts_week, p_week,  color="#E53935", lw=1.8, ls="--",
        label="Predicted arrivals")

# Peak-hour shading
for day_offset in range(7):
    day_start = pd.Timestamp("2017-01-02") + pd.Timedelta(days=day_offset)
    peak_start = day_start + pd.Timedelta(hours=10)
    peak_end   = day_start + pd.Timedelta(hours=19)
    ax.axvspan(peak_start, peak_end, alpha=0.07, color="#FB8C00", zorder=0)

# Legend entry for peak shading
peak_patch = mpatches.Patch(color="#FB8C00", alpha=0.3,
                             label="Peak hours (10:00–19:00)")

handles, lbls = ax.get_legend_handles_labels()
ax.legend(handles + [peak_patch],
          lbls + ["Peak hours (10:00–19:00)"],
          fontsize=9, loc="upper right", ncol=2)

ax.set_title("Actual vs Predicted with MAE and RMSE Error Bands\n"
             "Sample week: 2 Jan – 8 Jan 2017",
             fontsize=13, fontweight="bold", pad=10)
ax.set_xlabel("Date / Hour", fontsize=11)
ax.set_ylabel("Hourly arrivals", fontsize=11)
ax.set_ylim(bottom=0)
ax.yaxis.grid(True, linestyle="--", alpha=0.4)
ax.set_axisbelow(True)

# Annotation: label the bands on the right side
last_ts  = ts_week[-1]
last_p   = p_week[-1]
ax.annotate(f"+RMSE\n+{rmse_overall:.2f}",
            xy=(last_ts, last_p + rmse_overall),
            xytext=(last_ts, last_p + rmse_overall + 0.3),
            fontsize=7.5, color="#E53935", ha="right")
ax.annotate(f"+MAE\n+{mae_overall:.2f}",
            xy=(last_ts, last_p + mae_overall),
            xytext=(last_ts, last_p + mae_overall + 0.3),
            fontsize=7.5, color="#1565C0", ha="right")

fig.tight_layout()
fig.savefig(OUT / "mae_rmse_error_bands.png", dpi=150)
print("Saved mae_rmse_error_bands.png")
plt.close(fig)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("── Values used in charts ─────────────────────────")
print(f"  Overall MAE     : {mae_overall:.4f}")
print(f"  Overall RMSE    : {rmse_overall:.4f}")
print(f"  Peak-hour MAE   : {mae_peak:.4f}")
print(f"  Off-peak MAE    : {mae_offpeak:.4f}")
print(f"  Peak hours count: {peak_mask.sum():,} / {len(y_te):,}")
print("──────────────────────────────────────────────────")
