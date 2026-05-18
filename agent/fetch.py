"""Download today's holdings CSV for each Unlimited ETF."""
from __future__ import annotations
from pathlib import Path
from datetime import date
import requests
import pandas as pd
from io import StringIO

TICKERS = ["HFND", "HFMF", "HFEQ", "HFGM"]
URL_TEMPLATE = "https://unlimitedetfs.com/wp-content/uploads/data/TidalFG_Holdings_{ticker}.csv"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def fetch_holdings(ticker: str) -> pd.DataFrame:
    url = URL_TEMPLATE.format(ticker=ticker)
    resp = requests.get(url, timeout=30, headers={"User-Agent": "etf-diff-agent/1.0"})
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    # Normalize: strip whitespace, coerce types we care about
    df.columns = [c.strip() for c in df.columns]
    df["StockTicker"] = df["StockTicker"].astype(str).str.strip()
    df["Weightings"] = pd.to_numeric(df["Weightings"], errors="coerce")
    return df


def save_snapshot(ticker: str, df: pd.DataFrame) -> Path:
    # Use the as-of date inside the file if present, else today
    if "Date" in df.columns and not df["Date"].empty:
        as_of = str(df["Date"].iloc[0]).replace("/", "-")
        # Normalize MM-DD-YYYY -> YYYY-MM-DD
        parts = as_of.split("-")
        if len(parts) == 3 and len(parts[2]) == 4:
            as_of = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
    else:
        as_of = date.today().isoformat()

    out_dir = DATA_DIR / ticker
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{as_of}.csv"
    df.to_csv(out_path, index=False)
    return out_path


def latest_previous_snapshot(ticker: str, exclude: Path) -> Path | None:
    out_dir = DATA_DIR / ticker
    if not out_dir.exists():
        return None
    snapshots = sorted(p for p in out_dir.glob("*.csv") if p != exclude)
    return snapshots[-1] if snapshots else None
