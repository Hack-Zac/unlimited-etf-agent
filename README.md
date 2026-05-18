# Unlimited ETF Holdings Diff Agent

Daily agent that downloads holdings for the four Unlimited ETFs (HFND, HFMF, HFEQ, HFGM), compares today's weightings against the previous snapshot, and emails you a summary of new positions, removed positions, and weight changes above 0.25%.

## How it works

1. Pulls each fund's official CSV from `unlimitedetfs.com/wp-content/uploads/data/TidalFG_Holdings_{TICKER}.csv`
2. Saves it under `data/{TICKER}/{YYYY-MM-DD}.csv` (committed back to the repo for persistence)
3. Diffs against the most recent prior snapshot
4. Emails an HTML summary via SMTP

## Setup

1. Push this repo to GitHub.
2. In **Settings → Secrets and variables → Actions**, add:
   - `SMTP_HOST` (e.g. `smtp.gmail.com`)
   - `SMTP_PORT` (e.g. `587`)
   - `SMTP_USER` (your sending address)
   - `SMTP_PASSWORD` (Gmail App Password if using Gmail — *not* your account password)
   - `EMAIL_FROM` (usually same as SMTP_USER)
   - `EMAIL_TO` (recipient address)
3. In **Settings → Actions → General → Workflow permissions**, enable "Read and write permissions" so the workflow can commit snapshots back.
4. Trigger once manually from the **Actions** tab to seed the first snapshot. The first run won't email (no prior snapshot to diff against). The second run onwards will.

## Local testing

```bash
pip install -r requirements.txt
python -m agent.main
```

Set the SMTP env vars first, or comment out the `send_email` call in `agent/main.py` while testing.

## Tuning

- `WEIGHT_CHANGE_THRESHOLD` in `agent/diff.py` — minimum absolute weight delta (in pp) to flag.
- `TICKERS` in `agent/fetch.py` — add/remove funds.
- Cron in `.github/workflows/daily.yml` — schedule (currently weekdays 21:30 UTC).
