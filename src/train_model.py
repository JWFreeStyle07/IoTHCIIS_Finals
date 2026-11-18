"""
train_model.py
--------------
Trains a LightGBM model (Poisson objective) on the prepared feature set.
Performs a simple grid search over key hyperparameters using the
validation set (2016).  Saves the best model to models/lgbm_model.joblib.

Usage:
  python src/train_model.py
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product

import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT   = Path(__file__).resolve().parent.parent
DATA   = ROOT / "data"
MODELS = ROOT / "models"
MODELS.mkdir(exist_ok=True)

FEATURE_COLS = [
    "hour", "day_of_week", "is_weekend", "month", "is_holiday",
    "lag_24h", "lag_48h", "lag_168h", "lag_336h",
    "mean_same_hour_4wk", "prev_day_total",
]
TARGET = "count"


def load_split(split: str) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_parquet(DATA / f"features_{split}.parquet")
    return df[FEATURE_COLS], df[TARGET]


def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


def train(X_tr, y_tr, X_val, y_val, params: dict) -> lgb.Booster:
    dtrain = lgb.Dataset(X_tr, label=y_tr)
    dval   = lgb.Dataset(X_val, label=y_val, reference=dtrain)

    base_params = {
        "objective"      : "poisson",
        "metric"         : "poisson",
        "verbosity"      : -1,
        "n_jobs"         : -1,
        "seed"           : 42,
        "max_bin"        : 255,
    }
    base_params.update(params)

    callbacks = [lgb.early_stopping(50, verbose=False), lgb.log_evaluation(100)]

    model = lgb.train(
        base_params,
        dtrain,
        num_boost_round=1000,
        valid_sets=[dval],
        callbacks=callbacks,
    )
    return model


def grid_search(X_tr, y_tr, X_val, y_val):
    param_grid = {
        "learning_rate"   : [0.05, 0.1],
        "num_leaves"      : [31, 63],
        "min_child_samples": [20, 50],
    }

    keys   = list(param_grid.keys())
    values = list(param_grid.values())
    best_mae  = float("inf")
    best_model = None
    best_params = {}

    print("Starting grid search …")
    for combo in product(*values):
        params = dict(zip(keys, combo))
        model  = train(X_tr, y_tr, X_val, y_val, params)
        preds  = np.maximum(model.predict(X_val), 0)
        mae    = mean_absolute_error(y_val, preds)
        print(f"  {params}  →  val MAE={mae:.4f}")
        if mae < best_mae:
            best_mae    = mae
            best_model  = model
            best_params = params

    print(f"\nBest params : {best_params}")
    print(f"Best val MAE: {best_mae:.4f}")
    return best_model, best_params


def main():
    print("Loading data …")
    X_tr,  y_tr  = load_split("train")
    X_val, y_val = load_split("val")
    X_te,  y_te  = load_split("test")

    model, best_params = grid_search(X_tr, y_tr, X_val, y_val)

    # Final evaluation on test set
    preds_te = np.maximum(model.predict(X_te), 0)
    print("\n── Test-set metrics ──────────────────────────────")
    print(f"  MAE : {mean_absolute_error(y_te, preds_te):.4f}")
    print(f"  RMSE: {rmse(y_te, preds_te):.4f}")

    # Save model + feature list
    artifact = {"model": model, "features": FEATURE_COLS, "params": best_params}
    out_path = MODELS / "lgbm_model.joblib"
    joblib.dump(artifact, out_path)
    print(f"\nModel saved to {out_path}")


if __name__ == "__main__":
    main()
