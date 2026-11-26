"""Download every configured shop and store its offers."""
from __future__ import annotations

import logging
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

from . import db as dbmod
from .categories import categorize
from .matching import rebuild_products
from .sources import feed, sitemap
from .sources.common import Fetcher, Offer
from .text import normalize

log = logging.getLogger(__name__)
_write_lock = threading.Lock()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _shop_id(conn: sqlite3.Connection, shop: dict) -> int:
    with _write_lock, conn:
        conn.execute("INSERT INTO shops(name, url, type) VALUES (?,?,?) "
                     "ON CONFLICT(name) DO UPDATE SET url = excluded.url, type = excluded.type",
                     (shop["name"], shop.get("url"), shop.get("type")))
        return conn.execute("SELECT id FROM shops WHERE name = ?", (shop["name"],)).fetchone()[0]


def save_offer(conn: sqlite3.Connection, shop_id: int, o: Offer, rates: dict, day: str | None = None) -> None:
    rate = rates.get(o.currency.upper())
    price_base = round(o.price * rate, 2) if (o.price is not None and rate) else None
    now = _now()
    with _write_lock, conn:
        conn.execute("""
            INSERT INTO offers (shop_id, url, title, norm_title, price, currency, price_base, in_stock,
                                ean, brand, image, shop_category, category, active, first_seen, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)
            ON CONFLICT(shop_id, url) DO UPDATE SET
                title=excluded.title, norm_title=excluded.norm_title, price=excluded.price,
                currency=excluded.currency, price_base=excluded.price_base, in_stock=excluded.in_stock,
                ean=COALESCE(excluded.ean, offers.ean), brand=COALESCE(excluded.brand, offers.brand),
                image=COALESCE(excluded.image, offers.image), shop_category=excluded.shop_category,
                category=excluded.category, active=1, updated_at=excluded.updated_at
        """, (shop_id, o.url, o.title, normalize(o.title), o.price, o.currency, price_base,
              None if o.in_stock is None else int(o.in_stock), o.ean, o.brand, o.image,
              o.shop_category, categorize(o.title, o.shop_category), now, now))
        if price_base is not None:
            oid = conn.execute("SELECT id FROM offers WHERE shop_id=? AND url=?", (shop_id, o.url)).fetchone()[0]
            conn.execute("INSERT OR REPLACE INTO price_history VALUES (?,?,?)",
                         (oid, day or date.today().isoformat(), price_base))


def update_shop(conn: sqlite3.Connection, shop: dict, settings: dict) -> tuple[int, str]:
    shop_id = _shop_id(conn, shop)
    fetcher = Fetcher(settings["user_agent"], float(shop.get("request_delay", settings["request_delay"])),
                      float(shop.get("timeout", settings["timeout"])), settings["respect_robots"])
    currency = shop.get("currency", settings["base_currency"])
    started = _now()
    count = 0
    try:
        if shop.get("type") == "feed":
            offers = feed.read_feed(fetcher, shop["feed_url"], currency)
        elif shop.get("type") == "sitemap":
            cutoff = (datetime.now() - timedelta(hours=settings["recrawl_hours"])).isoformat(timespec="seconds")
            fresh = {r[0] for r in conn.execute(
                "SELECT url FROM offers WHERE shop_id = ? AND active = 1 AND updated_at > ?", (shop_id, cutoff))}
            offers = sitemap.crawl(fetcher, shop, currency, skip=fresh.__contains__)
        else:
            raise ValueError(f"unknown shop type {shop.get('type')!r} (use 'feed' or 'sitemap')")

        for o in offers:
            save_offer(conn, shop_id, o, settings["exchange_rates"])
            count += 1
            if count % 500 == 0:
                log.info("%s: %d offers…", shop["name"], count)
                _rematch(conn, settings)

        with _write_lock, conn:
            if shop.get("type") == "feed" and count:
                # A feed is the complete catalogue: anything missing from it is gone.
                conn.execute("UPDATE offers SET active = 0 WHERE shop_id = ? AND updated_at < ?", (shop_id, started))
            elif shop.get("type") == "sitemap":
                # Pages not seen for a week are treated as removed.
                week = (datetime.now() - timedelta(days=7)).isoformat(timespec="seconds")
                conn.execute("UPDATE offers SET active = 0 WHERE shop_id = ? AND updated_at < ?", (shop_id, week))
        status = f"ok: {count} offers read"
    except Exception as e:  # keep other shops running
        log.exception("%s failed", shop["name"])
        status = f"error: {e}"

    with _write_lock, conn:
        total = conn.execute("SELECT COUNT(*) FROM offers WHERE shop_id = ? AND active = 1", (shop_id,)).fetchone()[0]
        conn.execute("UPDATE shops SET last_update = ?, last_status = ?, offer_count = ? WHERE id = ?",
                     (_now(), status, total, shop_id))
    log.info("%s: %s", shop["name"], status)
    return count, status


def _rematch(conn: sqlite3.Connection, settings: dict) -> None:
    with _write_lock:
        n = rebuild_products(conn, settings["match_threshold"])
    log.info("Matched offers into %d products.", n)


def update_all(cfg: dict, only: list[str] | None = None) -> None:
    settings = cfg["settings"]
    conn = dbmod.connect(settings["database"])
    shops = [s for s in cfg["shops"] if not only or s["name"] in only]
    if not shops:
        log.warning("No enabled shops in config.")
    _rematch(conn, settings)
    with ThreadPoolExecutor(max_workers=max(1, int(settings["parallel_shops"]))) as pool:
        list(pool.map(lambda s: update_shop(conn, s, settings), shops))
    _rematch(conn, settings)
