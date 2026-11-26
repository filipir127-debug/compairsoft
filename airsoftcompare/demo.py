"""Sample data from four FICTIONAL shops, so the site can be tried without crawling anything.

Each shop writes product names its own way (Czech/English, different word order,
missing EANs…) to show how cross-shop matching works.  Creates demo/shops.yaml,
demo/feeds/*.xml and demo/airsoft-demo.db with 60 days of price history.
"""
from __future__ import annotations

import random
import zlib
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent / "demo"

# (canonical id, EAN or None, base price CZK, {shop: title})
CATALOG = [
    ("mask-v-tango", "0723758081501", 690, {"alfa": "Valken Tango maska - černá", "bravo": "Maska Valken Tango Black", "charlie": "VALKEN Tango Mask black", "delta": "Valken Tango Mask - Black"}),
    ("mesh-lower", None, 290, {"alfa": "Mesh maska spodní části obličeje V1 - olivová", "bravo": "Mesh lower face mask V1 olive", "charlie": "Mesh maska V1 OD"}),
    ("dye-i5", "0812184023451", 6490, {"bravo": "Dye i5 Thermal Goggle - Dyenamite", "delta": "DYE i5 Thermal Goggle Dyenamite"}),
    ("mag-m4-140", None, 249, {"alfa": "Mid-cap zásobník M4 140 ran - černý", "bravo": "Specna Arms M4 Mid-Cap 140 rds black", "charlie": "Zásobník mid-cap 140 rds pro M4/M16", "delta": "M4 Mid-Cap magazine 140 rds - black"}),
    ("mag-m4-300", None, 199, {"alfa": "Hi-cap zásobník M4 300 ran - černý", "bravo": "M4 Hi-Cap 300 rds black", "delta": "M4 Hi-Cap magazine 300 rds - black"}),
    ("mag-ak-130", None, 299, {"alfa": "Mid-cap zásobník AK 130 ran", "charlie": "AK Mid-Cap 130 rds magazine", "delta": "AK47 Mid-Cap magazine 130 rds"}),
    ("mag-glock-gas", "4710694591105", 990, {"alfa": "Plynový zásobník pro Glock 17 - GBB", "bravo": "Magazine for Glock 17 GBB gas", "charlie": "Zásobník Glock 17 GBB green gas"}),
    ("t1-red-dot", None, 1290, {"alfa": "Kolimátor T1 Red Dot s montáží - černý", "bravo": "T1 Red Dot s montáží black", "charlie": "Red dot T1 replica s montáží - černá", "delta": "T1 Red Dot sight with mount black"}),
    ("holo-552", None, 1590, {"alfa": "Holografický kolimátor 552 - tan", "bravo": "Holo 552 red dot sight - tan", "delta": "552 Holo sight red dot tan"}),
    ("magnifier-3x", None, 1490, {"bravo": "Magnifier 3x FTS flip - černý", "charlie": "Zvětšovač 3x FTS Magnifier black"}),
    ("rmr", None, 790, {"alfa": "RMR mini red dot - černý", "charlie": "Kolimátor RMR mini red dot black", "delta": "RMR mini red dot sight black"}),
    ("bbs-025", "5907583720011", 349, {"alfa": "Kuličky Specna Arms 0,25g 5000 ks", "bravo": "Specna Arms 0.25g BBs 5000 pcs", "charlie": "BB kuličky Specna Arms 0,25g 5000ks", "delta": "Specna Arms 0.25g BBs - 5000"}),
    ("bbs-030-bio", "5907583720080", 499, {"alfa": "Bio kuličky Specna Arms 0,30g 3500 ks", "bravo": "Specna Arms Bio 0.30g BBs 3500 pcs", "delta": "Specna Arms Bio 0.30g BBs - 3500"}),
    ("gas-green", None, 299, {"alfa": "Green gas Nimrod 500 ml", "bravo": "Nimrod Green Gas 500ml", "charlie": "Plyn Nimrod green gas 500 ml"}),
    ("lipo-1100", None, 549, {"alfa": "Akumulátor LiPo 7,4V 1100mAh 20C", "bravo": "LiPo baterie 7.4V 1100mAh 20C", "charlie": "Baterie LiPo 7,4V 1100 mAh 20C", "delta": "LiPo battery 7.4V 1100mAh 20C"}),
    ("charger-b3", None, 690, {"alfa": "Nabíječka LiPo B3 balancer", "charlie": "LiPo nabíječka B3 balanční"}),
    ("sa-e05", "5902543178017", 6990, {"alfa": "Specna Arms SA-E05 EDGE - černá", "bravo": "Specna Arms SA-E05 EDGE black", "charlie": "SA-E05 EDGE Specna Arms - černá", "delta": "Specna Arms SA-E05 EDGE Carbine Replica - black"}),
    ("sa-e07", "5902543178024", 7490, {"alfa": "Specna Arms SA-E07 EDGE - černá", "bravo": "Specna Arms SA-E07 EDGE black", "delta": "Specna Arms SA-E07 EDGE Carbine Replica - black"}),
    ("glock17", None, 3490, {"alfa": "Pistole Glock 17 GBB - černá", "bravo": "Glock 17 GBB pistol black", "charlie": "Glock 17 pistole GBB green gas černá"}),
    ("plate-carrier", None, 2290, {"alfa": "Nosič plátů JPC - multicam", "bravo": "JPC plate carrier multicam", "delta": "JPC Plate Carrier - multicam"}),
    ("chest-rig", None, 1490, {"bravo": "Chest rig Micro - olive", "charlie": "Hrudník micro chest rig - olivová"}),
    ("fast-helmet", None, 1190, {"alfa": "Helma FAST MH - tan", "bravo": "FAST MH helmet - tan", "charlie": "Přilba FAST MH písková", "delta": "FAST MH helmet replica - tan"}),
    ("gloves", None, 590, {"alfa": "Taktické rukavice Mechanix M-Pact - černé", "bravo": "Mechanix M-Pact gloves black", "delta": "Mechanix M-Pact Gloves - Black"}),
    ("mag-pouch", None, 349, {"alfa": "Sumka na zásobník M4 single - olive", "bravo": "Single M4 magazine pouch olive"}),
    ("hopup-rubber", None, 249, {"alfa": "Hop-up gumička 60°", "bravo": "Hop-up bucking 60°", "charlie": "Gumička hop-up 60°"}),
    ("spring-m120", None, 299, {"alfa": "Pružina M120", "charlie": "Upgrade pružina M120", "delta": "Spring M120"}),
    ("sling", None, 390, {"alfa": "Dvoubodový popruh - černý", "bravo": "Two point sling black"}),
    ("light", None, 990, {"bravo": "Svítilna M300 - černá", "charlie": "Weapon light M300 black", "delta": "M300 weapon light - black"}),
    ("smoke", None, 149, {"alfa": "Dýmovnice bílá", "charlie": "Dýmovnice - bílá"}),
]

SHOPS = {
    "alfa": ("Demo Shop Alfa", "heureka", "CZK", 1.00),
    "bravo": ("Demo Shop Bravo", "heureka", "CZK", 0.96),
    "charlie": ("Demo Shop Charlie", "heureka", "CZK", 1.04),
    "delta": ("Demo Shop Delta (SK)", "google", "EUR", 0.98),
}


def _heureka(items) -> str:
    out = ['<?xml version="1.0" encoding="utf-8"?>\n<SHOP>']
    for it in items:
        out.append(f"""  <SHOPITEM>
    <ITEM_ID>{it['id']}</ITEM_ID>
    <PRODUCTNAME>{escape(it['title'])}</PRODUCTNAME>
    <URL>{it['url']}</URL>
    <PRICE_VAT>{it['price']:.0f}</PRICE_VAT>
    {f"<EAN>{it['ean']}</EAN>" if it['ean'] else ''}
    <DELIVERY_DATE>{0 if it['stock'] else 14}</DELIVERY_DATE>
  </SHOPITEM>""")
    out.append("</SHOP>\n")
    return "\n".join(out)


def _google(items) -> str:
    out = ['<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel>',
           "<title>Demo Shop Delta</title>"]
    for it in items:
        out.append(f"""<item><g:id>{it['id']}</g:id><g:title>{escape(it['title'])}</g:title>
<g:link>{it['url']}</g:link><g:price>{it['price']:.2f} EUR</g:price>
<g:availability>{'in_stock' if it['stock'] else 'out_of_stock'}</g:availability>{f"<g:gtin>{it['ean']}</g:gtin>" if it['ean'] else ''}</item>""")
    out.append("</channel></rss>\n")
    return "\n".join(out)


def load_demo(days: int = 60) -> None:
    from . import config as cfgmod
    from . import db as dbmod
    from .matching import rebuild_products
    from .sources.feed import read_feed
    from .sources.common import Fetcher
    from .updater import save_offer, _shop_id

    rng = random.Random(42)
    (ROOT / "feeds").mkdir(parents=True, exist_ok=True)
    yaml_lines = ["# Generated by `python -m airsoftcompare demo` – fictional shops only.",
                  "settings:", "  database: airsoft-demo.db", "  exchange_rates: {EUR: 25.0}", "shops:"]
    for key, (name, fmt, cur, _) in SHOPS.items():
        yaml_lines += [f"  - name: {name}", f"    url: https://{key}.example", "    type: feed",
                       f"    feed_url: feeds/{key}.xml", f"    currency: {cur}"]
    (ROOT / "shops.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
    db_path = ROOT / "airsoft-demo.db"
    for suffix in ("", "-wal", "-shm"):
        Path(str(db_path) + suffix).unlink(missing_ok=True)

    cfg = cfgmod.load(ROOT / "shops.yaml")
    conn = dbmod.connect(cfg["settings"]["database"])
    fetcher = Fetcher("demo", 0, 5, False)

    # Each product gets a random-walk price per shop; write each day's feed and import it.
    walk = {(pid, s): 1.0 for pid, *_ in CATALOG for s in SHOPS}
    today = date.today()
    for d in range(days - 1, -1, -1):
        day = (today - timedelta(days=d)).isoformat()
        for key, (name, fmt, cur, factor) in SHOPS.items():
            items = []
            for pid, ean, base, titles in CATALOG:
                if key not in titles:
                    continue
                w = walk[(pid, key)] = min(1.25, max(0.8, walk[(pid, key)] * rng.choice([1, 1, 1, 1, 0.97, 1.03, 0.92])))
                price = base * factor * w * rng.uniform(0.97, 1.03) if d == days - 1 else base * factor * w
                price = round(price / 25, 2) if cur == "EUR" else round(price / 10) * 10 - 1
                items.append(dict(id=pid, title=titles[key], url=f"https://{key}.example/p/{pid}",
                                  price=price, ean=ean,
                                  stock=rng.random() > 0.12))
            # Some shops leave out EANs, so matching has to fall back to titles.
            for it in items:
                if it["ean"] and zlib.crc32(f"{key}{it['id']}".encode()) % 3 == 0 and key != "alfa":
                    it["ean"] = None
            (ROOT / "feeds" / f"{key}.xml").write_text(_heureka(items) if fmt == "heureka" else _google(items), encoding="utf-8")
            shop = next(s for s in cfg["shops"] if s["name"] == name)
            sid = _shop_id(conn, shop)
            for o in read_feed(fetcher, shop["feed_url"], cur):
                save_offer(conn, sid, o, cfg["settings"]["exchange_rates"], day=day)
    with conn:
        for s in cfg["shops"]:
            conn.execute("UPDATE shops SET last_update = datetime('now','localtime'), last_status = 'ok (demo)', "
                         "offer_count = (SELECT COUNT(*) FROM offers o WHERE o.shop_id = shops.id) WHERE name = ?", (s["name"],))
    n = rebuild_products(conn, cfg["settings"]["match_threshold"])
    offers = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    print(f"Demo loaded: {offers} offers from {len(SHOPS)} fictional shops → {n} products "
          f"(catalogue has {len(CATALOG)} real products).")
    print("Start the site with:\n  python -m airsoftcompare -c demo/shops.yaml serve")
