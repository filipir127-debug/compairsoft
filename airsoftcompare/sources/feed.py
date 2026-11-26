"""Read product XML feeds.

Supported formats (auto-detected):
  * Heureka / Zboží.cz   <SHOP><SHOPITEM><PRODUCTNAME>…
  * Google Merchant RSS  <rss><channel><item><g:title>…
  * Google Merchant Atom <feed><entry><g:title>…

Most Czech/Slovak e-shops already generate a Heureka or Zboží feed, so this is
the fastest and most reliable way to read a whole shop at once.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Iterator

from lxml import etree

from .common import Fetcher, Offer, clean_ean, parse_availability, parse_currency, parse_price

log = logging.getLogger(__name__)

ITEM_TAGS = {"SHOPITEM", "item", "entry"}


def _local(tag) -> str:
    return etree.QName(tag).localname if isinstance(tag, str) else ""


def _fields(el) -> dict[str, str]:
    out: dict[str, str] = {}
    for child in el:
        name = _local(child.tag).lower()
        if not name:
            continue
        text = (child.text or "").strip()
        if not text and name == "link":
            text = child.get("href", "")
        if text and name not in out:
            out[name] = text
    return out


def _to_offer(f: dict[str, str], default_currency: str) -> Offer | None:
    title = f.get("productname") or f.get("product") or f.get("title")
    url = f.get("url") or f.get("link")
    if not title or not url:
        return None
    raw_price = f.get("sale_price") or f.get("price_vat") or f.get("price")
    price = parse_price(raw_price)
    currency = f.get("currency") or parse_currency(raw_price, default_currency)
    avail = f.get("delivery_date") if "delivery_date" in f else f.get("availability")
    return Offer(
        url=url,
        title=title,
        price=price,
        currency=currency.upper(),
        in_stock=parse_availability(avail),
        ean=clean_ean(f.get("ean") or f.get("gtin")),
        brand=f.get("manufacturer") or f.get("brand"),
        image=f.get("imgurl") or f.get("image_link"),
        shop_category=f.get("categorytext") or f.get("product_type") or f.get("google_product_category"),
    )


def parse_feed(data: bytes, default_currency: str = "CZK") -> Iterator[Offer]:
    seen: dict[str, int] = {}
    for _, el in etree.iterparse(io.BytesIO(data), events=("end",), recover=True, huge_tree=True):
        if _local(el.tag) not in ITEM_TAGS:
            continue
        fields = _fields(el)
        offer = _to_offer(fields, default_currency)
        el.clear()
        if offer:
            # Variants (sizes, lengths) often share one product URL; keep them apart.
            n = seen[offer.url] = seen.get(offer.url, 0) + 1
            if n > 1:
                offer.url += "#" + (fields.get("item_id") or fields.get("id") or str(n))
            yield offer


def read_feed(fetcher: Fetcher, feed_url: str, default_currency: str = "CZK") -> Iterator[Offer]:
    path = Path(feed_url.removeprefix("file://"))
    if not feed_url.startswith(("http://", "https://")) and path.exists():
        data = path.read_bytes()
    else:
        # Feeds are meant for machine consumption, robots.txt rules for HTML pages don't apply.
        data = fetcher.get_bytes(feed_url, check_robots=False)
        if data is None:
            raise RuntimeError(f"could not download feed {feed_url}")
    yield from parse_feed(data, default_currency)
