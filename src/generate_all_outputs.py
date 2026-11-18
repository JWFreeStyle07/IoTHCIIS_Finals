"""
generate_all_outputs.py
-----------------------
Produces every output chart and table for the thesis documentation.
Run:  .\\venv\\Scripts\\python src\\generate_all_outputs.py
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error,
    precision_score, recall_score, f1_score,
)

ROOT    = Path(__file__).resolve().parent.parent
OUT     = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

HIGH_LOAD_QUANTILE = 0.75   # 75th percentile of training period
PEAK_HOURS = list(range(10, 20))  # 10:00–19:00 per methodology doc

# ── Load model and all three splits ──────────────────────────────────────────
art      = joblib.load(ROOT / "models" / "lgbm_model.joblib")
model    = art["model"]
features = art["features"]
params   = art["params"]

df_tr = pd.read_parquet(ROOT / "data" / "features_train.parquet")
df_va = pd.read_parquet(ROOT / "data" / "features_val.parquet")
df_te = pd.read_parquet(ROOT / "data" / "features_test.parquet")

p_tr = np.maximum(model.predict(df_tr[features]), 0)
p_va = np.maximum(model.predict(df_va[features]), 0)
p_te = np.maximum(model.predict(df_te[features]), 0)

y_tr = df_tr["count"].values
y_va = df_va["count"].values
y_te = df_te["count"].values

def rmse(a, b): return np.sqrt(mean_squared_error(a, b))

# ── Thresholds for high-load ──────────────────────────────────────────────────
# Actual threshold = 75th percentile of TRAINING counts (per methodology doc)
# Predicted threshold = 75th percentile of TEST predictions (Poisson means are
# lower than raw counts, so we compare each distribution on its own top-25%)
actual_thr = np.quantile(y_tr, HIGH_LOAD_QUANTILE)
pred_thr   = np.quantile(p_te, HIGH_LOAD_QUANTILE)
y_hi_true  = (y_te >= actual_thr).astype(int)
y_hi_pred  = (p_te >= pred_thr  ).astype(int)

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  TRAIN / VAL / TEST MAE COMPARISON (bar chart)
# ═══════════════════════════════════════════════════════════════════════════════
splits = ["Train\n(2014–2015)", "Validation\n(2016)", "Test\n(2017)"]
maes   = [mean_absolute_error(y_tr, p_tr),
          mean_absolute_error(y_va, p_va),
          mean_absolute_error(y_te, p_te)]
colors = ["#1565C0", "#F9A825", "#C62828"]

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(splits, maes, color=colors, width=0.5, edgecolor="white")
for bar, v in zip(bars, maes):
    ax.text(bar.get_x() + bar.get_width()/2, v + 0.02, f"{v:.4f}",
            ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_ylabel("Mean Absolute Error (arrivals/hour)")
ax.set_title("MAE across Train / Validation / Test splits")
ax.set_ylim(0, max(maes) * 1.2)
ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
fig.tight_layout()
fig.savefig(OUT / "train_val_test_mae.png", dpi=150)
print("Saved train_val_test_mae.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 2.  ACTUAL vs PREDICTED  – full test year (2017) scatter
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(y_te, p_te, alpha=0.15, s=8, color="#1565C0", rasterized=True)
lim = max(y_te.max(), p_te.max()) * 1.05
ax.plot([0, lim], [0, lim], "r--", lw=1, label="Perfect fit")
ax.set_xlabel("Actual arrivals")
ax.set_ylabel("Predicted arrivals")
ax.set_title("Actual vs Predicted – Test set (2017)")
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "scatter_actual_vs_predicted.png", dpi=150)
print("Saved scatter_actual_vs_predicted.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 3.  ACTUAL vs PREDICTED  – time-series, one sample week
# ═══════════════════════════════════════════════════════════════════════════════
mask = (df_te.index >= "2017-01-02") & (df_te.index < "2017-01-09")
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(df_te.index[mask], y_te[mask],  label="Actual",    lw=1.5, color="#1565C0")
ax.plot(df_te.index[mask], p_te[mask],  label="Predicted", lw=1.5, color="#E53935", ls="--")
ax.set_title("Actual vs Predicted – sample week (Jan 2–8, 2017)")
ax.set_xlabel("Timestamp"); ax.set_ylabel("Hourly arrivals")
ax.legend(); fig.tight_layout()
fig.savefig(OUT / "actual_vs_predicted.png", dpi=150)
print("Saved actual_vs_predicted.png  (overwritten with sample week)")

# ═══════════════════════════════════════════════════════════════════════════════
# 4.  RESIDUALS distribution
# ═══════════════════════════════════════════════════════════════════════════════
residuals = y_te - p_te
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].hist(residuals, bins=50, color="#1565C0", edgecolor="white")
axes[0].axvline(0, color="red", lw=1.5, ls="--", label="Zero error")
axes[0].set_title("Residuals distribution (Actual − Predicted)")
axes[0].set_xlabel("Residual (arrivals)"); axes[0].set_ylabel("Frequency")
axes[0].legend()

axes[1].scatter(p_te, residuals, alpha=0.1, s=6, color="#1565C0", rasterized=True)
axes[1].axhline(0, color="red", lw=1.5, ls="--")
axes[1].set_title("Residuals vs Predicted values")
axes[1].set_xlabel("Predicted arrivals"); axes[1].set_ylabel("Residual")

fig.tight_layout()
fig.savefig(OUT / "residuals.png", dpi=150)
print("Saved residuals.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 5.  MEAN ABSOLUTE ERROR BY HOUR OF DAY
# ═══════════════════════════════════════════════════════════════════════════════
df_err = pd.DataFrame({"actual": y_te, "pred": p_te, "hour": df_te["hour"].values})
mae_by_hour = df_err.groupby("hour").apply(
    lambda g: mean_absolute_error(g["actual"], g["pred"])
).reset_index(name="mae")

fig, ax = plt.subplots(figsize=(10, 4))
bar_colors = ["#C62828" if h in PEAK_HOURS else "#1565C0" for h in mae_by_hour["hour"]]
ax.bar(mae_by_hour["hour"], mae_by_hour["mae"], color=bar_colors, edgecolor="white")
ax.set_title("MAE by hour of day  (red = peak hours 10:00-19:00)")
ax.set_xlabel("Hour of day"); ax.set_ylabel("MAE (arrivals/hour)")
ax.set_xticks(range(24))
fig.tight_layout()
fig.savefig(OUT / "mae_by_hour.png", dpi=150)
print("Saved mae_by_hour.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 6.  MEAN ABSOLUTE ERROR BY DAY OF WEEK
# ═══════════════════════════════════════════════════════════════════════════════
df_err["dow"] = df_te["day_of_week"].values
mae_by_dow = df_err.groupby("dow").apply(
    lambda g: mean_absolute_error(g["actual"], g["pred"])
).reset_index(name="mae")
dow_labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(dow_labels, mae_by_dow["mae"], color="#1565C0", edgecolor="white")
ax.set_title("MAE by day of week")
ax.set_ylabel("MAE (arrivals/hour)")
fig.tight_layout()
fig.savefig(OUT / "mae_by_dow.png", dpi=150)
print("Saved mae_by_dow.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 7.  FEATURE IMPORTANCE  (overwrite the existing one)
# ═══════════════════════════════════════════════════════════════════════════════
fi = pd.Series(
    model.feature_importance(importance_type="gain"), index=features
).sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(8, 5))
fi.plot(kind="barh", ax=ax, color="#1565C0", edgecolor="white")
ax.set_title("Feature importance (gain) – LightGBM")
ax.set_xlabel("Total gain")
fig.tight_layout()
fig.savefig(OUT / "feature_importance.png", dpi=150)
print("Saved feature_importance.png  (overwritten)")

# ═══════════════════════════════════════════════════════════════════════════════
# 8.  HIGH-LOAD DETECTION summary chart
# ═══════════════════════════════════════════════════════════════════════════════
prec = precision_score(y_hi_true, y_hi_pred, zero_division=0)
rec  = recall_score(   y_hi_true, y_hi_pred, zero_division=0)
f1   = f1_score(       y_hi_true, y_hi_pred, zero_division=0)

fig, ax = plt.subplots(figsize=(6, 4))
metrics = ["Precision", "Recall", "F1 Score"]
vals    = [prec, rec, f1]
bar_c   = ["#2E7D32", "#1565C0", "#E65100"]
bars = ax.bar(metrics, vals, color=bar_c, width=0.4, edgecolor="white")
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width()/2, v + 0.01, f"{v:.3f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylim(0, 1.0)
ax.set_title(f"High-load detection  (top 20% of hours)\nActual threshold ≥ {actual_thr:.1f}  |  Pred threshold ≥ {pred_thr:.1f} arrivals")
ax.set_ylabel("Score")
fig.tight_layout()
fig.savefig(OUT / "high_load_detection.png", dpi=150)
print("Saved high_load_detection.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 9.  COMPREHENSIVE EVALUATION TABLE  (CSV)
# ═══════════════════════════════════════════════════════════════════════════════
skill_baseline_mae = mean_absolute_error(y_te, df_te["lag_168h"].values)
skill = 1.0 - mean_absolute_error(y_te, p_te) / skill_baseline_mae

rows = [
    ("Dataset",           "Real ED arrivals (2014–2017)"),
    ("Model",             "LightGBM – Poisson objective"),
    ("Best learning_rate", params["learning_rate"]),
    ("Best num_leaves",   params["num_leaves"]),
    ("Best min_child_samples", params["min_child_samples"]),
    ("Number of trees",   model.num_trees()),
    ("--- SPLIT METRICS ---", ""),
    ("Train MAE",         round(mean_absolute_error(y_tr, p_tr), 4)),
    ("Validation MAE",    round(mean_absolute_error(y_va, p_va), 4)),
    ("Test MAE",          round(mean_absolute_error(y_te, p_te), 4)),
    ("Test RMSE",         round(rmse(y_te, p_te), 4)),
    ("--- PEAK HOURS ---", ""),
    ("Peak-hour MAE (10:00-19:00)", round(mean_absolute_error(
        y_te[df_te["hour"].isin(PEAK_HOURS).values],
        p_te[df_te["hour"].isin(PEAK_HOURS).values]), 4)),
    ("Off-peak MAE",      round(mean_absolute_error(
        y_te[~df_te["hour"].isin(PEAK_HOURS).values],
        p_te[~df_te["hour"].isin(PEAK_HOURS).values]), 4)),
    ("--- SKILL SCORE ---", ""),
    ("Seasonal-naïve baseline MAE", round(skill_baseline_mae, 4)),
    ("Skill score vs naïve baseline", round(skill, 4)),
    ("--- HIGH-LOAD DETECTION ---", ""),
    ("Actual high-load threshold (75th pct of training)", round(actual_thr, 2)),
    ("Predicted high-load threshold (75th pct of preds)", round(pred_thr, 2)),
    ("Actual high-load hours",   int(y_hi_true.sum())),
    ("Predicted high-load hours", int(y_hi_pred.sum())),
    ("High-load Precision",      round(prec, 4)),
    ("High-load Recall",         round(rec, 4)),
    ("High-load F1",             round(f1, 4)),
]

summary_df = pd.DataFrame(rows, columns=["Metric", "Value"])
summary_df.to_csv(OUT / "evaluation_summary.csv", index=False)
print("Saved evaluation_summary.csv  (full version)")

# ═══════════════════════════════════════════════════════════════════════════════
# 10.  CONFUSION MATRIX for high-load detection
# ═══════════════════════════════════════════════════════════════════════════════
from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_hi_true, y_hi_pred)
# cm layout:
#   [[TN, FP],
#    [FN, TP]]
tn, fp, fn, tp = cm.ravel()

fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
plt.colorbar(im, ax=ax)

# Labels
classes = ["Normal load", "High load"]
tick_marks = [0, 1]
ax.set_xticks(tick_marks); ax.set_xticklabels(classes, fontsize=11)
ax.set_yticks(tick_marks); ax.set_yticklabels(classes, fontsize=11)
ax.set_xlabel("Predicted label", fontsize=12)
ax.set_ylabel("Actual label", fontsize=12)
ax.set_title(f"Confusion Matrix – High-load Detection\n"
             f"(threshold = 75th pct of training: {actual_thr:.1f} arrivals)", fontsize=11)

# Cell annotations
cell_text = [[f"TN\n{tn}", f"FP\n{fp}"],
             [f"FN\n{fn}", f"TP\n{tp}"]]
thresh = cm.max() / 2.0
for i in range(2):
    for j in range(2):
        ax.text(j, i, cell_text[i][j],
                ha="center", va="center", fontsize=12,
                color="white" if cm[i, j] > thresh else "black")

fig.tight_layout()
fig.savefig(OUT / "confusion_matrix.png", dpi=150)
print("Saved confusion_matrix.png")

# ═══════════════════════════════════════════════════════════════════════════════
# Done
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── All outputs saved to outputs/ ──────────────────────────────")
print(f"  train_val_test_mae.png")
print(f"  scatter_actual_vs_predicted.png")
print(f"  actual_vs_predicted.png")
print(f"  residuals.png")
print(f"  mae_by_hour.png")
print(f"  mae_by_dow.png")
print(f"  feature_importance.png")
print(f"  high_load_detection.png")
print(f"  confusion_matrix.png")
print(f"  evaluation_summary.csv")
