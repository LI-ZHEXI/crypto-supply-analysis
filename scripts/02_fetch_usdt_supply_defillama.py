"""
02_fetch_usdt_supply_defillama.py

Purpose:
    - Fetch USDT supply data from DeFiLlama stablecoins API (stablecoins.llama.fi)
    - Restrict to EVM-compatible chains only (EVM-only)
    - Aggregate to daily EVM-only supply (sum across chains)
    - Convert to weekly frequency (W-FRI, weekly mean)
    - Compute log_supply = ln(usdt_supply)

Outputs:
    data_raw/usdt_supply_daily_evm.csv
    data_processed/usdt_supply_weekly_evm.csv

Usage:
    python scripts/02_fetch_usdt_supply_defillama.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import requests


# -----------------------------
# Config
# -----------------------------
BASE = "https://stablecoins.llama.fi"

# EVM-only chain whitelist (as you confirmed)
# NOTE: DeFiLlama uses these slugs in stablecoincharts endpoints
EVM_CHAINS = [
    "ethereum",
    "arbitrum",
    "optimism",
    "bsc",
    "polygon",
    "avax",
    "base",
]

WEEKLY_RULE = "W-FRI"


# -----------------------------
# Helpers
# -----------------------------
def get_stablecoin_id(symbol: str = "USDT") -> int:
    """
    Resolve stablecoin numeric id from /stablecoins endpoint.
    The endpoint returns a dict with 'peggedAssets' list in most cases.
    """
    url = f"{BASE}/stablecoins?includePrices=false"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    payload = r.json()

    if not isinstance(payload, dict):
        raise TypeError(f"Unexpected /stablecoins payload type: {type(payload)}")

    assets = payload.get("peggedAssets")
    if not isinstance(assets, list):
        raise TypeError(f"Unexpected 'peggedAssets' type: {type(assets)}")

    for a in assets:
        if isinstance(a, dict) and str(a.get("symbol", "")).upper() == symbol.upper():
            if "id" not in a:
                raise KeyError(f"Found {symbol} but missing 'id'. Keys={list(a.keys())}")
            return int(a["id"])

    raise ValueError(f"Cannot find stablecoin id for symbol={symbol}")


def fetch_chain_chart(chain: str, stablecoin_id: int) -> pd.DataFrame:
    """
    Fetch stablecoin chart for a given chain.
    Returns a DataFrame with columns: date (datetime), <chain> (float).
    """
    url = f"{BASE}/stablecoincharts/{chain}?stablecoin={stablecoin_id}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    data = r.json()
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Empty or unexpected response for chain={chain}")

    df = pd.DataFrame(data)

    # date: unix seconds (but may come as int/str); make it robust
    if "date" not in df.columns:
        raise KeyError(f"Missing 'date' in response for chain={chain}. Columns={list(df.columns)}")

    df["date"] = pd.to_numeric(df["date"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], unit="s", errors="coerce")

    # totalCirculating is typically a dict; peggedUSD is the supply in USD
    if "totalCirculating" not in df.columns:
        raise KeyError(
            f"Missing 'totalCirculating' in response for chain={chain}. Columns={list(df.columns)}"
        )

    def _extract_supply(x):
        if isinstance(x, dict):
            v = x.get("peggedUSD")
            return float(v) if v is not None else np.nan
        return np.nan

    df[chain] = df["totalCirculating"].apply(_extract_supply)

    out = df[["date", chain]].dropna(subset=["date"]).sort_values("date")
    return out


# -----------------------------
# Main pipeline
# -----------------------------
def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    data_raw = project_root / "data_raw"
    data_processed = project_root / "data_processed"
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)

    # 1) Resolve USDT stablecoin id
    stablecoin_id = get_stablecoin_id("USDT")

    # 2) Fetch chain charts
    dfs: list[pd.DataFrame] = []
    fetched_chains: list[str] = []
    for ch in EVM_CHAINS:
        try:
            d = fetch_chain_chart(ch, stablecoin_id)
            dfs.append(d)
            fetched_chains.append(ch)
        except Exception as e:
            # If a chain endpoint returns non-JSON or empty, we skip it and fill 0 later
            print(f"[WARN] Skip {ch}: {e}", file=sys.stderr)

    if not dfs:
        print("[ERROR] No chain data fetched. Check API availability / chain slugs.", file=sys.stderr)
        return 1

    # 3) Merge all fetched chains on 'date'
    merged = dfs[0]
    for d in dfs[1:]:
        merged = merged.merge(d, on="date", how="outer")

    merged = merged.sort_values("date")

    # 4) Ensure all expected chains exist (fill missing columns with 0)
    #    This prevents KeyError even if some chains were skipped (e.g., 'base')
    merged = merged.reindex(columns=["date"] + EVM_CHAINS, fill_value=0.0)

    # 5) Sum EVM-only supply across chains
    merged["usdt_supply"] = merged[EVM_CHAINS].sum(axis=1, skipna=True)

    # 6) Daily output
    daily = merged[["date", "usdt_supply"]].dropna().copy()
    daily_out = data_raw / "usdt_supply_daily_evm.csv"
    daily.to_csv(daily_out, index=False)

    # 7) Weekly aggregation (W-FRI mean)
    weekly = (
        daily.set_index("date")
        .resample(WEEKLY_RULE)["usdt_supply"]
        .mean()
        .to_frame()
        .reset_index()
        .rename(columns={"date": "week"})
    )

    # drop NA and compute log supply
    weekly = weekly.dropna(subset=["usdt_supply"]).copy()
    weekly["log_supply"] = np.log(weekly["usdt_supply"])

    weekly_out = data_processed / "usdt_supply_weekly_evm.csv"
    weekly.to_csv(weekly_out, index=False)

    # 8) Logs
    print("[OK] USDT EVM-only supply constructed.")
    print(f"     Stablecoin ID (USDT): {stablecoin_id}")
    print(f"     Requested chains: {EVM_CHAINS}")
    print(f"     Fetched chains: {fetched_chains}")
    print(f"     Daily rows: {len(daily):,}")
    print(f"     Daily saved to: {daily_out}")
    print(f"     Weekly rows: {len(weekly):,}")
    print(f"     Weekly saved to: {weekly_out}")
    print(f"     Weekly range: {weekly['week'].min().date()} -> {weekly['week'].max().date()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
