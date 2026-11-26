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
    assert categorize("Pistole Glock 17 GBB green gas") == "guns"
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
