import pandas as pd

from app.analysis.loader import clean_actuals, clean_forecasts


def test_clean_actuals_filters_wind_dedupes_and_drops_nulls():
    raw = pd.DataFrame({
        "startTime": ["2026-01-02T00:00:00Z", "2026-01-02T00:00:00Z", "2026-01-02T00:30:00Z", "2026-01-02T01:00:00Z"],
        "fuelType": ["WIND", "WIND", "WIND", "CCGT"],
        "generation": [100, 105, None, 999],
    })
    out = clean_actuals(raw)
    assert len(out) == 1
    assert out.loc[0, "generation"] == 105  # duplicate keeps the last row


def test_clean_forecasts_dedupes_and_adds_horizon():
    raw = pd.DataFrame({
        "startTime": ["2026-01-02T12:00:00Z"] * 3,
        "publishTime": ["2026-01-01T06:00:00Z", "2026-01-01T06:00:00Z", "2026-01-01T07:00:00Z"],
        "generation": [100, 101, None],
    })
    out = clean_forecasts(raw)
    assert len(out) == 1
    assert out.loc[0, "generation"] == 101
    assert out.loc[0, "horizon_h"] == 30.0
