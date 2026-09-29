# IPO Post Listing Rally

Tests one hypothesis on NSE mainboard IPOs listed since 2021:

1. The IPO lists and sets a listing-day close.
2. The stock falls below that close on the daily chart.
3. It rounds out a U and closes back above the listing-day close.
4. It then rallies.

**Live app:** https://sajitnandkumar.github.io/ipo-post-listing-rally/

## Result at default settings

Default settings: dip of at least 10%, at least 10 days before the reclaim, reclaim within 250 days, stop 8% below the listing close, 60-day hold.

- 167 of 411 IPOs formed the U.
- The median return 60 days after the reclaim is +1.1%, with about half the signals up. The median signal does not beat the Nifty.
- The average trade makes +7.1%, but the win rate is 39%. Without the 5 best trades the average drops to +3.9%.

The pattern is common, but the reclaim alone is not a reliable rally signal. Any edge comes from a few big winners.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python fetch_data.py    # IPO list (NSE) + daily prices (Yahoo Finance)
.venv/bin/python backtest.py      # prints summary, writes results.csv
.venv/bin/python export_data.py   # writes docs/data.js for the app
```

Open `docs/index.html` through a local server (`python3 -m http.server --directory docs`).

## Data

- **IPO list:** NSE past public issues (`data/past_issues.json`), filtered to mainboard equity.
- **Prices:** Yahoo Finance via `yfinance`, as split-adjusted daily closes with dividends excluded. `data/prices/` is not committed; `fetch_data.py` downloads it.
- **Missing IPOs:** about 20 IPOs that were renamed or delisted have no price data.

Research only. Not investment advice.
