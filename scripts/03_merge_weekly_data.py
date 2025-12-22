"""
03_merge_weekly_data.py

Purpose:
    - Merge weekly 3M T-bill (FRED) with weekly EVM-only USDT supply (DeFiLlama)
    - Align on week (W-FRI)
    - Keep intersection weeks (inner join)
    - Enforce a 5-year weekly window (end at max available week in merged data)
    - Output a clean merged dataset for regression

Inputs:
    data_processed/tbill_3m_weekly.csv      columns: week, tbill_3m
    data_processed/usdt_supply_weekly_evm.csv columns: week, usdt_supply, log_supply

Output:
    data_processed/merged_weekly.csv

Usage:
    python scripts/03_merge_weekly_data.py
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    data_processed = project_root / "data_processed"

    tbill_path = data_processed / "tbill_3m_weekly.csv"
    usdt_path = data_processed / "usdt_supply_weekly_evm.csv"
    out_path = data_processed / "merged_weekly.csv"

    if not tbill_path.exists():
        raise FileNotFoundError(f"Missing file: {tbill_path}")
    if not usdt_path.exists():
        raise FileNotFoundError(f"Missing file: {usdt_path}")

    tbill = pd.read_csv(tbill_path)
    usdt = pd.read_csv(usdt_path)

    # Basic column checks
    required_tbill = {"week", "tbill_3m"}
    required_usdt = {"week", "usdt_supply", "log_supply"}

    if not required_tbill.issubset(set(tbill.columns)):
        raise ValueError(f"{tbill_path.name} must contain columns: {sorted(required_tbill)}")
    if not required_usdt.issubset(set(usdt.columns)):
        raise ValueError(f"{usdt_path.name} must contain columns: {sorted(required_usdt)}")

    # Parse week as datetime
    tbill["week"] = pd.to_datetime(tbill["week"], errors="coerce")
    usdt["week"] = pd.to_datetime(usdt["week"], errors="coerce")

    tbill = tbill.dropna(subset=["week"]).copy()
    usdt = usdt.dropna(subset=["week"]).copy()

    # Ensure uniqueness by week (keep last if duplicates)
    tbill = tbill.sort_values("week").drop_duplicates(subset=["week"], keep="last")
    usdt = usdt.sort_values("week").drop_duplicates(subset=["week"], keep="last")

    # Inner join: intersection of weeks
    merged = tbill.merge(usdt, on="week", how="inner").sort_values("week").reset_index(drop=True)

    if merged.empty:
        raise RuntimeError("Merged dataset is empty. Check that both series share overlapping weeks.")

    # Enforce a 5-year window: end at the latest merged week
    end_week = merged["week"].max()
    start_week = end_week - pd.DateOffset(years=5)

    merged_5y = merged.loc[merged["week"].between(start_week, end_week)].copy()
    merged_5y = merged_5y.reset_index(drop=True)

    # Final sanity checks
    # (No missing values in model variables)
    merged_5y = merged_5y.dropna(subset=["tbill_3m", "usdt_supply", "log_supply"]).copy()

    merged_5y.to_csv(out_path, index=False)

    print("[OK] Weekly datasets merged and trimmed to 5 years.")
    print(f"     Input (tbill): {tbill_path}")
    print(f"     Input (usdt) : {usdt_path}")
    print(f"     Output       : {out_path}")
    print(f"     Rows (merged intersection): {len(merged):,}")
    print(f"     Rows (5y window, cleaned) : {len(merged_5y):,}")
    print(f"     Range (5y window)         : {merged_5y['week'].min().date()} -> {merged_5y['week'].max().date()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
