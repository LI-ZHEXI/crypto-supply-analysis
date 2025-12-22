"""
01_fetch_fred_3m_tbill.py

Purpose:
    - Fetch daily 3M T-bill series from FRED
    - Aggregate to weekly frequency (W-FRI, weekly mean)
    - Save:
        data_raw/tbill_3m_daily.csv
        data_processed/tbill_3m_weekly.csv

Usage:
    export FRED_API_KEY="YOUR_KEY"
    python scripts/01_fetch_fred_3m_tbill.py
"""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta

FRED_SERIES_ID = "DTB3"  # Daily 3-Month Treasury Bill: Secondary Market Rate
FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fred_daily_series(series_id: str, start: str, end: str, api_key: str | None) -> pd.DataFrame:
    params = {
        "series_id": series_id,
        "file_type": "json",
        "observation_start": start,
        "observation_end": end,
    }
    if api_key:
        params["api_key"] = api_key

    resp = requests.get(FRED_API_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if "observations" not in data:
        raise RuntimeError(f"Unexpected FRED response keys: {list(data.keys())}")

    df = pd.DataFrame(data["observations"])
    if df.empty:
        raise RuntimeError("No observations returned. Check series_id/date range/API key.")

    df = df[["date", "value"]].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"].replace(".", pd.NA), errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    return df


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    data_raw_dir = project_root / "data_raw"
    data_processed_dir = project_root / "data_processed"
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    data_processed_dir.mkdir(parents=True, exist_ok=True)

    end_dt = date.today()
    start_dt = end_dt - relativedelta(years=5)

    start = start_dt.isoformat()
    end = end_dt.isoformat()

    api_key = os.getenv("FRED_API_KEY")

    try:
        daily = fetch_fred_daily_series(FRED_SERIES_ID, start, end, api_key)
    except requests.HTTPError as e:
        print(f"[ERROR] FRED request failed: {e}", file=sys.stderr)
        print('Try setting: export FRED_API_KEY="YOUR_KEY"', file=sys.stderr)
        return 1

    daily_out = data_raw_dir / "tbill_3m_daily.csv"
    daily.to_csv(daily_out, index=False)

    weekly = (
        daily.set_index("date")
        .rename(columns={"value": "tbill_3m"})
        .resample("W-FRI")["tbill_3m"]
        .mean()
        .to_frame()
        .reset_index()
        .rename(columns={"date": "week"})
    ).dropna(subset=["tbill_3m"])

    weekly_out = data_processed_dir / "tbill_3m_weekly.csv"
    weekly.to_csv(weekly_out, index=False)

    print("[OK] FRED daily series fetched and saved.")
    print(f"     Series: {FRED_SERIES_ID}")
    print(f"     Daily rows: {len(daily):,} | Missing values: {daily['value'].isna().sum():,}")
    print(f"     Daily saved to: {daily_out}")
    print("[OK] Weekly aggregation complete (W-FRI mean).")
    print(f"     Weekly rows: {len(weekly):,}")
    print(f"     Weekly saved to: {weekly_out}")
    print(f"     Weekly range: {weekly['week'].min().date()} -> {weekly['week'].max().date()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

