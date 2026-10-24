"""Google Haberler'den Türkçe piyasa haberlerini çekip news.json dosyasını üretir.

Kullanım: python3 scripts/fetch_news.py news.json
Genel piyasa gündemi + her varlık için son 7 günün başlıkları.
"""
import email.utils
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from fetch_prices import BIST, CRYPTO, US

UA = "Mozilla/5.0"
PER_ASSET = 6
GENERAL = [
    "Borsa İstanbul when:1d",
    "BIST 100 when:1d",
    "dolar altın piyasa when:1d",
    "Merkez Bankası faiz when:3d",
    "Fed faiz karar when:3d",
    "Wall Street borsa when:1d",
]
FAILS = []


def rss(query, limit):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "tr", "gl": "TR", "ceid": "TR:tr"})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            root = ET.fromstring(r.read())
    except Exception as e:  # noqa: BLE001
        FAILS.append(f"{query}: {e}")
        return []
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        if src and title.endswith(" - " + src):
            title = title[: -len(src) - 3]
        try:
            t = int(email.utils.parsedate_to_datetime(it.findtext("pubDate")).timestamp())
        except Exception:  # noqa: BLE001
            t = 0
        out.append({"title": title, "src": src, "url": it.findtext("link") or "", "t": t})
    out.sort(key=lambda x: -x["t"])
    return out[:limit]


def dedupe(items):
    seen, res = set(), []
    for x in items:
        k = x["title"].lower()[:70]
        if k not in seen:
            seen.add(k)
            res.append(x)
    return res


def main(out):
    general = []
    for q in GENERAL:
        general += rss(q, 15)
        time.sleep(0.4)
    general = dedupe(sorted(general, key=lambda x: -x["t"]))[:40]

    by = {}
    queries = [(c, f'"{c}" hisse when:7d') for c, _ in BIST]
    queries += [(c, f'{n} hisse when:7d') for c, n in US]
    queries += [(c, f'{n} kripto when:7d') for c, n in CRYPTO]
    queries += [("GAU", "gram altın when:3d"), ("GAG", "gümüş fiyatı when:3d"),
                ("USD", "dolar kuru when:2d"), ("EUR", "euro kuru when:2d")]
    for code, q in queries:
        items = dedupe(rss(q, PER_ASSET + 4))[:PER_ASSET]
        if items:
            by[code] = items
        time.sleep(0.4)

    if not general and not by:
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::warning::Haber alınamadı. Örnek: {FAILS[:2]}")
        sys.exit("Haber alınamadı; eski dosya korunuyor.")
    if FAILS and os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning::{len(FAILS)} haber sorgusu başarısız. İlki: {FAILS[0]}")

    data = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "general": general, "by": by}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(general)} genel haber, {len(by)} varlık için haber → {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "news.json")
