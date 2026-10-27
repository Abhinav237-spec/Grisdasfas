"""Error breakdowns by forecast horizon, hour of day and wind level."""
from __future__ import annotations

import pandas as pd

from .metrics import compute_metrics

# Lead-time buckets in hours between publishTime and the target startTime.
HORIZON_BINS = [0, 6, 12, 18, 24, 30, 36, 48, 72, 1e9]
HORIZON_LABELS = ["0-6h", "6-12h", "12-18h", "18-24h", "24-30h", "30-36h", "36-48h", "48-72h", "72h+"]


def _group(df: pd.DataFrame, key: pd.Series, name: str) -> list[dict]:
    rows = []
    for k, g in df.groupby(key, observed=True):
        m = compute_metrics(g)
        m[name] = k if not hasattr(k, "item") else k.item()
        rows.append(m)
    return rows


def errors_by_horizon(joined_all: pd.DataFrame) -> list[dict]:
    """Use ALL forecasts joined to actuals (not only decision-time ones) to show accuracy vs lead time."""
    d = joined_all[joined_all["horizon_h"] >= 0].copy()
    d["horizon_bucket"] = pd.cut(d["horizon_h"], HORIZON_BINS, labels=HORIZON_LABELS, right=False)
    rows = _group(d, d["horizon_bucket"], "horizon_bucket")
    for r in rows:
        r["horizon_bucket"] = str(r["horizon_bucket"])
    return rows


def errors_by_hour(df: pd.DataFrame) -> list[dict]:
    """Hour of day in UK local time (0-23)."""
    hour = df["startTime"].dt.tz_convert("Europe/London").dt.hour
    return _group(df, hour, "hour")


def errors_by_wind_level(df: pd.DataFrame) -> list[dict]:
    """Low / medium / high wind, defined by tertiles of actual generation."""
    if len(df) < 3:
        return []
    level = pd.qcut(df["actual"], 3, labels=["low", "medium", "high"], duplicates="drop")
    rows = _group(df, level, "wind_level")
    for r in rows:
        r["wind_level"] = str(r["wind_level"])
    return rows
