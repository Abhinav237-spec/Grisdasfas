"""Join forecasts to actuals and build the decision-time backtest table."""
from __future__ import annotations

from datetime import date, time
from typing import Iterable

import pandas as pd

from .selector import DEFAULT_CUTOFF, expected_hours, select_forecasts


def hourly_actuals(actuals: pd.DataFrame) -> pd.DataFrame:
    """WINDFOR is hourly but FUELHH is half-hourly. Average the two half-hours of each hour.

    The forecast for startTime T (on the hour) is compared with the mean of actuals at T and T+30min.
    Hours where either half-hour is missing are dropped.
    """
    a = actuals[["startTime", "generation"]].copy()
    a["hour"] = a["startTime"].dt.floor("h")
    g = a.groupby("hour")["generation"].agg(["mean", "count"])
    g = g[g["count"] == 2]
    return g["mean"].rename("generation").rename_axis("startTime").reset_index()


def join_actuals(forecasts: pd.DataFrame, actuals: pd.DataFrame, hourly: bool = True) -> pd.DataFrame:
    """Attach actual generation to forecasts. error = forecast - actual (positive = over-forecast)."""
    base = hourly_actuals(actuals) if hourly else actuals
    a = base[["startTime", "generation"]].rename(columns={"generation": "actual"})
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

    Adds `day` (delivery day) and `coverage_ok` (day had a forecast for every hour).
    """
    frames = []
    for d in days:
        sel = select_forecasts(forecasts, d, cutoff)
        if sel.empty:
            continue
        joined = join_actuals(sel, actuals)
        joined["day"] = d
        joined["coverage_ok"] = len(sel) == expected_hours(d)
        frames.append(joined)
    if not frames:
        return pd.DataFrame(
            columns=["startTime", "publishTime", "forecast", "horizon_h", "actual",
                     "error", "abs_error", "day", "coverage_ok"]
        )
    return pd.concat(frames, ignore_index=True)
