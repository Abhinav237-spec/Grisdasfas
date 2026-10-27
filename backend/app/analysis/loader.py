"""Load raw Elexon CSVs into clean, UTC-indexed frames.

Assumed columns (to be confirmed against the real files, see issue #2):
  FUELHH (actuals): startTime, generation  (rows already filtered to fuelType WIND)
  WINDFOR (forecasts): startTime, publishTime, generation
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def _to_utc(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        df[c] = pd.to_datetime(df[c], utc=True)
    return df


def clean_actuals(df: pd.DataFrame) -> pd.DataFrame:
    """Keep one row per half-hour; if duplicated, keep the last row. Drop null generation."""
    if "fuelType" in df.columns:
        df = df[df["fuelType"] == "WIND"]
    out = df[["startTime", "generation"]].copy()
    out = _to_utc(out, ["startTime"])
    out["generation"] = pd.to_numeric(out["generation"], errors="coerce")
    out = out.dropna(subset=["generation"])
    out = out.drop_duplicates("startTime", keep="last").sort_values("startTime")
    return out.reset_index(drop=True)


def clean_forecasts(df: pd.DataFrame) -> pd.DataFrame:
    """Keep one row per (startTime, publishTime); drop null generation; add horizon_h."""
    out = df[["startTime", "publishTime", "generation"]].copy()
    out = _to_utc(out, ["startTime", "publishTime"])
    out["generation"] = pd.to_numeric(out["generation"], errors="coerce")
    out = out.dropna(subset=["generation"])
    out = out.drop_duplicates(["startTime", "publishTime"], keep="last")
    out["horizon_h"] = (out["startTime"] - out["publishTime"]).dt.total_seconds() / 3600
    return out.sort_values(["startTime", "publishTime"]).reset_index(drop=True)


def load_actuals(path: str | Path) -> pd.DataFrame:
    return clean_actuals(pd.read_csv(path))


def load_forecasts(path: str | Path) -> pd.DataFrame:
    return clean_forecasts(pd.read_csv(path))
