"""Yahoo Finance'ten fiyatları çekip uygulamanın okuduğu prices.json dosyasını üretir.

Kullanım: python3 scripts/fetch_prices.py out/prices.json
Alınamayan semboller atlanır; uygulama yalnızca dosyada olanları gösterir.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

OZ_TO_GRAM = 31.1034768

# BIST 100 endeksindeki şirketler (2026 başı itibarıyla yaklaşık liste; Yahoo'da bulunamayanlar atlanır)
BIST = [
    ("AEFES", "Anadolu Efes"), ("AGHOL", "Anadolu Grubu Holding"), ("AHGAZ", "Ahlatcı Doğalgaz"),
    ("AKBNK", "Akbank"), ("AKFYE", "Akfen Yenilenebilir"), ("AKSA", "Aksa Akrilik"), ("AKSEN", "Aksa Enerji"),
    ("ALARK", "Alarko Holding"), ("ALBRK", "Albaraka Türk"), ("ALFAS", "Alfa Solar"), ("ALTNY", "Altınay Savunma"),
    ("ANSGR", "Anadolu Sigorta"), ("ARCLK", "Arçelik"), ("ARDYZ", "ARD Bilişim"), ("ASELS", "Aselsan"),
    ("ASTOR", "Astor Enerji"), ("BERA", "Bera Holding"), ("BIMAS", "BİM Mağazalar"), ("BINHO", "1000 Yatırımlar Holding"),
    ("BRSAN", "Borusan Boru"), ("BRYAT", "Borusan Yatırım"), ("BSOKE", "Batısöke Çimento"), ("BTCIM", "Batıçim"),
    ("CANTE", "Çan2 Termik"), ("CCOLA", "Coca-Cola İçecek"), ("CIMSA", "Çimsa"), ("CLEBI", "Çelebi Hava Servisi"),
    ("CWENE", "CW Enerji"), ("DOAS", "Doğuş Otomotiv"), ("DOHOL", "Doğan Holding"), ("ECILC", "EİS Eczacıbaşı İlaç"),
    ("EGEEN", "Ege Endüstri"), ("EKGYO", "Emlak Konut GYO"), ("ENERY", "Enerya Enerji"),
    ("ENJSA", "Enerjisa"), ("ENKAI", "Enka İnşaat"), ("EREGL", "Ereğli Demir Çelik"), ("EUPWR", "Europower Enerji"),
    ("FENER", "Fenerbahçe"), ("FROTO", "Ford Otosan"), ("GARAN", "Garanti BBVA"), ("GESAN", "Girişim Elektrik"),
    ("GLRMK", "Gülermak"), ("GOLTS", "Göltaş Çimento"), ("GRSEL", "Gür-Sel Turizm"), ("GSRAY", "Galatasaray"),
    ("GUBRF", "Gübre Fabrikaları"), ("HALKB", "Halkbank"), ("HEKTS", "Hektaş"), ("ISCTR", "İş Bankası (C)"),
    ("ISMEN", "İş Yatırım"), ("KCAER", "Kocaer Çelik"), ("KCHOL", "Koç Holding"), ("KONTR", "Kontrolmatik"),
    ("KONYA", "Konya Çimento"), ("KRDMD", "Kardemir (D)"), ("KTLEV", "Katılımevim"),
    ("LMKDC", "Limak Doğu Anadolu Çimento"), ("MAVI", "Mavi Giyim"), ("MGROS", "Migros"), ("MIATK", "Mia Teknoloji"),
    ("MPARK", "MLP Sağlık (Medical Park)"), ("OBAMS", "Oba Makarnacılık"), ("ODAS", "Odaş Elektrik"), ("OTKAR", "Otokar"),
    ("OYAKC", "Oyak Çimento"), ("PASEU", "Pasifik Eurasia"), ("PETKM", "Petkim"), ("PGSUS", "Pegasus"),
    ("RALYH", "Ral Yatırım Holding"), ("REEDR", "Reeder Teknoloji"), ("SAHOL", "Sabancı Holding"), ("SASA", "SASA Polyester"),
    ("SELEC", "Selçuk Ecza"), ("SISE", "Şişecam"), ("SKBNK", "Şekerbank"), ("SMRTG", "Smart Güneş Enerjisi"),
    ("SOKM", "Şok Marketler"), ("TABGD", "TAB Gıda"), ("TAVHL", "TAV Havalimanları"), ("TCELL", "Turkcell"),
    ("THYAO", "Türk Hava Yolları"), ("TKFEN", "Tekfen Holding"), ("TOASO", "Tofaş"), ("TRALT", "Türk Altın (Koza Altın)"),
    ("TSKB", "TSKB"), ("TTKOM", "Türk Telekom"), ("TTRAK", "Türk Traktör"), ("TUKAS", "Tukaş"), ("TUPRS", "Tüpraş"),
    ("TURSG", "Türkiye Sigorta"), ("ULKER", "Ülker"), ("VAKBN", "VakıfBank"), ("VESBE", "Vestel Beyaz Eşya"),
    ("VESTL", "Vestel"), ("YEOTK", "YEO Teknoloji"), ("YKBNK", "Yapı Kredi"), ("ZOREN", "Zorlu Enerji"),
]
US = [
    ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "NVIDIA"), ("AMZN", "Amazon"), ("GOOGL", "Alphabet (Google)"),
    ("META", "Meta"), ("TSLA", "Tesla"), ("AVGO", "Broadcom"), ("ORCL", "Oracle"), ("NFLX", "Netflix"),
    ("AMD", "AMD"), ("INTC", "Intel"), ("QCOM", "Qualcomm"), ("MU", "Micron"), ("TSM", "TSMC"), ("ASML", "ASML"),
    ("CRM", "Salesforce"), ("ADBE", "Adobe"), ("PLTR", "Palantir"), ("UBER", "Uber"), ("SHOP", "Shopify"),
    ("SPOT", "Spotify"), ("ABNB", "Airbnb"), ("PYPL", "PayPal"), ("COIN", "Coinbase"), ("BABA", "Alibaba"),
    ("JPM", "JPMorgan Chase"), ("BAC", "Bank of America"), ("V", "Visa"), ("MA", "Mastercard"),
    ("BRK-B", "Berkshire Hathaway"), ("WMT", "Walmart"), ("COST", "Costco"), ("KO", "Coca-Cola"), ("PEP", "PepsiCo"),
    ("MCD", "McDonald's"), ("SBUX", "Starbucks"), ("NKE", "Nike"), ("DIS", "Disney"), ("XOM", "Exxon Mobil"),
    ("CVX", "Chevron"), ("LLY", "Eli Lilly"), ("JNJ", "Johnson & Johnson"), ("PFE", "Pfizer"), ("BA", "Boeing"),
    ("F", "Ford"), ("GM", "General Motors"),
]
CRYPTO = [
    ("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("SOL", "Solana"), ("XRP", "XRP"), ("BNB", "BNB"),
    ("DOGE", "Dogecoin"), ("ADA", "Cardano"), ("AVAX", "Avalanche"), ("TRX", "TRON"), ("LINK", "Chainlink"),
    ("DOT", "Polkadot"), ("LTC", "Litecoin"), ("BCH", "Bitcoin Cash"), ("SHIB", "Shiba Inu"), ("XLM", "Stellar"),
    ("NEAR", "NEAR Protocol"), ("ATOM", "Cosmos"), ("ETC", "Ethereum Classic"), ("HBAR", "Hedera"),
    ("FIL", "Filecoin"), ("ALGO", "Algorand"),
]
# Endeks fonları (ETF): tek alımla bir endeksin tamamına yatırım
FUNDS = [
    ("SPY", "S&P 500 Endeks Fonu (ABD'nin en büyük 500 şirketi)"), ("QQQ", "Nasdaq 100 Endeks Fonu (teknoloji ağırlıklı)"),
    ("DIA", "Dow Jones Endeks Fonu"), ("VT", "Tüm Dünya Hisse Fonu"), ("EEM", "Gelişmekte Olan Ülkeler Fonu"),
    ("TUR", "Türkiye Hisse Fonu (MSCI Turkey)"), ("GLD", "Altın Fonu"), ("TLT", "ABD Uzun Vadeli Tahvil Fonu"),
]

# Yahoo tam tarayıcı kimliğiyle gelen çerezsiz istekleri 429 ile reddediyor; kısa kimlik çalışıyor
UA = "Mozilla/5.0"


FAILS = []


def chart(sym):
    last_err = None
    for attempt, host in enumerate(("query1", "query2")):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=5d&interval=30m"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.load(r)["chart"]["result"][0]
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.5)
    FAILS.append(f"{sym}: {last_err}")
    if len(FAILS) <= 3 and os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning::{sym} alınamadı: {last_err}", flush=True)
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
    d = {"p": price, "prev": prev, "t": t_last, "ps": reg.get("start"), "pe": reg.get("end"), "h": hist}
    # Bilgi kartı: gün ve 52 haftalık aralık, hacim
    for k, m in (("dh", "regularMarketDayHigh"), ("dl", "regularMarketDayLow"),
                 ("hi52", "fiftyTwoWeekHigh"), ("lo52", "fiftyTwoWeekLow"), ("vol", "regularMarketVolume")):
        if meta.get(m) is not None:
            d[k] = meta[m]
    return d


def main(out):
    # (kod, ad, kategori, para birimi, yahoo sembolü, ekler)
    specs = [("XU100", "BIST 100 Endeksi", "Endeks", "TRY", "XU100.IS", {"idx": True})]
    specs += [(c, n, "BIST", "TRY", c + ".IS", {}) for c, n in BIST]
    specs += [(c.replace("-", "."), n, "ABD", "USD", c, {}) for c, n in US]
    specs += [(c, n, "Fonlar", "USD", c, {}) for c, n in FUNDS]
    specs += [(c, n, "Kripto", "USD", c + "-USD", {"dec": True, "bn": c + "USDT"}) for c, n in CRYPTO]
    specs += [
        ("USD", "ABD Doları", "Döviz", "TRY", "TRY=X", {"dec": True}),
        ("EUR", "Euro", "Döviz", "TRY", "EURTRY=X", {"dec": True}),
        ("GBP", "İngiliz Sterlini", "Döviz", "TRY", "GBPTRY=X", {"dec": True}),
        ("CHF", "İsviçre Frangı", "Döviz", "TRY", "CHFTRY=X", {"dec": True}),
        ("BRENT", "Brent Petrol (varil)", "Emtia", "USD", "BZ=F", {"dec": True}),
        ("XAU", "Ons Altın", "Emtia", "USD", "GC=F", {"dec": True}),
        ("XAG", "Ons Gümüş", "Emtia", "USD", "SI=F", {"dec": True}),
    ]

    def one(spec):
        code, name, cat, cur, yahoo, extra = spec
        r = chart(yahoo)
        d = parse(r) if r else None
        return code, ({"n": name, "c": cat, "cur": cur, **d, **extra} if d else None)

    # 6 paralel istek: ~190 sembol yarım dakikada biter
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = dict(ex.map(one, specs))
    assets = {code: results[code] for code, *_ in specs if results.get(code)}

    # Gram altın ve gümüş: ons fiyatı × dolar kuru / 31,10
    usd = assets.get("USD")
    if usd:
        k = usd["p"] / OZ_TO_GRAM
        for code, name, src in (("GAU", "Gram Altın", "XAU"), ("GAG", "Gram Gümüş", "XAG")):
            d = assets.get(src)
            if not d:
                continue
            assets[code] = {
                "n": name, "c": "Emtia", "cur": "TRY", "dec": True,
                "p": d["p"] * k, "prev": d["prev"] * usd["prev"] / OZ_TO_GRAM,
                "t": d["t"], "ps": d["ps"], "pe": d["pe"],
                "h": [[t, round(c * k, 4)] for t, c in d["h"]],
                **{f: d[f] * k for f in ("dh", "dl", "hi52", "lo52") if f in d},
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
