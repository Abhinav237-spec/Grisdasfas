import math

import pandas as pd

from app.analysis.metrics import compute_metrics


def frame(forecast, actual):
    df = pd.DataFrame({"forecast": forecast, "actual": actual})
    df["error"] = df["forecast"] - df["actual"]
    df["abs_error"] = df["error"].abs()
    return df


def test_metrics_hand_checked():
    # errors: -2, +2, 0, -10  -> MAE 3.5, RMSE sqrt(27), bias -2.5
    m = compute_metrics(frame([10, 20, 30, 40], [12, 18, 30, 50]))
    assert m["n"] == 4
    assert m["mae_mw"] == 3.5
    assert math.isclose(m["rmse_mw"], math.sqrt(27))
    assert m["bias_mw"] == -2.5
    assert m["mean_actual_mw"] == 27.5
    assert math.isclose(m["nmae_pct_of_mean"], 100 * 3.5 / 27.5)
    assert math.isclose(m["nmae_pct_of_peak"], 100 * 3.5 / 50)
    assert m["over_forecast_share"] == 0.25


def test_percentiles_of_absolute_error():
    # abs errors 0..10 -> P50 = 5, P90 = 9, P95 = 9.5
    df = frame(list(range(11)), [0] * 11)
    m = compute_metrics(df)
    assert m["abs_error_p50_mw"] == 5
    assert m["abs_error_p90_mw"] == 9
    assert m["abs_error_p95_mw"] == 9.5


def test_perfect_forecast():
    m = compute_metrics(frame([5, 6, 7], [5, 6, 7]))
    assert m["mae_mw"] == 0 and m["rmse_mw"] == 0 and m["bias_mw"] == 0


def test_empty_frame():
    assert compute_metrics(frame([], [])) == {"n": 0}


def test_zero_actual_does_not_divide_by_zero():
    m = compute_metrics(frame([1, 2], [0, 0]))
    assert m["nmae_pct_of_mean"] is None and m["nmae_pct_of_peak"] is None


def test_rmse_splits_into_bias_and_scatter():
    m = compute_metrics(frame([10, 20, 30, 40], [12, 18, 30, 50]))
    assert math.isclose(m["rmse_mw"] ** 2, m["bias_mw"] ** 2 + m["error_std_mw"] ** 2)
