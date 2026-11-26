"""Crawl a shop through its sitemap and read schema.org Product data from each page.

Nearly every modern e-shop (Shoptet, Shopify, WooCommerce, PrestaShop, Magento,
Upgates…) embeds JSON-LD `Product` data for Google, so one generic parser covers
most shops without any per-shop code.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Callable, Iterable, Iterator
from urllib.parse import urljoin

from lxml import etree, html

from .common import Fetcher, Offer, clean_ean, parse_availability, parse_currency, parse_price

log = logging.getLogger(__name__)


# ---------------------------------------------------------------- sitemaps

def find_sitemaps(fetcher: Fetcher, base_url: str) -> list[str]:
    r = fetcher.get(urljoin(base_url, "/robots.txt"), check_robots=False)
    found = []
    if r is not None:
        found = [line.split(":", 1)[1].strip() for line in r.text.splitlines()
                 if line.lower().startswith("sitemap:")]
    return found or [urljoin(base_url, "/sitemap.xml")]


def iter_sitemap(fetcher: Fetcher, url: str, depth: int = 0) -> Iterator[str]:
    data = fetcher.get_bytes(url, check_robots=False)
    if not data or depth > 4:
        return
    try:
        root = etree.fromstring(data, parser=etree.XMLParser(recover=True, huge_tree=True))
    except etree.XMLSyntaxError:
        return
    if root is None:
        return
    is_index = etree.QName(root).localname == "sitemapindex"
    locs = [el.text.strip() for el in root.iter() if etree.QName(el).localname == "loc" and el.text]
    for loc in locs:
        if is_index:
            yield from iter_sitemap(fetcher, loc, depth + 1)
        else:
            yield loc


# ---------------------------------------------------------------- product pages

def _walk(obj) -> Iterator[dict]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _is_type(node: dict, name: str) -> bool:
    t = node.get("@type")
    return t == name or (isinstance(t, list) and name in t)


def _first(v):
    if isinstance(v, list):
        return v[0] if v else None
    return v


def _text(v):
    v = _first(v)
    if isinstance(v, dict):
        return v.get("name") or v.get("url") or v.get("@id")
    return v


def _offer_from_jsonld(node: dict, page_url: str, default_currency: str) -> Offer | None:
    name = node.get("name")
    offers = [o for o in _walk(node.get("offers") or []) if _is_type(o, "Offer") or _is_type(o, "AggregateOffer") or "price" in o]
    price = currency = avail = None
    for o in offers:
        spec = _first(o.get("priceSpecification"))
        p = parse_price(o.get("price") or o.get("lowPrice") or (spec.get("price") if isinstance(spec, dict) else None))
        if p is not None and (price is None or p < price):
            price, currency, avail = p, o.get("priceCurrency"), o.get("availability")
    if not name or price is None:
        return None
    ean = next((node.get(k) for k in ("gtin13", "gtin", "ean", "gtin14", "gtin12", "gtin8") if node.get(k)), None)
    return Offer(
        url=page_url,
        title=str(name).strip(),
        price=price,
        currency=(currency or default_currency).upper(),
        in_stock=parse_availability(avail),
        ean=clean_ean(ean),
        brand=_text(node.get("brand")),
        image=urljoin(page_url, _text(node.get("image"))) if node.get("image") else None,
        shop_category=_text(node.get("category")),
    )


def extract_product(page: str | bytes, page_url: str, default_currency: str = "CZK") -> Offer | None:
    """Return the product on a page, or None when the page isn't a product page."""
    try:
        doc = html.fromstring(page)
    except (etree.ParserError, ValueError):
        return None

    for script in doc.xpath('//script[@type="application/ld+json"]'):
        raw = (script.text or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw, strict=False)
        except json.JSONDecodeError:
            continue
        for node in _walk(data):
            if _is_type(node, "Product"):
                offer = _offer_from_jsonld(node, page_url, default_currency)
                if offer:
                    return offer

    # Fallback: OpenGraph / microdata meta tags.
    def meta(*names):
        for n in names:
            v = doc.xpath(f'//meta[@property="{n}" or @name="{n}" or @itemprop="{n}"]/@content')
            if v:
                return v[0].strip()
        return None

    price_raw = meta("product:price:amount", "og:price:amount", "price")
    title = meta("og:title") or (doc.findtext(".//title") or "").strip()
    if price_raw is None or not title:
        return None
    return Offer(
        url=page_url,
        title=title,
        price=parse_price(price_raw),
        currency=(meta("product:price:currency", "og:price:currency", "priceCurrency")
                  or parse_currency(price_raw, default_currency)).upper(),
        in_stock=parse_availability(meta("product:availability", "og:availability", "availability")),
        ean=clean_ean(meta("product:ean", "gtin13", "gtin")),
        brand=meta("product:brand", "og:brand", "brand"),
        image=meta("og:image"),
    )


def crawl(fetcher: Fetcher, shop: dict, default_currency: str = "CZK",
          skip: Callable[[str], bool] = lambda u: False) -> Iterator[Offer]:
    """Yield offers found by walking the shop's sitemap(s)."""
    sitemaps = shop.get("sitemap_urls") or ([shop["sitemap_url"]] if shop.get("sitemap_url") else None)
    sitemaps = sitemaps or find_sitemaps(fetcher, shop["url"])
    include = re.compile(shop["include"]) if shop.get("include") else None
    exclude = re.compile(shop["exclude"]) if shop.get("exclude") else None
    max_pages = int(shop.get("max_pages", 3000))

    seen: set[str] = set()
    fetched = 0
    for sm in sitemaps:
        for url in iter_sitemap(fetcher, sm):
            if url in seen or (include and not include.search(url)) or (exclude and exclude.search(url)):
                continue
            seen.add(url)
            if skip(url):
                continue
            if fetched >= max_pages:
                log.info("%s: reached max_pages=%d", shop["name"], max_pages)
                return
            fetched += 1
            r = fetcher.get(url)
            if r is None:
                continue
            offer = extract_product(r.content, r.url, default_currency)
            if offer:
                yield offer


def probe_feed_urls(base_url: str) -> Iterable[str]:
    for path in ("/heureka.xml", "/heureka/export/products.xml", "/export/heureka.xml",
                 "/zbozi.xml", "/feed/heureka.xml", "/google.xml", "/export/products.xml",
                 "/feeds/heureka.xml", "/xml/heureka.xml"):
        yield urljoin(base_url, path)
