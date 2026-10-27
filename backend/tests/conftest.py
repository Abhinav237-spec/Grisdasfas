import pandas as pd
import pytest


def ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


@pytest.fixture
def ts_fn():
    return ts


def make_forecasts(rows):
    """rows: (startTime, publishTime, generation) strings in UTC."""
    df = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df["horizon_h"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    return df


def make_actuals(rows):
    df = pd.DataFrame(rows, columns=["startTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df
