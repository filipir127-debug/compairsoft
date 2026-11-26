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
import re
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from . import db as dbmod
from .categories import CATEGORIES, GROUP_OF, GROUPS
from .sources.common import safe_url
from .text import SYNONYMS, colors, normalize, strip_accents

log = logging.getLogger(__name__)
HERE = Path(__file__).parent
HISTORY_DAYS = 180
GROUP_ICONS = {"weapons": "crosshair", "ammo": "layers", "sights": "telescope", "upgrades": "cog",
               "gear": "backpack", "protection": "shield", "apparel": "shirt", "misc": "layout-grid"}


def _num(v):
    return None if v is None else round(v, 2)


_POWER = [("hpa", r"\bhpa\b"), ("co2", r"\bco2\b"),
          ("gas", r"\b(gbbr?|gnb|plyn\w*|green ?gas|gas ?blow\w*)\b"),
          ("electric", r"\b(aeg|aep|ebb|etu|bldc|mosfet|elektri\w*|electric\w*)\b"),
          ("spring", r"\b(manual\w*|manualn\w*|pruzin\w*|spring\w*|bolt ?action)\b")]
_METAL = r"\b(kov\w*|celokov\w*|full ?metal|metal\w*|ocel\w*|steel|hlinik\w*|alu\w*|cnc)\b"
_PLASTIC = r"\b(abs|plast\w*|nylon\w*|polymer\w*)\b"
_CAP = r"\b(mid|hi|high|low|real)[ -]?cap\b"
_BB_WEIGHT = r"\b0[,.](\d{2})\d? ?g\b"


def _attrs(title: str, category: str) -> list[str]:
    """Filterable tags derived from the title: colour, power source, material, capacity, BB weight."""
    t = strip_accents(title.lower())
    tags = [f"col:{c}" for c in sorted(colors(normalize(title)))]
    if GROUP_OF.get(category) == "weapons":
        power = next((name for name, rx in _POWER if re.search(rx, t)), None)
        if power:
            tags.append(f"pw:{power}")
        if re.search(_METAL, t):
            tags.append("mt:metal")
        elif re.search(_PLASTIC, t):
            tags.append("mt:plastic")
    if category == "magazines" and (m := re.search(_CAP, t)):
        tags.append("cap:" + {"high": "hi"}.get(m.group(1), m.group(1)))
    if category == "bbs" and (m := re.search(_BB_WEIGHT, t)):
        tags.append(f"bbw:0.{m.group(1)}")
    return tags


def _brand(p: dict, known: dict[str, str]) -> str | None:
    """The product's brand, or a known brand named at the end of the title ("…, Specna Arms")."""
    if p["brand"]:
        return known.get(p["brand"].strip().lower(), p["brand"].strip())
    for part in reversed(re.split(r"\s*[,\-–]\s*", p["title"])):
        if part.strip().lower() in known:
            return known[part.strip().lower()]
    return None


def _card(p: dict, shops_of: dict, brand: str | None = None) -> dict:
    card = {"id": p["id"], "t": p["title"], "c": p["category"], "p": _num(p["min_price"]), "x": _num(p["max_price"]),
            "s": p["shop_count"], "k": p["in_stock_count"], "i": safe_url(p["image"]) or "",
            "h": sorted(shops_of.get(p["id"], ()))}
    if brand:
        card["b"] = brand
    if tags := _attrs(p["title"], p["category"]):
        card["a"] = tags
    return card


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


# No inline scripts anywhere: only our own files run. Product photos come from the shops (https only);
# Cloudflare Web Analytics is allowed in case it is switched on in the dashboard.
CSP = ("default-src 'self'; script-src 'self' https://static.cloudflareinsights.com; style-src 'self'; "
       "style-src-attr 'unsafe-inline'; img-src 'self' https: data:; font-src 'self'; "
       "connect-src 'self' https://cloudflareinsights.com; object-src 'none'; base-uri 'none'; "
       "frame-ancestors 'none'; form-action 'self'; upgrade-insecure-requests")

TILE_SUBCATEGORY = {"weapons": "guns", "ammo": "magazines", "sights": "optics", "upgrades": "parts",
                    "gear": "vests", "protection": "helmets", "apparel": "clothing", "misc": "grenades"}


def _group_images(products: list[dict], offers: dict) -> dict[str, str]:
    """A representative photo per top-level category: a typical item (a rifle for guns, a vest for
    gear) that is widely compared and pricier, which tends to be the flagship product."""
    out = {}
    for g, sub in TILE_SUBCATEGORY.items():
        cands = [p for p in products if p["category"] == sub and safe_url(p["image"])] or \
                [p for p in products if GROUP_OF.get(p["category"]) == g and safe_url(p["image"])]
        if cands:
            best = max(cands, key=lambda p: (min(p["shop_count"], 3), p["in_stock_count"] > 0, p["min_price"]))
            out[g] = safe_url(best["image"])
    return out


def _scramble(email: str) -> str:
    """Keep the address out of the page source in plain text, so address-harvesting bots miss it."""
    import base64
    return base64.b64encode(email[::-1].encode()).decode() if email else ""


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

    # Brands as most shops spell them; a brand must be used by 3+ products to count.
    spellings: dict[str, Counter] = defaultdict(Counter)
    for p in products:
        if p["brand"] and 1 < len(p["brand"].strip()) <= 30:
            spellings[p["brand"].strip().lower()][p["brand"].strip()] += 1
    known = {k: c.most_common(1)[0][0] for k, c in spellings.items() if sum(c.values()) >= 3}
    cards = {p["id"]: _card(p, shops_of, _brand(p, known)) for p in products}
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
        "images": _group_images(products, offers),
        "sections": sections,
        "syn": synonyms,
    }
    _dump(out / "data" / "meta.json", meta)

    # HTML shells and assets
    version = datetime.now().strftime("%Y%m%d%H%M")
    env = Environment(loader=FileSystemLoader(HERE / "site"), autoescape=True)
    site = {"CATEGORIES": CATEGORIES, "GROUPS": GROUPS, "GROUP_OF": GROUP_OF, "version": version, "ICONS": GROUP_ICONS,
            # Embedded in a <script type="application/json">: "</" must not end that element early.
            "config": json.dumps({"cats": CATEGORIES, "groups": GROUPS, "groupOf": GROUP_OF, "icons": GROUP_ICONS,
                                  "currency": settings["base_currency"], "contact": _scramble(settings.get("contact_email") or "")},
                                 ensure_ascii=False).replace("</", "<\\/")}
    for page in ("index", "product", "shops", "privacy", "404"):
        (out / f"{page}.html").write_text(env.get_template(f"{page}.html").render(page=page, **site), encoding="utf-8")
    for asset in ("style.css", "app.js", "init.js", "LICENSE-Lucide.txt"):
        shutil.copy(HERE / "static" / asset, out / "static" / asset)
    shutil.copytree(HERE / "static" / "fonts", out / "static" / "fonts")
    # Search engines: every category and product page, on the canonical host.
    site = settings.get("site_url", "https://www.compairsoft.eu").rstrip("/")
    today = date.today().isoformat()
    urls = [f"{site}/", f"{site}/shops", f"{site}/privacy"] + [f"{site}/?cat={c}" for c in list(GROUPS) + sorted(counts)]
    urls += [f"{site}/product/{p['id']}" for p in sorted(products, key=lambda p: -p["shop_count"])]
    chunks = [urls[i:i + 40000] for i in range(0, len(urls), 40000)]
    for n, chunk in enumerate(chunks, 1):
        (out / f"sitemap-{n}.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"<url><loc>{u.replace('&', '&amp;')}</loc><lastmod>{today}</lastmod></url>\n" for u in chunk)
            + "</urlset>\n", encoding="utf-8")
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<sitemap><loc>{site}/sitemap-{n}.xml</loc><lastmod>{today}</lastmod></sitemap>\n" for n in range(1, len(chunks) + 1))
        + "</sitemapindex>\n", encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site}/sitemap.xml\n", encoding="utf-8")
    (out / "_redirects").write_text("/product/*  /product  200\n", encoding="utf-8")
    (out / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()\n"
        "  Strict-Transport-Security: max-age=31536000; includeSubDomains\n"
        "  Cross-Origin-Opener-Policy: same-origin\n"
        f"  Content-Security-Policy: {CSP}\n"
        "/data/*\n  Cache-Control: public, max-age=600\n"
        "/static/*\n  Cache-Control: public, max-age=31536000, immutable\n", encoding="utf-8")
    files = sum(1 for f in out.rglob("*") if f.is_file())
    log.info("Exported %d products as %d files to %s", len(products), files, out)
