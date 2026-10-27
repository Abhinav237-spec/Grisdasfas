from datetime import date, time

import pandas as pd

from app.analysis.selector import (
    decision_cutoff, delivery_window, expected_half_hours, select_forecasts,
)
from conftest import make_forecasts, ts


def test_cutoff_winter_is_same_as_utc():
    # January is GMT, so 09:00 UK on 1 Jan is 09:00 UTC
    assert decision_cutoff(date(2026, 1, 2)) == ts("2026-01-01 09:00")


def test_cutoff_summer_accounts_for_bst():
    # July is BST (UTC+1): 09:00 UK is 08:00 UTC
    assert decision_cutoff(date(2026, 7, 2)) == ts("2026-07-01 08:00")


def test_custom_cutoff_time():
    assert decision_cutoff(date(2026, 1, 2), time(10, 30)) == ts("2026-01-01 10:30")


def test_delivery_window_winter():
    start, end = delivery_window(date(2026, 1, 2))
    assert start == ts("2026-01-02 00:00") and end == ts("2026-01-03 00:00")


def test_half_hours_per_day_including_dst():
    assert expected_half_hours(date(2026, 1, 2)) == 48
    assert expected_half_hours(date(2026, 3, 29)) == 46   # clocks go forward
    assert expected_half_hours(date(2026, 10, 25)) == 50  # clocks go back


def test_picks_latest_forecast_before_cutoff():
    fc = make_forecasts([
        ("2026-01-02 12:00", "2025-12-31 18:00", 100),
        ("2026-01-02 12:00", "2026-01-01 06:00", 110),  # latest before 09:00 cutoff
        ("2026-01-02 12:00", "2026-01-01 12:00", 999),  # after cutoff, must be ignored
    ])
    sel = select_forecasts(fc, date(2026, 1, 2))
    assert len(sel) == 1
    assert sel.loc[0, "generation"] == 110
    assert sel.loc[0, "publishTime"] == ts("2026-01-01 06:00")


def test_forecast_published_exactly_at_cutoff_is_included():
    fc = make_forecasts([
        ("2026-01-02 12:00", "2026-01-01 08:00", 100),
        ("2026-01-02 12:00", "2026-01-01 09:00", 120),
    ])
    sel = select_forecasts(fc, date(2026, 1, 2))
    assert sel.loc[0, "generation"] == 120


def test_forecast_one_minute_after_cutoff_is_excluded():
    fc = make_forecasts([
        ("2026-01-02 12:00", "2026-01-01 08:00", 100),
        ("2026-01-02 12:00", "2026-01-01 09:01", 120),
    ])
    sel = select_forecasts(fc, date(2026, 1, 2))
    assert sel.loc[0, "generation"] == 100


def test_other_days_are_excluded():
    fc = make_forecasts([
        ("2026-01-01 23:30", "2025-12-31 06:00", 1),   # day before delivery day
        ("2026-01-02 00:00", "2025-12-31 06:00", 2),   # first half-hour of delivery day
        ("2026-01-02 23:30", "2025-12-31 06:00", 3),   # last half-hour of delivery day
        ("2026-01-03 00:00", "2025-12-31 06:00", 4),   # next day
    ])
    sel = select_forecasts(fc, date(2026, 1, 2))
    assert list(sel["generation"]) == [2, 3]


def test_half_hour_with_no_eligible_forecast_is_absent():
    fc = make_forecasts([
        ("2026-01-02 12:00", "2026-01-01 06:00", 100),
        ("2026-01-02 12:30", "2026-01-01 10:00", 200),  # published after cutoff only
    ])
    sel = select_forecasts(fc, date(2026, 1, 2))
    assert list(sel["startTime"]) == [ts("2026-01-02 12:00")]


def test_changing_cutoff_changes_selection():
    fc = make_forecasts([
        ("2026-01-02 12:00", "2026-01-01 06:00", 100),
        ("2026-01-02 12:00", "2026-01-01 11:00", 150),
    ])
    assert select_forecasts(fc, date(2026, 1, 2), time(9, 0)).loc[0, "generation"] == 100
    assert select_forecasts(fc, date(2026, 1, 2), time(12, 0)).loc[0, "generation"] == 150


def test_horizon_of_selected_forecast():
    fc = make_forecasts([("2026-01-02 12:00", "2026-01-01 06:00", 100)])
    sel = select_forecasts(fc, date(2026, 1, 2))
    assert sel.loc[0, "horizon_h"] == 30.0
