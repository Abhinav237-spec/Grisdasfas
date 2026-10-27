"""Explore the raw Elexon files. Run after fetch_data.py and paste the full output back.

Usage: python scripts/explore.py
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)


def section(title):
    print(f"\n{'=' * 8} {title} {'=' * 8}")


act = pd.read_csv(RAW / "fuelhh_wind.csv")
fc = pd.read_csv(RAW / "windfor.csv")
for df, cols in ((act, ["startTime", "publishTime"]), (fc, ["startTime", "publishTime"])):
    for c in cols:
        if c in df:
            df[c] = pd.to_datetime(df[c], utc=True)

section("ACTUALS: schema and sample")
print(act.dtypes)
print(act.head(3))
print("fuelType values:", act["fuelType"].unique())
print("startTime range:", act["startTime"].min(), "->", act["startTime"].max())
print("rows:", len(act))
print("duplicate startTime rows:", act.duplicated("startTime").sum())
full = pd.date_range(act["startTime"].min(), act["startTime"].max(), freq="30min")
print("missing half-hours:", len(full.difference(act["startTime"])))
print(act["generation"].describe())
print("negative or null generation:", (act["generation"] < 0).sum(), act["generation"].isna().sum())

section("FORECASTS: schema and sample")
print(fc.dtypes)
print(fc.head(3))
print("rows:", len(fc))
print("startTime range:", fc["startTime"].min(), "->", fc["startTime"].max())
print("publishTime range:", fc["publishTime"].min(), "->", fc["publishTime"].max())
print("duplicate (startTime, publishTime):", fc.duplicated(["startTime", "publishTime"]).sum())
print(fc["generation"].describe())
print("null generation:", fc["generation"].isna().sum())

section("FORECASTS: publish cadence")
pubs = fc["publishTime"].drop_duplicates().sort_values()
print("distinct publishTimes:", len(pubs))
gaps = pubs.diff().dropna()
print("gap between consecutive publishes:\n", gaps.value_counts().head(8))
print("publish minute-of-hour counts:\n", pubs.dt.minute.value_counts().head(6))
print("publishes per day (UTC):\n", pubs.dt.date.value_counts().sort_index().describe())

section("FORECASTS: horizon (startTime - publishTime), hours")
fc["horizon_h"] = (fc["startTime"] - fc["publishTime"]).dt.total_seconds() / 3600
print(fc["horizon_h"].describe())
print("negative horizons (target before publish):", (fc["horizon_h"] < 0).sum())
print("targets per single publish (median):", fc.groupby("publishTime").size().median())
print("horizon percentiles:\n", fc["horizon_h"].quantile([0, .01, .1, .5, .9, .99, 1]))

section("DECISION-TIME SELECTION CHECK (cutoff 09:00 UTC on D-1)")
rows = []
for d in pd.date_range("2026-01-02", "2026-02-01", freq="D", tz="UTC"):
    cutoff = d - pd.Timedelta(days=1) + pd.Timedelta(hours=9)
    targets = fc[(fc["startTime"] >= d) & (fc["startTime"] < d + pd.Timedelta(days=1))]
    avail = targets[targets["publishTime"] <= cutoff]
    latest = avail.sort_values("publishTime").groupby("startTime").tail(1)
    rows.append({
        "delivery_day": d.date(), "cutoff": cutoff,
        "half_hours_covered": latest["startTime"].nunique(),
        "latest_publish": latest["publishTime"].max(),
        "min_horizon_h": latest["horizon_h"].min(), "max_horizon_h": latest["horizon_h"].max(),
    })
sel = pd.DataFrame(rows)
print(sel.to_string(index=False))
print("days with <48 covered half-hours:", (sel["half_hours_covered"] < 48).sum())

section("FORECAST vs ACTUAL QUICK LOOK (latest forecast at cutoff)")
merged = []
for d in pd.date_range("2026-01-02", "2026-02-01", freq="D", tz="UTC"):
    cutoff = d - pd.Timedelta(days=1) + pd.Timedelta(hours=9)
    t = fc[(fc["startTime"] >= d) & (fc["startTime"] < d + pd.Timedelta(days=1)) & (fc["publishTime"] <= cutoff)]
    merged.append(t.sort_values("publishTime").groupby("startTime").tail(1))
m = pd.concat(merged).merge(act[["startTime", "generation"]], on="startTime", suffixes=("_fc", "_act"))
m["err"] = m["generation_fc"] - m["generation_act"]
print("matched half-hours:", len(m))
print("MAE:", m["err"].abs().mean(), "RMSE:", (m["err"] ** 2).mean() ** 0.5, "bias:", m["err"].mean())
print("mean actual:", m["generation_act"].mean())
