"""Export compact price data for the browser app (docs/data.js)."""
import json, pathlib
import pandas as pd
from backtest import load

ROOT = pathlib.Path(__file__).parent
stocks, nifty = load()
epoch = pd.Timestamp("2020-01-01")
out = []
for sym, s in stocks.items():
    px = s["px"]
    days = ((px.index - epoch).days).tolist()
    out.append(dict(s=sym, n=s["company"].replace(" Limited", "").replace(" Ltd", ""),
                    ip=None if pd.isna(s["issue"]) else float(s["issue"]),
                    d0=days[0], dd=[b - a for a, b in zip(days, days[1:])],
                    c=[round(float(x), 2) for x in px.values]))
nf = nifty[nifty.index >= epoch]
nd = ((nf.index - epoch).days).tolist()
data = dict(asof=str(max(s["px"].index[-1] for s in stocks.values()).date()),
            stocks=out, nifty=dict(d0=nd[0], dd=[b - a for a, b in zip(nd, nd[1:])], c=[round(float(x), 1) for x in nf.values]))
(ROOT / "docs" / "data.js").write_text("window.IPO_DATA=" + json.dumps(data, separators=(",", ":")) + ";")
print(len(out), (ROOT / "docs" / "data.js").stat().st_size // 1024, "KB", data["asof"])
