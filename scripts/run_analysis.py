"""Run the full Sprint 1 analysis on the raw Elexon files and print a summary.

Usage (from the repo root):
    python scripts/run_analysis.py                 # reads data/raw, writes data/processed
    python scripts/run_analysis.py --raw DIR --out DIR --cutoff 09:00

Writes to the output directory:
    actuals.csv, forecasts.csv       cleaned inputs
    backtest.csv                     decision-time forecast vs actual, delivery days 2 Jan - 1 Feb 2026
    summary.json                     headline metrics, breakdowns, safety margin, worst days
"""
import argparse
import json
import sys
from datetime import date, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.analysis import (  # noqa: E402
    build_backtest, compute_metrics, coverage, errors_by_horizon, errors_by_hour,
    errors_by_wind_level, join_actuals, load_actuals, load_forecasts, worst_days,
)
from app.analysis.uncertainty import safety_margin  # noqa: E402

FIRST_DAY, LAST_DAY = date(2026, 1, 2), date(2026, 2, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", default=str(ROOT / "data" / "raw"))
    p.add_argument("--out", default=str(ROOT / "data" / "processed"))
    p.add_argument("--cutoff", default="09:00", help="UK local time on the day before delivery, HH:MM")
    a = p.parse_args()
    hh, mm = map(int, a.cutoff.split(":"))
    cutoff = time(hh, mm)

    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    act = load_actuals(raw / "fuelhh_wind.csv")
    fc = load_forecasts(raw / "windfor.csv")
    act.to_csv(out / "actuals.csv", index=False)
    fc.to_csv(out / "forecasts.csv", index=False)

    days = [FIRST_DAY + timedelta(days=i) for i in range((LAST_DAY - FIRST_DAY).days + 1)]
    bt = build_backtest(fc, act, days, cutoff)
    bt.to_csv(out / "backtest.csv", index=False)

    incomplete = sorted({str(d) for d in bt.loc[~bt["coverage_ok"], "day"]})
    missing_days = [str(d) for d in days if d not in set(bt["day"])]
    margin = safety_margin(bt["error"], 0.90)
    summary = {
        "cutoff_uk_local": a.cutoff,
        "delivery_days_with_data": int(bt["day"].nunique()),
        "days_with_no_forecast": missing_days,
        "days_with_incomplete_coverage": incomplete,
        "headline": compute_metrics(bt),
        "safety_margin_p90_mw": margin,
        "margin_coverage_in_sample": coverage(bt, margin),
        "by_horizon_all_forecasts": errors_by_horizon(join_actuals(fc, act)),
        "by_hour": errors_by_hour(bt),
        "by_wind_level": errors_by_wind_level(bt),
        "worst_days": worst_days(bt, 5),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    h = summary["headline"]
    print(f"Delivery days with data: {summary['delivery_days_with_data']} / {len(days)}")
    print(f"No forecast: {missing_days or 'none'}; incomplete coverage: {incomplete or 'none'}")
    print(f"Half-hours evaluated: {h['n']}")
    print(f"MAE {h['mae_mw']:.0f} MW | RMSE {h['rmse_mw']:.0f} MW | bias {h['bias_mw']:+.0f} MW")
    print(f"nMAE {h['nmae_pct_of_mean']:.1f}% of mean actual ({h['mean_actual_mw']:.0f} MW)")
    print(f"P90 safety margin {margin:.0f} MW; margin held in {100 * summary['margin_coverage_in_sample']:.1f}% of half-hours")
    print("Worst days:")
    for w in summary["worst_days"]:
        print(f"  {w['day']}: MAE {w['mae_mw']:.0f} MW, bias {w['bias_mw']:+.0f} MW")
    print(f"Wrote files to {out}")


if __name__ == "__main__":
    main()
