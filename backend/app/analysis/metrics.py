"""Headline error metrics. Input is a frame with `forecast`, `actual`, `error`, `abs_error`.

Sign convention: error = forecast - actual. Positive bias means the forecast over-states wind,
which is the risky direction for a buyer (they would under-procure thermal power).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_metrics(df: pd.DataFrame) -> dict:
    n = len(df)
    if n == 0:
        return {"n": 0}
    err = df["error"].to_numpy(dtype=float)
    abs_err = np.abs(err)
    mean_actual = float(df["actual"].mean())
    peak_actual = float(df["actual"].max())
    mae = float(abs_err.mean())
    return {
        "n": int(n),
        "mae_mw": mae,
        "rmse_mw": float(np.sqrt((err ** 2).mean())),
        "bias_mw": float(err.mean()),
        # RMSE^2 = bias^2 + error_std^2: separates the systematic offset from the random scatter
        "error_std_mw": float(err.std(ddof=0)),
        "mean_actual_mw": mean_actual,
        "peak_actual_mw": peak_actual,
        "nmae_pct_of_mean": float(100 * mae / mean_actual) if mean_actual > 0 else None,
        "nmae_pct_of_peak": float(100 * mae / peak_actual) if peak_actual > 0 else None,
        "abs_error_p50_mw": float(np.percentile(abs_err, 50)),
        "abs_error_p90_mw": float(np.percentile(abs_err, 90)),
        "abs_error_p95_mw": float(np.percentile(abs_err, 95)),
        "over_forecast_share": float((err > 0).mean()),
    }
