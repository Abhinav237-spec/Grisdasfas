from datetime import date

import pandas as pd

from app.analysis.backtest import build_backtest, join_actuals
from app.analysis.breakdowns import errors_by_horizon, errors_by_hour, errors_by_wind_level
from app.analysis.uncertainty import conservative_wind, coverage, safety_margin, worst_days
from conftest import make_actuals, make_forecasts


def test_join_actuals_sign_convention():
    fc = make_forecasts([("2026-01-02 12:00", "2026-01-01 06:00", 120)])
    act = make_actuals([("2026-01-02 12:00", 100)])
    j = join_actuals(fc, act)
    assert j.loc[0, "error"] == 20 and j.loc[0, "abs_error"] == 20  # over-forecast is positive


def test_errors_by_horizon_buckets():
    # same actual, two forecasts at different lead times: 5h (err 1) and 30h (err 10)
    fc = make_forecasts([
        ("2026-01-02 12:00", "2026-01-02 07:00", 101),
        ("2026-01-02 12:00", "2026-01-01 06:00", 110),
    ])
    j = join_actuals(fc, make_actuals([("2026-01-02 12:00", 100)]))
    by = {r["horizon_bucket"]: r for r in errors_by_horizon(j)}
    assert by["0-6h"]["mae_mw"] == 1
    assert by["30-36h"]["mae_mw"] == 10  # 30h exactly falls in [30, 36)
    assert len(by) == 2


def test_errors_by_hour_uses_uk_local_hour():
    fc = make_forecasts([
        ("2026-01-02 00:00", "2026-01-01 06:00", 10),
        ("2026-01-02 12:00", "2026-01-01 06:00", 30),
    ])
    j = join_actuals(fc, make_actuals([("2026-01-02 00:00", 0), ("2026-01-02 12:00", 20)]))
    by = {r["hour"]: r for r in errors_by_hour(j)}
    assert by[0]["mae_mw"] == 10 and by[12]["mae_mw"] == 10


def test_errors_by_wind_level_tertiles():
    actual = [10, 20, 30, 40, 50, 60]
    df = pd.DataFrame({"actual": actual, "forecast": [a + 5 for a in actual]})
    df["error"] = 5
    df["abs_error"] = 5
    df["startTime"] = pd.date_range("2026-01-02", periods=6, freq="30min", tz="UTC")
    levels = {r["wind_level"]: r["n"] for r in errors_by_wind_level(df)}
    assert levels == {"low": 2, "medium": 2, "high": 2}


def test_safety_margin_and_conservative_wind():
    errors = pd.Series(range(-5, 6))  # -5..5 -> 90th percentile = 4
    assert safety_margin(errors, 0.90) == 4
    cons = conservative_wind(pd.Series([10, 3, 100]), 4)
    assert list(cons) == [6, 0, 96]  # floored at zero


def test_coverage():
    df = pd.DataFrame({"forecast": [100, 100, 100, 100], "actual": [100, 95, 85, 50]})
    # margin 10 -> conservative 90: actual >= 90 for first two only
    assert coverage(df, 10) == 0.5


def test_worst_days_ranking():
    fc = make_forecasts([
        ("2026-01-02 12:00", "2026-01-01 06:00", 110),  # day 1 err 10
        ("2026-01-03 12:00", "2026-01-02 06:00", 150),  # day 2 err 50
    ])
    act = make_actuals([("2026-01-02 12:00", 100), ("2026-01-03 12:00", 100)])
    bt = build_backtest(fc, act, [date(2026, 1, 2), date(2026, 1, 3)])
    w = worst_days(bt, n=2)
    assert [r["day"] for r in w] == [date(2026, 1, 3), date(2026, 1, 2)]
    assert w[0]["mae_mw"] == 50 and w[0]["bias_mw"] == 50


def test_build_backtest_flags_incomplete_days_and_skips_empty():
    fc = make_forecasts([("2026-01-02 12:00", "2026-01-01 06:00", 110)])
    act = make_actuals([("2026-01-02 12:00", 100)])
    bt = build_backtest(fc, act, [date(2026, 1, 2), date(2026, 1, 5)])
    assert list(bt["day"].unique()) == [date(2026, 1, 2)]
    assert not bt["coverage_ok"].iloc[0]  # 1 of 48 half-hours
