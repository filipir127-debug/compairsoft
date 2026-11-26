"""Write the whole site as static files (for Cloudflare Pages).

HTML pages are thin shells; the browser renders them from JSON files:
  data/meta.json        stats, shops, category counts, homepage rows, search synonyms
  data/g/<group>.json   product cards of one top-level category (listing, filters, search)
  data/p/<xx>.json      product details sharded by id prefix: offers, price history, similar
"""
from __future__ import annotations

import bisect
import json
import logging
import shutil
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from . import db as dbmod
from .categories import CATEGORIES, GROUP_OF, GROUPS
from .sources.common import safe_url
from .text import SYNONYMS

log = logging.getLogger(__name__)
HERE = Path(__file__).parent
HISTORY_DAYS = 180


def _num(v):
    return None if v is None else round(v, 2)


def _card(p: dict, shops_of: dict) -> dict:
    return {"id": p["id"], "t": p["title"], "c": p["category"], "p": _num(p["min_price"]), "x": _num(p["max_price"]),
            "s": p["shop_count"], "k": p["in_stock_count"], "i": safe_url(p["image"]) or "", "h": sorted(shops_of.get(p["id"], ()))}


def _dump(path: Path, data) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(raw, encoding="utf-8")
    return len(raw)


def _similar(products: list[dict]) -> dict[str, list[str]]:
    """Up to 8 products of the same category with a similar price, most-compared first."""
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for p in products:
        by_cat[p["category"]].append(p)
    out = {}
    for items in by_cat.values():
        items.sort(key=lambda p: p["min_price"])
        prices = [p["min_price"] for p in items]
        for i, p in enumerate(items):
            lo = bisect.bisect_left(prices, p["min_price"] * 0.6)
            hi = bisect.bisect_right(prices, p["min_price"] * 1.6)
            window = items[max(lo, i - 40):min(hi, i + 41)]
            cands = sorted((q for q in window if q["id"] != p["id"]),
                           key=lambda q: (-q["shop_count"], abs(q["min_price"] - p["min_price"])))
            out[p["id"]] = [q["id"] for q in cands[:8]]
    return out


def export_site(cfg: dict, out: str | Path) -> None:
    settings = cfg["settings"]
    conn = dbmod.connect(settings["database"])
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    (out / "static").mkdir(parents=True)

    products = [dict(r) for r in conn.execute("SELECT * FROM products")]
    if not products:
        raise SystemExit("No products in the database – refusing to publish an empty site.")
    listed = {s["name"] for s in cfg["shops"]}  # shops removed from shops.yaml stay in the DB, hidden
    all_shops = [dict(r) for r in conn.execute("SELECT * FROM shops ORDER BY name")]
    shops = [s for s in all_shops if s["name"] in listed]
    shop_name = {s["id"]: s["name"] for s in all_shops}

    offers: dict[str, list[dict]] = defaultdict(list)
    shops_of: dict[str, set[int]] = defaultdict(set)
    for o in conn.execute("SELECT * FROM offers WHERE product_id IS NOT NULL ORDER BY (in_stock = 0), price_base"):
        offers[o["product_id"]].append(o)
        if o["active"]:
            shops_of[o["product_id"]].add(o["shop_id"])

    # Price history, kept only where the price changed (plus the latest point).
    cutoff = (date.today() - timedelta(days=HISTORY_DAYS)).isoformat()
    history: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    rows = conn.execute("""SELECT o.product_id, o.shop_id, h.day, h.price_base FROM price_history h
                           JOIN offers o ON o.id = h.offer_id
                           WHERE o.product_id IS NOT NULL AND h.day >= ? ORDER BY o.id, h.day""", (cutoff,))
    last: dict[tuple, list] = {}
    for pid, sid, day, price in rows:
        series = history[pid][shop_name[sid]]
        if not series or series[-1][1] != _num(price):
            series.append([day, _num(price)])
        last[(pid, shop_name[sid])] = [day, _num(price)]
    for (pid, shop), point in last.items():
        if history[pid][shop][-1] != point:
            history[pid][shop].append(point)

    cards = {p["id"]: _card(p, shops_of) for p in products}
    similar = _similar(products)

    # Product detail shards
    shards: dict[str, dict] = defaultdict(dict)
    for p in products:
        pid = p["id"]
        shards[pid[:2]][pid] = {
            "p": {**cards[pid], "b": p["brand"], "e": p["ean"]},
            "o": [{"s": shop_name[o["shop_id"]], "t": o["title"], "u": safe_url(o["url"]) or "#", "v": _num(o["price_base"]),
                   "r": _num(o["price"]), "y": o["currency"], "k": o["in_stock"], "a": o["active"]}
                  for o in offers.get(pid, [])],
            "hist": history.get(pid, {}),
            "sim": [{k: v for k, v in cards[q].items() if k != "h"} for q in similar.get(pid, [])[:6]],
        }
    size = sum(_dump(out / "data" / "p" / f"{k}.json", v) for k, v in shards.items())
    log.info("Wrote %d product shards (%.1f MB)", len(shards), size / 1e6)

    # Listing files, one per top-level category
    by_group: dict[str, list[dict]] = defaultdict(list)
    for p in sorted(products, key=lambda p: (-p["shop_count"], p["min_price"])):
        by_group[GROUP_OF.get(p["category"], "misc")].append(cards[p["id"]])
    for g in GROUPS:
        n = _dump(out / "data" / "g" / f"{g}.json", by_group.get(g, []))
        log.info("Group %s: %d products (%.1f MB)", g, len(by_group.get(g, [])), n / 1e6)

    # Metadata and homepage
    counts: dict[str, int] = defaultdict(int)
    for p in products:
        counts[p["category"]] += 1
    multi = [p for p in products if p["shop_count"] > 1 and p["in_stock_count"] > 0]
    sections = [
        {"title": "Compared in the most shops", "more": "/?multi=1&sort=shops",
         "items": [cards[p["id"]] for p in sorted(multi, key=lambda p: (-p["shop_count"], -(p["max_price"] - p["min_price"])))[:12]]},
        {"title": "Biggest price differences", "more": "/?multi=1&sort=savings",
         "items": [cards[p["id"]] for p in sorted(multi, key=lambda p: -(p["max_price"] - p["min_price"]))[:12]]},
    ]
    cheapest = defaultdict(int)
    for p in products:
        if p["shop_count"] > 1:
            for o in offers.get(p["id"], []):
                if o["active"] and o["price_base"] == p["min_price"]:
                    cheapest[o["shop_id"]] += 1
    synonyms: dict[str, list[str]] = defaultdict(list)
    for local, english in SYNONYMS.items():
        if " " not in local:
            synonyms[english].append(local)
    meta = {
        "generated": datetime.now().isoformat(timespec="minutes"),
        "currency": settings["base_currency"],
        "stats": {"products": len(products), "compared": sum(p["shop_count"] > 1 for p in products),
                  "offers": sum(len(v) for v in shops_of.values()), "shops": len(shops)},
        "shops": [{"id": s["id"], "name": s["name"], "url": safe_url(s["url"]), "type": s["type"], "offers": s["offer_count"],
                   "cheapest": cheapest[s["id"]], "updated": s["last_update"], "status": s["last_status"]} for s in shops],
        "counts": counts,
        "sections": sections,
        "syn": synonyms,
    }
    _dump(out / "data" / "meta.json", meta)

    # HTML shells and assets
    version = datetime.now().strftime("%Y%m%d%H%M")
    env = Environment(loader=FileSystemLoader(HERE / "site"), autoescape=True)
    site = {"CATEGORIES": CATEGORIES, "GROUPS": GROUPS, "GROUP_OF": GROUP_OF, "version": version,
            "config": json.dumps({"cats": CATEGORIES, "groups": GROUPS, "groupOf": GROUP_OF,
                                  "currency": settings["base_currency"]}, ensure_ascii=False)}
    for page in ("index", "product", "shops", "404"):
        (out / f"{page}.html").write_text(env.get_template(f"{page}.html").render(page=page, **site), encoding="utf-8")
    for asset in ("style.css", "app.js"):
        shutil.copy(HERE / "static" / asset, out / "static" / asset)
    shutil.copytree(HERE / "static" / "fonts", out / "static" / "fonts")
    (out / "_redirects").write_text("/product/*  /product.html  200\n", encoding="utf-8")
    (out / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n"
        "/data/*\n  Cache-Control: public, max-age=600\n"
        "/static/*\n  Cache-Control: public, max-age=31536000, immutable\n", encoding="utf-8")
    files = sum(1 for f in out.rglob("*") if f.is_file())
    log.info("Exported %d products as %d files to %s", len(products), files, out)
