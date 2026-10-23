"""Yahoo Finance'ten fiyatları çekip uygulamanın okuduğu prices.json dosyasını üretir.

Kullanım: python3 scripts/fetch_prices.py out/prices.json
Alınamayan semboller atlanır; uygulama yalnızca dosyada olanları gösterir.
"""
import http.cookiejar
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

OZ_TO_GRAM = 31.1034768

# (yahoo sembolü, uygulamadaki kod, ad)
BIST = [
    ("AEFES", "Anadolu Efes"), ("AKBNK", "Akbank"), ("ARCLK", "Arçelik"), ("ASELS", "Aselsan"),
    ("ASTOR", "Astor Enerji"), ("BIMAS", "BİM Mağazalar"), ("CCOLA", "Coca-Cola İçecek"),
    ("DOAS", "Doğuş Otomotiv"), ("EKGYO", "Emlak Konut GYO"), ("ENKAI", "Enka İnşaat"),
    ("EREGL", "Ereğli Demir Çelik"), ("FROTO", "Ford Otosan"), ("GARAN", "Garanti BBVA"),
    ("GUBRF", "Gübre Fabrikaları"), ("HALKB", "Halkbank"), ("HEKTS", "Hektaş"),
    ("ISCTR", "İş Bankası (C)"), ("KCHOL", "Koç Holding"), ("KONTR", "Kontrolmatik"),
    ("KOZAL", "Koza Altın"), ("KRDMD", "Kardemir (D)"), ("MGROS", "Migros"),
    ("OYAKC", "Oyak Çimento"), ("PETKM", "Petkim"), ("PGSUS", "Pegasus"),
    ("SAHOL", "Sabancı Holding"), ("SASA", "SASA Polyester"), ("SISE", "Şişecam"),
    ("TAVHL", "TAV Havalimanları"), ("TCELL", "Turkcell"), ("THYAO", "Türk Hava Yolları"),
    ("TOASO", "Tofaş"), ("TTKOM", "Türk Telekom"), ("TUPRS", "Tüpraş"), ("ULKER", "Ülker"),
    ("VAKBN", "VakıfBank"), ("YKBNK", "Yapı Kredi"),
]
US = [
    ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "NVIDIA"), ("AMZN", "Amazon"),
    ("GOOGL", "Alphabet (Google)"), ("META", "Meta"), ("TSLA", "Tesla"), ("NFLX", "Netflix"),
    ("AMD", "AMD"), ("INTC", "Intel"), ("PLTR", "Palantir"), ("JPM", "JPMorgan Chase"),
    ("V", "Visa"), ("KO", "Coca-Cola"), ("DIS", "Disney"), ("NKE", "Nike"), ("COIN", "Coinbase"),
]
CRYPTO = [
    ("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("SOL", "Solana"), ("XRP", "XRP"),
    ("BNB", "BNB"), ("DOGE", "Dogecoin"), ("ADA", "Cardano"), ("AVAX", "Avalanche"),
]

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


# Yahoo bazı sunuculardan gelen çerezsiz istekleri reddediyor; önce çerez alıyoruz
JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))
OPENER.addheaders = [("User-Agent", UA), ("Accept", "application/json,text/html;q=0.9,*/*;q=0.8"), ("Accept-Language", "en-US,en;q=0.9")]
FAILS = []


def warm_up():
    for url in ("https://fc.yahoo.com/", "https://finance.yahoo.com/"):
        try:
            OPENER.open(url, timeout=15).read(1000)
        except Exception:  # noqa: BLE001  (fc.yahoo.com 404 döner ama çerezi bırakır)
            pass


def chart(sym):
    last_err = None
    for attempt, host in enumerate(("query1", "query2", "query1")):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=5d&interval=30m"
        try:
            with OPENER.open(url, timeout=20) as r:
                return json.load(r)["chart"]["result"][0]
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 * (attempt + 1))
    FAILS.append(f"{sym}: {last_err}")
    print(f"atlandı: {sym} ({last_err})", file=sys.stderr)
    return None


def parse(r):
    """Son fiyat, önceki günün kapanışı, işlem saatleri ve 5 günlük seri."""
    meta = r["meta"]
    off = meta.get("gmtoffset", 0)
    closes = r["indicators"]["quote"][0].get("close") or []
    pts = [(t, c) for t, c in zip(r.get("timestamp") or [], closes) if c is not None]
    price = meta.get("regularMarketPrice") or (pts[-1][1] if pts else None)
    if price is None:
        return None
    t_last = meta.get("regularMarketTime") or (pts[-1][0] if pts else int(time.time()))
    last_day = (t_last + off) // 86400
    before = [c for t, c in pts if (t + off) // 86400 < last_day]
    prev = before[-1] if before else meta.get("chartPreviousClose") or price
    reg = (meta.get("currentTradingPeriod") or {}).get("regular") or {}
    hist = [[t, round(c, 6)] for t, c in pts][-160:]
    return {"p": price, "prev": prev, "t": t_last, "ps": reg.get("start"), "pe": reg.get("end"), "h": hist}


def main(out):
    warm_up()
    print(f"çerez: {len(JAR)} adet")
    assets = {}

    def add(code, name, cat, cur, yahoo, **extra):
        r = chart(yahoo)
        d = parse(r) if r else None
        if d:
            assets[code] = {"n": name, "c": cat, "cur": cur, **d, **extra}

    add("XU100", "BIST 100 Endeksi", "Endeks", "TRY", "XU100.IS", idx=True)
    for code, name in BIST:
        add(code, name, "BIST", "TRY", code + ".IS")
    for code, name in US:
        add(code, name, "ABD", "USD", code)
    for code, name in CRYPTO:
        add(code, name, "Kripto", "USD", code + "-USD", dec=True, bn=code + "USDT")
    add("USD", "ABD Doları", "Döviz", "TRY", "TRY=X", dec=True)
    add("EUR", "Euro", "Döviz", "TRY", "EURTRY=X", dec=True)

    # Gram altın ve gümüş: ons fiyatı × dolar kuru / 31,10
    usd = assets.get("USD")
    if usd:
        k = usd["p"] / OZ_TO_GRAM
        for code, name, yahoo in (("GAU", "Gram Altın", "GC=F"), ("GAG", "Gram Gümüş", "SI=F")):
            r = chart(yahoo)
            d = parse(r) if r else None
            if not d:
                continue
            assets[code] = {
                "n": name, "c": "Emtia", "cur": "TRY", "dec": True,
                "p": d["p"] * k, "prev": d["prev"] * usd["prev"] / OZ_TO_GRAM,
                "t": d["t"], "ps": d["ps"], "pe": d["pe"],
                "h": [[t, round(c * k, 4)] for t, c in d["h"]],
            }

    if FAILS and os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning::{len(FAILS)} sembol alınamadı. İlki: {FAILS[0]}")
    if "USD" not in assets or len(assets) < 10:
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::error::Yeterli veri alınamadı ({len(assets)} varlık). Örnek hata: {FAILS[:3]}")
        sys.exit(f"Yeterli veri alınamadı ({len(assets)} varlık); eski dosya korunuyor.")

    data = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "assets": assets}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(assets)} varlık yazıldı → {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "prices.json")
