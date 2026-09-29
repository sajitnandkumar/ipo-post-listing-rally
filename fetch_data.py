"""Build the mainboard IPO universe (NSE, 2021+) and download daily OHLCV via yfinance."""
import json, time, pathlib
import pandas as pd, yfinance as yf

DATA = pathlib.Path(__file__).parent / "data"
PRICES = DATA / "prices"

def universe():
    d = pd.DataFrame(json.load(open(DATA / "past_issues.json")))
    d = d[d.securityType.isin(["EQ", "BE"])].copy()
    d["ipo_end"] = pd.to_datetime(d.ipoEndDate, format="%d-%b-%Y", errors="coerce")
    d["issue_price"] = pd.to_numeric(d.issuePrice.str.replace(",", ""), errors="coerce")
    d = d.sort_values("ipo_end").drop_duplicates("symbol", keep="first")
    return d[["symbol", "company", "ipo_end", "issue_price"]].reset_index(drop=True)

def fetch(sym):
    out = PRICES / f"{sym}.csv"
    if out.exists():
        return "cached"
    for suffix in (".NS", ".BO"):
        try:
            df = yf.Ticker(sym + suffix).history(period="max", interval="1d", auto_adjust=False)
        except Exception:
            df = pd.DataFrame()
        if len(df):
            df.index = df.index.tz_localize(None).normalize()
            df[["Open", "High", "Low", "Close", "Volume"]].to_csv(out)
            return suffix
    return "missing"

if __name__ == "__main__":
    u = universe()
    u.to_csv(DATA / "universe.csv", index=False)
    res = {}
    for i, s in enumerate(u.symbol):
        res[s] = fetch(s)
        if i % 50 == 0:
            print(i, len(u))
        time.sleep(0.15)
    print(pd.Series(res).value_counts())
    print("missing:", [k for k, v in res.items() if v == "missing"])
    # Nifty 50 benchmark
    n = yf.Ticker("^NSEI").history(period="max", auto_adjust=False)
    n.index = n.index.tz_localize(None).normalize()
    n[["Close"]].to_csv(DATA / "nifty.csv")
