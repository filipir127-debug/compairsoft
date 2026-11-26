"""Regression tests for the fixes in docs/AUDIT.md."""
import gzip
import logging

import pytest

from airsoftcompare import db, matching
from airsoftcompare.sources import common
from airsoftcompare.sources.common import clean_ean, safe_url
from airsoftcompare.sources.feed import parse_feed
from airsoftcompare.sources.sitemap import extract_product


# ---------------------------------------------------------------- URL safety (S1)

def test_safe_url():
    assert safe_url("https://shop.cz/p") == "https://shop.cz/p"
    assert safe_url("/img/a.jpg", "https://shop.cz/p/1") == "https://shop.cz/img/a.jpg"
    for bad in ("javascript:alert(1)", " JavaScript:alert(1)", "data:text/html,x", "vbscript:x", "//", "", None):
        assert safe_url(bad) is None
    assert safe_url("javascript:alert(1)", "https://shop.cz/") is None


def test_feed_drops_script_links_and_images():
    feed = b"""<SHOP>
      <SHOPITEM><PRODUCTNAME>Evil</PRODUCTNAME><URL>javascript:alert(1)</URL><PRICE_VAT>1</PRICE_VAT></SHOPITEM>
      <SHOPITEM><PRODUCTNAME>Ok</PRODUCTNAME><URL>https://a.cz/ok</URL><PRICE_VAT>1</PRICE_VAT>
        <IMGURL>javascript:alert(2)</IMGURL></SHOPITEM></SHOP>"""
    (o,) = parse_feed(feed)
    assert o.title == "Ok" and o.image is None


# ---------------------------------------------------------------- XML entities (S2)

BOMB = (b'<?xml version="1.0"?><!DOCTYPE s [<!ENTITY a "AAAAAAAAAA">'
        b'<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;"><!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">]>'
        b'<SHOP><SHOPITEM><PRODUCTNAME>X&c;</PRODUCTNAME><URL>https://a.cz/x</URL><PRICE_VAT>1</PRICE_VAT>'
        b'</SHOPITEM></SHOP>')


def test_feed_does_not_expand_entities():
    offers = list(parse_feed(BOMB))
    assert all(len(o.title) < 50 for o in offers)


# ---------------------------------------------------------------- download caps (S3)

def test_gunzip_cap(monkeypatch):
    monkeypatch.setattr(common, "MAX_DOWNLOAD_BYTES", 1000)
    assert common._gunzip(gzip.compress(b"x" * 500), "u") == b"x" * 500
    assert common._gunzip(gzip.compress(b"x" * 5000), "u") is None


# ---------------------------------------------------------------- EAN / GTIN (B2)

def test_gtin14_with_leading_zero_equals_ean13():
    assert clean_ean("05902543178017") == clean_ean("5902543178017") == "5902543178017"
    assert clean_ean("15902543178014") == "15902543178014"  # a real GTIN-14 stays as is


# ---------------------------------------------------------------- relative images (B3)

def test_microdata_relative_image_is_absolute():
    page = """<html><body><div itemscope itemtype="https://schema.org/Product"><h1 itemprop="name">N</h1>
      <img itemprop="image" src="/i.jpg"><span itemprop="price" content="5"></span></div></body></html>"""
    assert extract_product(page, "https://s.cz/p/1").image == "https://s.cz/i.jpg"


def test_og_relative_image_is_absolute():
    page = """<html><head><meta property="og:title" content="G"><meta property="og:image" content="img/g.png">
      <meta property="product:price:amount" content="5"></head></html>"""
    assert extract_product(page, "https://s.cz/p/1").image == "https://s.cz/p/img/g.png"


# ---------------------------------------------------------------- product id collision (B1)

def _conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    c.execute("INSERT INTO shops(id, name) VALUES (1, 'A'), (2, 'B')")
    return c


def test_groups_with_same_anchor_get_distinct_ids(tmp_path):
    c = _conn(tmp_path)
    # Same shop, same title, different categories → two groups with the same title anchor.
    for oid, cat in ((1, "masks"), (2, "helmets")):
        c.execute("INSERT INTO offers(id, shop_id, url, title, norm_title, price_base, category, in_stock) "
                  "VALUES (?, 1, ?, 'Mask X', 'mask x', 100, ?, 1)", (oid, f"u{oid}", cat))
    c.commit()
    assert matching.rebuild_products(c, 90) == 2
    assert c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 2
    assert c.execute("SELECT COUNT(DISTINCT product_id) FROM offers").fetchone()[0] == 2
    first = dict(c.execute("SELECT id, product_id FROM offers").fetchall())
    matching.rebuild_products(c, 90)
    assert dict(c.execute("SELECT id, product_id FROM offers").fetchall()) == first  # stable ids


# ---------------------------------------------------------------- web (S1, S4, S5, B4, B5)

@pytest.fixture
def client(tmp_path):
    from fastapi.testclient import TestClient
    from airsoftcompare.web import create_app

    (tmp_path / "shops.yaml").write_text(
        "settings: {database: t.db}\nshops:\n  - {name: A, url: 'https://a.cz', type: feed, feed_url: x}\n",
        encoding="utf-8")
    c = _conn(tmp_path)
    # A row stored before the URL checks existed.
    c.execute("INSERT INTO offers(id, shop_id, url, title, norm_title, price, currency, price_base, "
              "category, in_stock, product_id) VALUES (1, 1, 'javascript:alert(1)', 'Mask', 'mask', 4, 'EUR', 100, "
              "'masks', 1, 'p1')")
    c.execute("INSERT INTO products VALUES ('p1', 'Mask', 'mask', 'masks', NULL, 'javascript:x', NULL, 100, 100, 1, 1)")
    c.commit()
    return TestClient(create_app(str(tmp_path / "shops.yaml")))


def test_product_page_neutralises_stored_script_urls(client):
    r = client.get("/product/p1")
    assert r.status_code == 200
    assert "javascript:" not in r.text
    assert r.headers["x-content-type-options"] == "nosniff"


def test_api_rejects_unbounded_limit_and_page(client):
    assert client.get("/api/products?limit=-1").status_code == 422
    assert client.get("/api/products?limit=0").status_code == 422
    assert client.get("/api/products?page=99999999999999999").status_code == 422
    assert client.get("/api/products?limit=10").json()["total"] == 1


def test_nan_price_filter_is_ignored(client):
    r = client.get("/?pmin=nan")
    assert r.status_code == 200 and "Mask" in r.text


def test_disabled_shops_are_not_listed(client):
    r = client.get("/shops")
    assert ">A<" in r.text and ">B<" not in r.text


def test_update_hides_offers_of_unlisted_shops(tmp_path):
    from airsoftcompare.updater import _hide_unlisted_shops
    c = _conn(tmp_path)
    for oid, sid in ((1, 1), (2, 2)):
        c.execute("INSERT INTO offers(id, shop_id, url, title, norm_title) VALUES (?, ?, ?, 't', 't')", (oid, sid, f"u{oid}"))
    c.commit()
    _hide_unlisted_shops(c, [{"name": "A"}])
    assert dict(c.execute("SELECT id, active FROM offers").fetchall()) == {1: 1, 2: 0}


def test_unknown_currency_warns_once(tmp_path, caplog):
    from airsoftcompare.sources.common import Offer
    from airsoftcompare.updater import _warned_currencies, save_offer
    _warned_currencies.discard("XYZ")
    c = _conn(tmp_path)
    with caplog.at_level(logging.WARNING):
        for i in range(3):
            save_offer(c, 1, Offer(url=f"https://a.cz/{i}", title="t", price=1, currency="XYZ"), {"CZK": 1})
    assert sum("XYZ" in m for m in caplog.messages) == 1


# ---------------------------------------------------------------- Fetcher caps (S3, robots.txt)

class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers: dict | None = None):
        import requests
        self._r = requests.Response()
        self._r.status_code, self._r.url, self._r.encoding = status, "https://a.cz/x", "utf-8"
        self._r.headers.update(headers or {})
        self._body = body
        self._r.iter_content = lambda size: (body[i:i + size] for i in range(0, len(body), size))
        self._r.close = lambda: None


def _fetcher(monkeypatch, responses: dict):
    f = common.Fetcher("test", 0, 5, respect_robots=True)
    monkeypatch.setattr(f.session, "get", lambda url, **kw: responses[url]._r)
    return f


def test_fetcher_caps_body_and_keeps_small_ones(monkeypatch):
    monkeypatch.setattr(common, "MAX_DOWNLOAD_BYTES", 1000)
    f = _fetcher(monkeypatch, {"https://a.cz/small": _FakeResponse(b"hello"),
                               "https://a.cz/big": _FakeResponse(b"x" * 5000),
                               "https://a.cz/announced": _FakeResponse(b"x", headers={"Content-Length": "999999"})})
    r = f.get("https://a.cz/small", check_robots=False)
    assert r.content == b"hello" and r.text == "hello"
    assert f.get("https://a.cz/big", check_robots=False) is None
    assert f.get("https://a.cz/announced", check_robots=False) is None


def test_robots_txt_is_capped(monkeypatch):
    monkeypatch.setattr(common, "MAX_ROBOTS_BYTES", 100)
    huge = b"User-agent: *\nDisallow: /\n" + b"#" * 1000
    f = _fetcher(monkeypatch, {"https://a.cz/robots.txt": _FakeResponse(huge, headers={"Content-Length": "999999"})})
    assert f.allowed("https://a.cz/p") is False  # oversized file is cut, its beginning still obeyed
    r = f._fetch("https://a.cz/robots.txt", 100, truncate=True)
    assert r.content == b"User-agent: *\nDisallow: /\n"  # cut at the cap, then back to the last full line


def test_truncated_robots_drops_partial_last_line(monkeypatch):
    body = b"User-agent: *\nAllow: /shop/private-ok\nDisallow: /\n"
    f = _fetcher(monkeypatch, {"https://a.cz/robots.txt": _FakeResponse(body)})
    r = f._fetch("https://a.cz/robots.txt", body.index(b"/shop") + 1, truncate=True)  # cut to "Allow: /"
    assert r.content == b"User-agent: *\n"


def test_broken_gzip_does_not_raise():
    assert common._gunzip(gzip.compress(b"x" * 100)[:15], "u") is None


# ---------------------------------------------------------------- sitemap entities, JSON-LD image

def test_sitemap_does_not_expand_entities(monkeypatch):
    from airsoftcompare.sources import sitemap
    xml = (b'<?xml version="1.0"?><!DOCTYPE u [<!ENTITY a "AAAAAAAAAA"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>'
           b'<urlset><url><loc>https://a.cz/&b;</loc></url><url><loc>https://a.cz/p</loc></url></urlset>')

    class F:
        def get_bytes(self, url, check_robots=True):
            return xml
    assert all(len(u) < 40 for u in sitemap.iter_sitemap(F(), "https://a.cz/sitemap.xml"))


def test_jsonld_unsafe_image_dropped():
    page = """<html><head><script type="application/ld+json">{"@type":"Product","name":"N","image":"javascript:x",
      "offers":{"price":"5"}}</script></head></html>"""
    assert extract_product(page, "https://s.cz/p").image is None


# ---------------------------------------------------------------- updater guards

def test_empty_shop_list_hides_nothing(tmp_path):
    from airsoftcompare.updater import _hide_unlisted_shops
    c = _conn(tmp_path)
    c.execute("INSERT INTO offers(id, shop_id, url, title, norm_title) VALUES (1, 1, 'u', 't', 't')")
    c.commit()
    _hide_unlisted_shops(c, [])
    assert c.execute("SELECT active FROM offers").fetchone()[0] == 1


def test_invalid_currency_not_echoed(tmp_path, caplog):
    from airsoftcompare.sources.common import Offer
    from airsoftcompare.updater import save_offer
    c = _conn(tmp_path)
    with caplog.at_level(logging.WARNING):
        save_offer(c, 1, Offer(url="https://a.cz/1", title="t", price=1, currency="X\nFAKE LOG LINE"), {"CZK": 1})
    assert not any("FAKE LOG LINE" in m for m in caplog.messages)


def test_sitemap_with_comment_is_read():
    from airsoftcompare.sources import sitemap

    class F:
        def get_bytes(self, url, check_robots=True):
            return b'<urlset><!-- generated by plugin --><url><loc>https://a.cz/p</loc></url></urlset>'
    assert list(sitemap.iter_sitemap(F(), "https://a.cz/sitemap.xml")) == ["https://a.cz/p"]
