"""Uncertainty band ("conservative wind") and worst-day analysis.

Method: error = forecast - actual. The buyer is hurt when the forecast is too HIGH, because wind
fails to show up and extra power must be bought. We take the q-th quantile of the historical signed
error (default q = 0.90) as a safety margin and subtract it from the forecast:

    conservative_wind = max(0, forecast - margin)

If q = 0.90, history says actual wind fell below this figure in roughly 10 percent of half-hours.
The margin is estimated from the same period it is evaluated on (in-sample), which is a stated
limitation of this pilot.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def safety_margin(errors: pd.Series, q: float = 0.90) -> float:
    return float(np.quantile(errors.to_numpy(dtype=float), q))


def conservative_wind(forecast: pd.Series, margin_mw: float) -> pd.Series:
    return (forecast - margin_mw).clip(lower=0)


def coverage(df: pd.DataFrame, margin_mw: float) -> float:
    """Share of half-hours where actual >= conservative wind (the margin 'held')."""
    cons = conservative_wind(df["forecast"], margin_mw)
    return float((df["actual"] >= cons).mean())


def worst_days(df: pd.DataFrame, n: int = 5) -> list[dict]:
    """Delivery days ranked by daily MAE, with signed bias and the single largest miss."""
    rows = []
    for day, g in df.groupby("day"):
        worst = g.loc[g["abs_error"].idxmax()]
        rows.append({
            "day": day,
            "mae_mw": float(g["abs_error"].mean()),
            "bias_mw": float(g["error"].mean()),
            "max_abs_error_mw": float(worst["abs_error"]),
            "max_error_at": worst["startTime"],
            "mean_actual_mw": float(g["actual"].mean()),
        })
    return sorted(rows, key=lambda r: r["mae_mw"], reverse=True)[:n]
