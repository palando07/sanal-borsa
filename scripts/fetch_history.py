"""Her varlığın 5 yıllık günlük kapanış fiyatlarını hist/<KOD>.json dosyalarına yazar.

Kullanım: python3 scripts/fetch_history.py hist
Dosya biçimi: {"d": [gün numarası (1970'ten beri)], "c": [kapanış]}; uygulama grafikler,
hareketli ortalama/RSI ve "Ya o zaman alsaydım?" hesabı için kullanır.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from fetch_prices import BIST, CRYPTO, FUNDS, OZ_TO_GRAM, UA, US

FAILS = []


def daily(sym):
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=5y&interval=1d"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.load(r)["chart"]["result"][0]
            off = res["meta"].get("gmtoffset", 0)
            closes = res["indicators"]["quote"][0].get("close") or []
            out = {}
            for t, c in zip(res.get("timestamp") or [], closes):
                if c is not None:
                    out[(t + off) // 86400] = c  # aynı güne düşen son değer kalır
            return out
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(0.5)
    FAILS.append(f"{sym}: {err}")
    return {}


def sig(v):
    return float(f"{v:.6g}")


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    specs = [("XU100", "XU100.IS")]
    specs += [(c, c + ".IS") for c, _ in BIST]
    specs += [(c.replace("-", "."), c) for c, _ in US]
    specs += [(c, c) for c, _ in FUNDS]
    specs += [(c, c + "-USD") for c, _ in CRYPTO]
    specs += [("USD", "TRY=X"), ("EUR", "EURTRY=X"), ("GBP", "GBPTRY=X"), ("CHF", "CHFTRY=X"),
              ("BRENT", "BZ=F"), ("XAU", "GC=F"), ("XAG", "SI=F")]

    with ThreadPoolExecutor(max_workers=6) as ex:
        series = dict(zip([c for c, _ in specs], ex.map(lambda s: daily(s[1]), specs)))

    # Gram altın / gümüş: ons × o günkü dolar kuru / 31,10
    usd = series.get("USD") or {}
    if usd:
        days = sorted(usd)
        for code, src in (("GAU", "XAU"), ("GAG", "XAG")):
            g, last, j = {}, None, 0
            for d in sorted(series.get(src) or {}):
                while j < len(days) and days[j] <= d:
                    last = usd[days[j]]
                    j += 1
                if last:
                    g[d] = series[src][d] * last / OZ_TO_GRAM
            series[code] = g

    n = 0
    for code, s in series.items():
        if len(s) < 5:
            continue
        ds = sorted(s)
        with open(os.path.join(outdir, code + ".json"), "w") as f:
            json.dump({"d": ds, "c": [sig(s[d]) for d in ds]}, f, separators=(",", ":"))
        n += 1

    if FAILS and os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning::{len(FAILS)} sembolün geçmişi alınamadı. İlki: {FAILS[0]}")
    if n < 10:
        sys.exit(f"Yeterli geçmiş alınamadı ({n} dosya).")
    print(f"{n} varlığın geçmişi yazıldı → {outdir}/")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "hist")
