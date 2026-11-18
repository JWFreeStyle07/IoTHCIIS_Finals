"""
evaluate_model.py
-----------------
Loads the trained model and the test split (2017), then computes:
  - Overall MAE and RMSE
  - Peak-hour MAE  (hours 8–11 and 13–17 — typical clinic busy hours)
  - Skill score vs. seasonal-naïve baseline
  - High-load detection  (precision, recall, F1)

Saves plots to outputs/.

Usage:
  python src/evaluate_model.py
"""

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error,
    precision_score, recall_score, f1_score,
    confusion_matrix,
)

ROOT    = Path(__file__).resolve().parent.parent
DATA    = ROOT / "data"
MODELS  = ROOT / "models"
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(exist_ok=True)

# Peak hours per documentation: 10:00–19:00
PEAK_HOURS = list(range(10, 20))

# High-load threshold: 75th percentile of TRAINING period counts
HIGH_LOAD_QUANTILE = 0.75


def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


def skill_score(y_true, y_pred, y_baseline):
    """1 − MAE_model / MAE_baseline  (higher is better; >0 beats baseline)."""
    mae_model    = mean_absolute_error(y_true, y_pred)
    mae_baseline = mean_absolute_error(y_true, y_baseline)
    return 1.0 - mae_model / mae_baseline


def seasonal_naive_baseline(test_df: pd.DataFrame) -> np.ndarray:
    """
    For each test hour, predict the value from exactly one week ago (168 h).
    Reuses the lag_168h column that was already computed during feature engineering.
    """
    return test_df["lag_168h"].values


def main():
    # ── Load model & test data ───────────────────────────────────────────────
    artifact = joblib.load(MODELS / "lgbm_model.joblib")
    model    = artifact["model"]
    features = artifact["features"]

    test_df = pd.read_parquet(DATA / "features_test.parquet")
    X_te    = test_df[features]
    y_te    = test_df["count"].values
    preds   = np.maximum(model.predict(X_te), 0)

    # ── Overall metrics ──────────────────────────────────────────────────────
    overall_mae  = mean_absolute_error(y_te, preds)
    overall_rmse = rmse(y_te, preds)
    print("── Overall ───────────────────────────────────────")
    print(f"  MAE : {overall_mae:.4f}")
    print(f"  RMSE: {overall_rmse:.4f}")

    # ── Peak-hour MAE ────────────────────────────────────────────────────────
    peak_mask     = test_df["hour"].isin(PEAK_HOURS).values
    peak_mae      = mean_absolute_error(y_te[peak_mask], preds[peak_mask])
    off_peak_mae  = mean_absolute_error(y_te[~peak_mask], preds[~peak_mask])
    print(f"\n── Peak-hour (10:00–19:00) ────────────────────────")
    print(f"  Peak MAE     : {peak_mae:.4f}")
    print(f"  Off-peak MAE : {off_peak_mae:.4f}")

    # ── Skill score vs seasonal naïve ────────────────────────────────────────
    baseline = seasonal_naive_baseline(test_df)
    sk = skill_score(y_te, preds, baseline)
    print(f"\n── Skill score vs seasonal-naïve ─────────────────")
    print(f"  Skill score: {sk:.4f}  ({'beats' if sk > 0 else 'loses to'} baseline)")

    # ── High-load detection ──────────────────────────────────────────────────
    # Threshold = 75th percentile of TRAINING period (as per methodology doc).
    train_df      = pd.read_parquet(DATA / "features_train.parquet")
    actual_threshold = np.quantile(train_df["count"].values, HIGH_LOAD_QUANTILE)
    pred_threshold   = np.quantile(preds, HIGH_LOAD_QUANTILE)
    y_high_true  = (y_te  >= actual_threshold).astype(int)
    y_high_pred  = (preds >= pred_threshold  ).astype(int)
    prec = precision_score(y_high_true, y_high_pred, zero_division=0)
    rec  = recall_score(   y_high_true, y_high_pred, zero_division=0)
    f1   = f1_score(       y_high_true, y_high_pred, zero_division=0)
    print(f"\n── High-load detection ──────────────────────────────────────────")
    print(f"  Actual threshold  (75th pct of training counts) : {actual_threshold:.2f} arrivals")
    print(f"  Predicted threshold (75th pct of test preds)    : {pred_threshold:.2f} arrivals")
    print(f"  Actual high-load hours  : {y_high_true.sum()}")
    print(f"  Predicted high-load hrs : {y_high_pred.sum()}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall   : {rec:.4f}")
    print(f"  F1       : {f1:.4f}")

    # ── Confusion matrix ─────────────────────────────────────────────────────
    cm = confusion_matrix(y_high_true, y_high_pred)
    tn, fp, fn, tp = cm.ravel()
    fig3, ax3 = plt.subplots(figsize=(5, 4))
    im = ax3.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax3)
    classes = ["Normal load", "High load"]
    ax3.set_xticks([0, 1]); ax3.set_xticklabels(classes, fontsize=11)
    ax3.set_yticks([0, 1]); ax3.set_yticklabels(classes, fontsize=11)
    ax3.set_xlabel("Predicted label", fontsize=12)
    ax3.set_ylabel("Actual label", fontsize=12)
    ax3.set_title(f"Confusion Matrix – High-load Detection\n"
                  f"(threshold = 75th pct of training: {actual_threshold:.1f} arrivals)", fontsize=11)
    cell_text = [[f"TN\n{tn}", f"FP\n{fp}"], [f"FN\n{fn}", f"TP\n{tp}"]]
    thresh_cm = cm.max() / 2.0
    for i in range(2):
        for j in range(2):
            ax3.text(j, i, cell_text[i][j], ha="center", va="center", fontsize=12,
                     color="white" if cm[i, j] > thresh_cm else "black")
    fig3.tight_layout()
    fig3.savefig(OUTPUTS / "confusion_matrix.png", dpi=150)
    print(f"Saved confusion_matrix.png to {OUTPUTS}")

    # ── Summary table ────────────────────────────────────────────────────────
    summary = pd.DataFrame({
        "Metric": [
            "Overall MAE", "Overall RMSE",
            "Peak-hour MAE (10:00-19:00)", "Off-peak MAE",
            "Skill score",
            "High-load threshold (75th pct of training)", "Predicted threshold (75th pct of preds)",
            "Actual high-load hours", "Predicted high-load hours",
            "High-load Precision", "High-load Recall", "High-load F1",
        ],
        "Value": [
            overall_mae, overall_rmse,
            peak_mae, off_peak_mae,
            sk,
            actual_threshold, pred_threshold,
            int(y_high_true.sum()), int(y_high_pred.sum()),
            prec, rec, f1,
        ]
    })
    summary.to_csv(OUTPUTS / "evaluation_summary.csv", index=False)
    print(f"\nSaved evaluation_summary.csv to {OUTPUTS}")

    # ── Plot: actual vs predicted (first week of Jan 2017) ──────────────────
    week_mask = (test_df.index >= "2017-01-01") & (test_df.index < "2017-01-08")
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(test_df.index[week_mask], y_te[week_mask],  label="Actual",    lw=1.5)
    ax.plot(test_df.index[week_mask], preds[week_mask], label="Predicted", lw=1.5, ls="--")
    ax.set_title("Actual vs Predicted – first week of Jan 2017")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Hourly arrivals")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUTS / "actual_vs_predicted.png", dpi=150)
    print(f"Saved actual_vs_predicted.png to {OUTPUTS}")

    # ── Feature importance ───────────────────────────────────────────────────
    fi = pd.Series(model.feature_importance(importance_type="gain"),
                   index=features).sort_values(ascending=True)
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    fi.plot(kind="barh", ax=ax2)
    ax2.set_title("Feature importance (gain)")
    ax2.set_xlabel("Gain")
    fig2.tight_layout()
    fig2.savefig(OUTPUTS / "feature_importance.png", dpi=150)
    print(f"Saved feature_importance.png to {OUTPUTS}")


if __name__ == "__main__":
    main()
