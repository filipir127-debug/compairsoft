from airsoftcompare.categories import categorize
from airsoftcompare.matching import cluster
from airsoftcompare.sources.common import clean_ean, parse_availability, parse_price
from airsoftcompare.sources.feed import parse_feed
from airsoftcompare.sources.sitemap import extract_product
from airsoftcompare.text import normalize


def test_parse_price():
    assert parse_price("1 299 Kč") == 1299
    assert parse_price("1\xa0299,00 Kč") == 1299
    assert parse_price("1.299,50 €") == 1299.5
    assert parse_price("1299.00 CZK") == 1299
    assert parse_price("1,299.00") == 1299
    assert parse_price("12.990") == 12990
    assert parse_price("49,9") == 49.9
    assert parse_price(349) == 349
    assert parse_price("zdarma") is None


def test_availability_and_ean():
    assert parse_availability("0") is True
    assert parse_availability("https://schema.org/InStock") is True
    assert parse_availability("out_of_stock") is False
    assert parse_availability("Není skladem") is False
    assert parse_availability("14") is False
    assert clean_ean("723758081501") == "0723758081501"
    assert clean_ean("0000000000000") is None


def test_categories():
    assert categorize("Valken Tango maska - černá") == "masks"
    assert categorize("Sumka na zásobník M4") == "pouches"
    assert categorize("Mid-cap zásobník M4 140 ran") == "magazines"
    assert categorize("Kolimátor T1 Red Dot") == "optics"
    assert categorize("Pistole Glock 17 GBB green gas") == "pistols"
    assert categorize("Green gas Nimrod 500 ml") == "gas"
    assert categorize("Gearbox V2 pro M4") == "parts"
    assert categorize("Specna Arms SA-E05 EDGE", "Airsoftové zbraně | Útočné pušky") == "guns"
    assert categorize("Něco neznámého") == "other"


def _offers(*rows):
    return [dict(shop_id=s, ean=e, norm_title=normalize(t), category=categorize(t)) for s, t, e in rows]


def test_matching_merges_variants_of_same_name():
    groups = cluster(_offers(
        (1, "Valken Tango maska - černá", None),
        (2, "Maska Valken Tango Black", None),
        (3, "VALKEN Tango Mask black", None),
    ))
    assert len(set(groups)) == 1


def test_matching_respects_numbers_colors_and_shops():
    groups = cluster(_offers(
        (1, "M4 Mid-Cap zásobník 120 ran", None),
        (2, "M4 Mid-Cap magazine 140 rds", None),
        (3, "FAST helma - černá", None),
        (4, "FAST helmet - tan", None),
        (5, "Specna Arms SA-E05 EDGE", None),
        (5, "Specna Arms SA-E05 EDGE black", None),  # same shop twice → different variants
    ))
    assert len(set(groups)) == 6


def test_matching_by_ean():
    groups = cluster(_offers((1, "Something", "5902543178017"), (2, "Totally different name", "5902543178017")))
    assert groups[0] == groups[1]


def test_heureka_and_google_feeds():
    heureka = b"""<?xml version="1.0"?><SHOP><SHOPITEM><PRODUCTNAME>Maska X</PRODUCTNAME>
      <URL>https://a.cz/x</URL><PRICE_VAT>690</PRICE_VAT><EAN>723758081501</EAN><DELIVERY_DATE>0</DELIVERY_DATE>
      </SHOPITEM></SHOP>"""
    (o,) = parse_feed(heureka)
    assert (o.title, o.price, o.in_stock, o.ean) == ("Maska X", 690, True, "0723758081501")

    google = b"""<rss xmlns:g="http://base.google.com/ns/1.0"><channel><item>
      <g:title>Mask Y</g:title><g:link>https://b.sk/y</g:link><g:price>27.60 EUR</g:price>
      <g:availability>out of stock</g:availability></item></channel></rss>"""
    (o,) = parse_feed(google)
    assert (o.title, o.price, o.currency, o.in_stock) == ("Mask Y", 27.6, "EUR", False)


def test_jsonld_product_page():
    page = """<html><head><script type="application/ld+json">
      {"@context":"https://schema.org","@graph":[{"@type":"WebPage"},{"@type":"Product","name":"T1 Red Dot",
       "gtin13":"5902543178017","brand":{"@type":"Brand","name":"Specna"},"image":["/img/t1.jpg"],
       "offers":{"@type":"Offer","price":"1290.00","priceCurrency":"CZK","availability":"https://schema.org/InStock"}}]}
      </script></head><body></body></html>"""
    o = extract_product(page, "https://shop.cz/t1")
    assert o.title == "T1 Red Dot" and o.price == 1290 and o.in_stock and o.brand == "Specna"
    assert o.image == "https://shop.cz/img/t1.jpg"
    assert extract_product("<html><title>Blog</title></html>", "https://shop.cz/blog") is None


def test_opengraph_fallback():
    page = """<html><head><meta property="og:title" content="Gloves">
      <meta property="product:price:amount" content="590"><meta property="product:price:currency" content="CZK">
      </head></html>"""
    o = extract_product(page, "https://shop.cz/g")
    assert o.title == "Gloves" and o.price == 590


def test_microdata_availability_link():
    from airsoftcompare.sources.sitemap import extract_product
    page = b"""<html><head><meta property="og:title" content="Hop-up rubber"></head><body>
    <span itemprop="offers" itemscope itemtype="https://schema.org/Offer">
    <meta itemprop="price" content="79"><meta itemprop="priceCurrency" content="CZK">
    <link itemprop="availability" href="https://schema.org/InStock" /></span></body></html>"""
    o = extract_product(page, "https://shop.example/p")
    assert o.price == 79 and o.in_stock is True


def test_microdata_ignores_related_products():
    from airsoftcompare.sources.sitemap import extract_product
    page = """<html><head><meta charset="utf-8"><meta property="og:title" content="Tlumič 32 × 150 mm – Černá"></head><body>
    <div itemscope itemtype="https://schema.org/Product"><h1 itemprop="name">Tlumič 32 × 150 mm</h1>
      <div itemprop="offers" itemscope itemtype="https://schema.org/Offer">
        <span itemprop="price" content="1190">1 190 Kč</span><meta itemprop="priceCurrency" content="CZK"></div>
      <span id="availability_value">Není skladem</span>
      <ul><li itemscope itemtype="https://schema.org/Product"><span itemprop="name">Related</span>
        <div itemprop="offers" itemscope itemtype="https://schema.org/Offer"><span itemprop="price" content="98"></span>
        <link itemprop="availability" href="https://schema.org/InStock"></div></li></ul>
    </div></body></html>""".encode()
    o = extract_product(page, "https://shop.example/p")
    assert (o.title, o.price, o.in_stock) == ("Tlumič 32 × 150 mm – Černá", 1190, False)


def test_export_sanitises_urls_and_hides_unlisted_shops(tmp_path):
    import json
    from airsoftcompare import db as dbmod
    from airsoftcompare.export import export_site
    from airsoftcompare.matching import rebuild_products
    from airsoftcompare.sources.common import Offer
    from airsoftcompare.updater import _shop_id, save_offer
    dbfile = tmp_path / "t.db"
    conn = dbmod.connect(str(dbfile))
    rates = {"CZK": 1.0}
    for name in ("Kept", "Removed"):
        sid = _shop_id(conn, {"name": name, "url": "https://x.cz", "type": "feed"})
        save_offer(conn, sid, Offer(url=f"https://{name}.cz/m4", title="M4 mid-cap zásobník 120 ran",
                                    price=200, currency="CZK", in_stock=True, ean=None, brand=None, image=None), rates)
    conn.execute("UPDATE offers SET url = 'javascript:alert(1)' WHERE shop_id = 1")
    conn.commit()
    rebuild_products(conn)
    cfg = {"settings": {"database": str(dbfile), "base_currency": "CZK"},
           "shops": [{"name": "Kept"}]}
    export_site(cfg, tmp_path / "dist")
    meta = json.loads((tmp_path / "dist/data/meta.json").read_text())
    assert [s["name"] for s in meta["shops"]] == ["Kept"]
    shard = next((tmp_path / "dist/data/p").glob("*.json"))
    urls = {o["u"] for p in json.loads(shard.read_text()).values() for o in p["o"]}
    assert "javascript:alert(1)" not in urls and "#" in urls


def test_crawler_refuses_private_addresses():
    from airsoftcompare.sources.common import Fetcher, public_host
    for url in ("http://127.0.0.1/x", "http://169.254.169.254/latest/meta-data/", "http://10.0.0.5/", "http://[::1]/", "file:///etc/passwd"):
        assert not public_host(url), url
    assert Fetcher("t", 0, 5, False).get("http://169.254.169.254/latest/meta-data/") is None
