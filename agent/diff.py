"""Compare two holdings snapshots and return a structured diff."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

# Ignore changes smaller than this absolute weight delta (in percentage points)
WEIGHT_CHANGE_THRESHOLD = 0.25


@dataclass
class HoldingsDiff:
    ticker: str
    as_of_today: str
    as_of_previous: str
    added: list[dict] = field(default_factory=list)
    removed: list[dict] = field(default_factory=list)
    changed: list[dict] = field(default_factory=list)  # only above threshold

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["StockTicker"] = df["StockTicker"].astype(str).str.strip()
    df["Weightings"] = pd.to_numeric(df["Weightings"], errors="coerce").fillna(0.0)
    # Collapse duplicates just in case (sum weights)
    return df.groupby("StockTicker", as_index=False).agg(
        Name=("Name", "first"),
        Weightings=("Weightings", "sum"),
    )


def diff_snapshots(ticker: str, today_path: Path, previous_path: Path) -> HoldingsDiff:
    today = _load(today_path)
    prev = _load(previous_path)

    merged = today.merge(
        prev, on="StockTicker", how="outer", suffixes=("_today", "_prev"), indicator=True
    )

    diff = HoldingsDiff(
        ticker=ticker,
        as_of_today=today_path.stem,
        as_of_previous=previous_path.stem,
    )

    for _, row in merged.iterrows():
        sym = row["StockTicker"]
        if row["_merge"] == "left_only":
            diff.added.append({
                "ticker": sym,
                "name": row["Name_today"],
                "weight": float(row["Weightings_today"]),
            })
        elif row["_merge"] == "right_only":
            diff.removed.append({
                "ticker": sym,
                "name": row["Name_prev"],
                "weight": float(row["Weightings_prev"]),
            })
        else:
            delta = float(row["Weightings_today"]) - float(row["Weightings_prev"])
            if abs(delta) >= WEIGHT_CHANGE_THRESHOLD:
                diff.changed.append({
                    "ticker": sym,
                    "name": row["Name_today"],
                    "previous": float(row["Weightings_prev"]),
                    "current": float(row["Weightings_today"]),
                    "delta": delta,
                })

    # Sort for readability
    diff.added.sort(key=lambda x: -x["weight"])
    diff.removed.sort(key=lambda x: -x["weight"])
    diff.changed.sort(key=lambda x: -abs(x["delta"]))
    return diff
