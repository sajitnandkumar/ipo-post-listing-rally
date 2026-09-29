"""Test the 'IPO post-listing U-turn rally' hypothesis on NSE mainboard IPOs.

Pattern, per IPO (all on daily closes, day 0 = listing day):
  L       = listing-day close
  dip     = stock closes below L and its lowest close is at least `dip_min` below L
  reclaim = first close back above L after that trough, within `max_days` of listing,
            and at least `min_base` days after listing (a U, not a one-day V)
  entry   = close on reclaim day
Then measure forward returns (vs Nifty over the same dates) and a simple trade:
exit on stop (close < L * (1 - stop)) or after `hold` days.
"""
import json, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
HORIZONS = (20, 60, 120, 250)


def load():
    u = pd.read_csv(DATA / "universe.csv", parse_dates=["ipo_end"])
    nifty = pd.read_csv(DATA / "nifty.csv", index_col=0, parse_dates=True)["Close"]
    stocks = {}
    for r in u.itertuples():
        f = DATA / "prices" / f"{r.symbol}.csv"
        if not f.exists():
            continue
        px = pd.read_csv(f, index_col=0, parse_dates=True)["Close"].dropna()
        px = px[px > 0]
        # First bar must be the listing: within 15 calendar days of issue close.
        # This drops FPOs / already-listed companies and series missing listing day.
        if len(px) < 5 or not (0 <= (px.index[0] - r.ipo_end).days <= 15):
            continue
        stocks[r.symbol] = dict(company=r.company, issue=r.issue_price, px=px)
    return stocks, nifty


def detect(px, dip_min=0.10, min_base=10, max_days=250):
    c = px.values
    L = c[0]
    below = np.where(c[1:] < L)[0] + 1
    if len(below) == 0:
        return dict(kind="never_below")
    trough_i, trough = None, np.inf
    for i in range(below[0], min(len(c), max_days + 1)):
        if c[i] < trough:
            trough, trough_i = c[i], i
        if c[i] > L and trough <= L * (1 - dip_min) and i >= min_base:
            return dict(kind="u_turn", entry_i=i, trough_i=trough_i, depth=trough / L - 1)
        if c[i] > L and trough > L * (1 - dip_min):
            # shallow wobble: reset and keep looking for a proper dip later
            trough, trough_i = np.inf, None
    return dict(kind="no_reclaim" if trough <= L * (1 - dip_min) else "shallow")


def fwd(series, i, h):
    return series.iloc[i + h] / series.iloc[i] - 1 if i + h < len(series) else np.nan


def trade(c, L, i, stop=0.08, hold=60):
    stop_px = L * (1 - stop)
    for j in range(i + 1, min(len(c), i + hold + 1)):
        if c[j] < stop_px:
            return c[j] / c[i] - 1, j - i, "stop"
    j = min(len(c) - 1, i + hold)
    return c[j] / c[i] - 1, j - i, "time" if j == i + hold else "open"


def run(stocks, nifty, **kw):
    stop, hold = kw.pop("stop", 0.08), kw.pop("hold", 60)
    rows = []
    for sym, s in stocks.items():
        px = s["px"]
        d = detect(px, **kw)
        row = dict(symbol=sym, company=s["company"], listed=px.index[0].date(), issue=s["issue"],
                   L=px.iloc[0], kind=d["kind"], days=len(px),
                   listing_gain=px.iloc[0] / s["issue"] - 1 if s["issue"] else np.nan)
        n = nifty.reindex(px.index).ffill()
        # Baseline: buy at listing close
        for h in HORIZONS:
            row[f"list_r{h}"] = fwd(px, 0, h)
        if d["kind"] == "u_turn":
            i = d["entry_i"]
            row.update(entry_date=px.index[i].date(), entry_day=i, depth=d["depth"],
                       trough_day=d["trough_i"])
            for h in HORIZONS:
                row[f"r{h}"] = fwd(px, i, h)
                row[f"x{h}"] = row[f"r{h}"] - fwd(n, i, h)
            row["mfe120"] = px.iloc[i:i + 121].max() / px.iloc[i] - 1
            row["trade_ret"], row["trade_days"], row["trade_exit"] = trade(px.values, px.iloc[0], i, stop, hold)
        rows.append(row)
    return pd.DataFrame(rows)


def summary(df):
    u = df[df.kind == "u_turn"]
    out = {"universe": len(df), "kinds": df.kind.value_counts().to_dict(), "u_turns": len(u)}
    for h in HORIZONS:
        r, x = u[f"r{h}"].dropna(), u[f"x{h}"].dropna()
        out[f"{h}d"] = dict(n=len(r), median=r.median(), mean=r.mean(), win=(r > 0).mean(),
                            beat_nifty=(x > 0).mean(), median_excess=x.median())
    t = u.dropna(subset=["trade_ret"])
    t = t[t.trade_exit != "open"]
    out["trade"] = dict(n=len(t), win=(t.trade_ret > 0).mean(), avg=t.trade_ret.mean(),
                        median=t.trade_ret.median(), stop_rate=(t.trade_exit == "stop").mean(),
                        avg_win=t.trade_ret[t.trade_ret > 0].mean(), avg_loss=t.trade_ret[t.trade_ret <= 0].mean())
    return out


if __name__ == "__main__":
    stocks, nifty = load()
    df = run(stocks, nifty)
    df.to_csv(ROOT / "results.csv", index=False)
    print(json.dumps(summary(df), indent=1, default=float))
