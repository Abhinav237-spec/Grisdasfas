"""Decision-time forecast selection.

Assumption: the day-ahead purchase for delivery day D is decided on D-1 at a cutoff
(default 09:00 UK local time). For every half-hour of D we use the forecast with the
greatest publishTime that is at or before that cutoff.
"""
from __future__ import annotations

from datetime import date, time

import pandas as pd

UK_TZ = "Europe/London"
DEFAULT_CUTOFF = time(9, 0)


def delivery_window(day: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """UTC [start, end) of the UK local delivery day. 48 half-hours (46/50 on DST days)."""
    start = pd.Timestamp(day).tz_localize(UK_TZ)
    end = (pd.Timestamp(day) + pd.Timedelta(days=1)).tz_localize(UK_TZ)
    return start.tz_convert("UTC"), end.tz_convert("UTC")


def decision_cutoff(day: date, cutoff: time = DEFAULT_CUTOFF) -> pd.Timestamp:
    """UTC timestamp of the decision cutoff: `cutoff` UK local time on the day before `day`."""
    prev = pd.Timestamp(day) - pd.Timedelta(days=1)
    local = prev.tz_localize(UK_TZ) + pd.Timedelta(hours=cutoff.hour, minutes=cutoff.minute)
    return local.tz_convert("UTC")


def select_forecasts(forecasts: pd.DataFrame, day: date, cutoff: time = DEFAULT_CUTOFF) -> pd.DataFrame:
    """Latest forecast per half-hour of `day` published at or before the cutoff.

    Returns columns startTime, publishTime, generation, horizon_h, one row per half-hour that has a
    forecast. Half-hours with no eligible forecast are simply absent (callers can detect gaps).
    """
    start, end = delivery_window(day)
    cut = decision_cutoff(day, cutoff)
    f = forecasts[
        (forecasts["startTime"] >= start)
        & (forecasts["startTime"] < end)
        & (forecasts["publishTime"] <= cut)
    ]
    latest = f.sort_values("publishTime").groupby("startTime", as_index=False).tail(1)
    return latest.sort_values("startTime").reset_index(drop=True)


def expected_half_hours(day: date) -> int:
    start, end = delivery_window(day)
    return int((end - start) / pd.Timedelta(minutes=30))
