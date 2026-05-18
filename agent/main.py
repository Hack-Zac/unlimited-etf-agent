"""Entry point: fetch, snapshot, diff, notify."""
from __future__ import annotations
import sys
import traceback
from .fetch import TICKERS, fetch_holdings, save_snapshot, latest_previous_snapshot
from .diff import diff_snapshots, HoldingsDiff
from .notify import send_email


def run() -> int:
    diffs: list[HoldingsDiff] = []
    errors: list[str] = []

    for ticker in TICKERS:
        try:
            df = fetch_holdings(ticker)
            today_path = save_snapshot(ticker, df)
            prev_path = latest_previous_snapshot(ticker, exclude=today_path)
            if prev_path is None:
                print(f"[{ticker}] first snapshot saved at {today_path.name}; no diff yet")
                continue
            if prev_path.name == today_path.name:
                print(f"[{ticker}] today's snapshot already exists, skipping")
                continue
            d = diff_snapshots(ticker, today_path, prev_path)
            diffs.append(d)
            print(f"[{ticker}] {d.as_of_previous} -> {d.as_of_today}: "
                  f"+{len(d.added)} -{len(d.removed)} ~{len(d.changed)}")
        except Exception as e:
            errors.append(f"{ticker}: {e}")
            traceback.print_exc()

    if diffs:
        try:
            send_email(diffs)
            print("Email sent.")
        except Exception:
            traceback.print_exc()
            return 1

    if errors:
        print("Errors:", errors, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
