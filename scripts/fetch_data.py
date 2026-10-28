"""Fetch Elexon wind actuals (FUELHH) and wind forecasts (WINDFOR) for the January 2026 pilot.

Decisions are made in Jan 2026 for delivery the following day, so delivery days run Jan 2 - Feb 1.
Forecasts are pulled by publishTime from 25 Dec 2025 to 31 Jan 2026 so every decision cutoff has history.

Usage: python scripts/fetch_data.py
Writes: data/raw/fuelhh_wind.csv, data/raw/windfor.csv
"""
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)


def get_json(url, params, retries=4):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            print(f"  HTTP {r.status_code} for {r.url}\n  {r.text[:300]}")
        except requests.RequestException as exc:
            print(f"  request error: {exc}")
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed after {retries} tries: {url} {params}")


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def fetch_actuals():
    rows = []
    # Chunk by week to stay well inside any stream range limit
    start, end = date(2026, 1, 1), date(2026, 2, 1)
    d = start
    while d <= end:
        chunk_end = min(d + timedelta(days=6), end)
        print(f"FUELHH {d} -> {chunk_end}")
        data = get_json(
            f"{BASE}/FUELHH/stream",
            {"settlementDateFrom": d.isoformat(), "settlementDateTo": chunk_end.isoformat(), "fuelType": "WIND"},
        )
        rows.extend(data)
        d = chunk_end + timedelta(days=1)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "fuelhh_wind.csv", index=False)
    print(f"FUELHH rows: {len(df)}; columns: {list(df.columns)}")


def fetch_forecasts():
    rows = []
    # One day of publishTime per request
    for d in daterange(date(2025, 12, 25), date(2026, 1, 31)):
        frm = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        to = frm + timedelta(days=1)
        print(f"WINDFOR publish {d}")
        data = get_json(
            f"{BASE}/WINDFOR/stream",
            {
                "publishDateTimeFrom": frm.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": to.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        rows.extend(data)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "windfor.csv", index=False)
    print(f"WINDFOR rows: {len(df)}; columns: {list(df.columns)}")


if __name__ == "__main__":
    fetch_actuals()
    fetch_forecasts()
