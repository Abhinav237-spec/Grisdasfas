"""Join forecasts to actuals and build the decision-time backtest table."""
from __future__ import annotations

from datetime import date, time
from typing import Iterable

import pandas as pd

from .selector import DEFAULT_CUTOFF, expected_half_hours, select_forecasts


def join_actuals(forecasts: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    """Attach actual generation to forecasts. error = forecast - actual (positive = over-forecast)."""
    a = actuals[["startTime", "generation"]].rename(columns={"generation": "actual"})
    out = forecasts.rename(columns={"generation": "forecast"}).merge(a, on="startTime", how="inner")
    out["error"] = out["forecast"] - out["actual"]
    out["abs_error"] = out["error"].abs()
    return out


def build_backtest(
    forecasts: pd.DataFrame,
    actuals: pd.DataFrame,
    days: Iterable[date],
    cutoff: time = DEFAULT_CUTOFF,
) -> pd.DataFrame:
    """Decision-time forecast vs actual for every delivery day.

    Adds `day` (delivery day) and `coverage_ok` (day had all expected half-hours forecast).
    """
    frames = []
    for d in days:
        sel = select_forecasts(forecasts, d, cutoff)
        if sel.empty:
            continue
        joined = join_actuals(sel, actuals)
        joined["day"] = d
        joined["coverage_ok"] = len(sel) == expected_half_hours(d)
        frames.append(joined)
    if not frames:
        return pd.DataFrame(
            columns=["startTime", "publishTime", "forecast", "horizon_h", "actual",
                     "error", "abs_error", "day", "coverage_ok"]
        )
    return pd.concat(frames, ignore_index=True)
