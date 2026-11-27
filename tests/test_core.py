import pytest
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


def test_thumbnails_fit_450_and_flatten_transparency():
    import io
    from PIL import Image
    from airsoftcompare.images import BUCKETS, bucket, make_thumb, thumb_name
    src = io.BytesIO()
    Image.new("RGBA", (1600, 800), (255, 0, 0, 0)).save(src, "PNG")
    out = Image.open(io.BytesIO(make_thumb(src.getvalue())))
    assert out.format == "WEBP" and out.size == (450, 225) and out.mode == "RGB"
    assert out.getpixel((10, 10))[0] > 240  # transparent -> white, not black
    assert make_thumb(b"not an image") is None
    name = thumb_name("https://shop.cz/a.jpg")
    assert name.endswith(".webp") and 0 <= bucket(name) < BUCKETS


def test_parse_cnb_rates():
    from airsoftcompare.rates import parse_cnb
    day, rates = parse_cnb("26.11.2026 #227\nzemě|měna|množství|kód|kurz\nEMU|euro|1|EUR|24,455\nMaďarsko|forint|100|HUF|6,570\n")
    assert day == "26.11.2026" and rates["EUR"] == 24.455 and abs(rates["HUF"] - 0.0657) < 1e-9 and rates["CZK"] == 1.0


@pytest.mark.parametrize("title, expected", [
    # real names that used to land in the wrong category
    ("Skládací odhazovací vak na zásobníky - Amber, Novritsch", "pouches"),
    ("Zásobník AK, 150 BB, US Palm, černý, Cyma", "magazines"),
    ("Záchyt dna zásobníku pro WE R17, díl č.66 - WE", "parts"),
    ("Kompletní set nabíjecí trysky pro WE R17, 19, 33 - díl č.47", "parts"),
    ("Inteligentní Li-Pol nabíječka Compact B3AC, Turnigy", "chargers"),
    ("Krytka bateriového prostoru pažby LMT Crane - černá, E&C", "parts"),
    ("Airsoftová pistole CZ 75 SP-01 Shadow - CO2, GNB, ASG", "pistols"),
    ("Airsoft sniper MB4405D + optika a dvojnožka - černá - WELL", "snipers"),
    ("G&G Airsoftová zbraň CM16 SRL, Sportline, elektronická spoušť", "guns"),
    ("Fleece čepice Pískova - MFH Maskáče", "clothing"),
    ("Zásobníková Molle sumka pro 2x pistole - VZ.95, MFH", "pouches"),
    ("Ocelová kuličková ložiska 7mm, AirsoftPro", "parts"),
    ("Pouzdro Blackhawk SERPA CQC pro Glock 17", "holsters"),
    ("Pouzdro na pušku Gamo 130cm černo-zelené", "pouches"),
    ("Boty Sniper Pro s YKK zipem - Coyote", "clothing"),
    ("Taktické rukavice Fast Fit® - Coyote Brown, Mechanix", "gloves"),
    ("PMR M24-S, set, Midland", "comms"),
    ("SSG96 Trigger Box", "parts"),
    ("Glock 17 Gen 5 FS MOS, Black, GBB, Umarex", "pistols"),
    ("Magazine pouch M4", "pouches"),
    ("Odstřelovací puška VSR-10 Pro Sniper Version, Tokyo Marui", "snipers"),
    ("Univerzální Karabina Grmloc 5cm - písková DE, FMA", "pouches"),
    # food and radios have their own top-level groups
    ("Potravinová dávka Pro Ration FULL-DAY (celodenní) - Menu 1, Adventure Menu", "food"),
    ("Plátek sýrové pizzy (US MRE Menu 11)", "food"),
    ("Sušené hovězí maso Original - 25g, Indiana Jerky", "food"),
    ("Diabolo Gamo Magnum Energy 250ks cal.4,5mm", "airguns"),
    ("Handsfree A21M, Midland", "comms"),
    ("Baterie BL-5 pro rádiostanici Baofeng UV-5R - Baofeng", "comms"),
    ("Špunty do uší MaxDefense M02, EARMOR", "comms"),
    ("Set špuntů pro airsoftové granáty 40mm - 10ks, Specna Arms", "grenades"),
    ("Otevřená sumka MOLLE na vysílačku / radiostanici - černá, Mil-Tec", "pouches"),
])
def test_categorize_real_names(title, expected):
    assert categorize(title) == expected


def test_shop_path_beats_weak_hints():
    # "M4" alone in a name is a hint; the shop filing it under parts decides
    assert categorize("M4 tělo spodní", "Airsoft | Náhradní díly") == "parts"
    assert categorize("Ruger Super Hawk CO2", "Airsoftové zbraně | Pistole") == "pistols"


def test_translation_locker_keeps_english_words_and_splits_colours():
    from airsoftcompare.translate import _Locker
    lk = _Locker({"Tokyo Marui"})
    text, kept = lk.lock("Odstřelovací puška VSR-10 - desert, Tokyo Marui", use_glossary=True)
    assert "desert" in kept and "sniper rifle" in kept and "Tokyo Marui" in kept and "desert" not in text
    text, kept = lk.lock("Pistole M1911 - černá/stříbrná, S&T Armament", use_glossary=True)
    assert "black" in kept and "Armament" in kept and "S&T" in kept
    text, kept = lk.lock("Magazine pouch for M4/AR15 - tan, Emerson Gear", use_glossary=False, lang="sk")
    assert "zásobníková sumka" in kept and "M4/AR15" in kept and "Gear" in kept and "piesková" in kept
    text, kept = lk.lock("Tactical gear set", use_glossary=False, lang="de")
    assert "Tactical" not in kept and "Zahnradsatz" in kept


def test_every_subcategory_is_in_exactly_one_group():
    from airsoftcompare.categories import CATEGORIES, GROUPS
    subs = [c for _, _, cs in GROUPS.values() for c in cs]
    assert sorted(subs) == sorted(CATEGORIES) and len(subs) == len(set(subs))


@pytest.mark.parametrize("title, expected", [
    ("Airsoftový samopal CZ Scorpion EVO 3 A1 - černý, ASG", "smgs"),
    ("H&K MP5KA4 PDW, Tokyo Marui", "smgs"),
    ("CYMA Airsoftový samopal Thompson M1928A1 - celokov", "smgs"),
    ("Airsoftová zbraň AK-74M - celokov, sklápěcí pažba, ICS", "guns"),
    ("Airsoftový kulomet FN M249 - černý, ABS, CyberGun", "guns"),
    ("Granátomet M203 krátký na RIS lištu", "grenades"),
    ("G&G CM16 SRS (M)", "guns"),
])
def test_gun_types(title, expected):
    assert categorize(title) == expected


def test_gun_power_and_platform_tags():
    from airsoftcompare.export import _attrs
    tags = lambda t, c, p=5000: set(_attrs(t, c, p))
    assert {"pw:electric", "pl:ak"} <= tags("Airsoftová zbraň AK74M - LCT", "guns")      # AEG unless said otherwise
    assert {"pw:gas", "pl:m4"} <= tags("WE GBB M4 CQB", "guns")
    assert "pl:m4" not in tags("Odstřelovací puška SA-S02 CORE™ SAG M40", "snipers")
    assert {"pl:ww2", "pl:mp5"}.isdisjoint(tags("Glock 17", "pistols"))
    assert "pw:spring" in tags("Glock 25, kov, Galaxy", "pistols", 470)            # cheap pistol: spring
    assert "pw:gas" in tags("Hi-Capa 5.1, WE", "pistols", 2500)
    assert {"pl:ww2", "pl:mg"} <= tags("Airsoftový kulomet MG42 - celokov", "guns")


@pytest.mark.parametrize("title, expected", [
    ("Nůž Mora® 756T nerez ZELENÝ", "melee"),
    ("Obušek teleskopický EXB 16 nekalený ČERNÝ", "melee"),
    ("Kuše Beast Hunter Blade 175lb camo", "bows"),
    ("Toulec Avalon Classic 3T-2 pocket LH black", "bows"),
    ("Pryžové nesmeky s kovovými hroty YETTI, BENNON", "other"),
    ("Střelecký terč IPSC Hard Cover 1 - 50ks, Range Solutions", "targets"),
    ("Magnetka Umarex Germany", "magnets"),
    ("Magnetický opasek EDC Magnetic Belt - černý, Helikon-Tex", "pouches"),
    ("Sběratelská kniha nášivek - Coyote Brown, Emerson Gear", "books"),
    ("Redukce T-Dean, Large TAMIYA konektor, samice", "cables"),
    ("Redukce závitu tlumiče ze 14mm + na 14mm -, Specna Arms", "parts"),
    ("Vzduchovka Hatsan 105X Torpedo cal.5,5mm FP", "airguns"),
    ("Vzduchová pistole Glock 17 Gen5 BlowBack Coyote", "airguns"),
    ("CZ 75D Compact Dual tone - CO2, 4,5mm, GNB, ASG", "airguns"),
    ("Diabolo JSB Exact Jumbo RS 500ks cal.5,52mm", "airguns"),
    ("Zásobník pro CZ 75D cal. 4,5mm 15BB Co2 ASG", "magazines"),
])
def test_other_and_airgun_categories(title, expected):
    assert categorize(title) == expected


@pytest.mark.parametrize("title, price, expected", [
    ("Diabolo JSB Exact Jumbo RS 500ks cal.5,52mm", 385, {"ag:pellets", "cal:5.5"}),
    ("Diabolo H&N Field Target .177", 200, {"ag:pellets", "cal:4.5"}),
    ("Diabolo cal. 22 (5,5 mm)", 200, {"ag:pellets", "cal:5.5"}),
    ("Diabolky EXACT King Heavy 6,35mm (cal .25)", 474, {"ag:pellets", "cal:6.35"}),
    ("Vzduchová pistole Glock 17 Gen5 Diabolo BlowBack", 3890, {"ag:pistol"}),
    ("ASG Schofield 6\" 4,5mm Diabolky Stainless", 3840, {"ag:pistol", "cal:4.5"}),
    ("Vzduchovka Taipan Veteran II cal.6,35mm FP", 42900, {"ag:rifle", "cal:6.35"}),
])
def test_airgun_kind_and_calibre(title, price, expected):
    from airsoftcompare.export import _attrs
    assert expected <= set(_attrs(title, "airguns", price))


def test_page_numbers_in_app_js():
    import re, shutil, subprocess
    from pathlib import Path
    if not shutil.which("node"):
        pytest.skip("node not installed")
    js = Path(__file__).resolve().parent.parent.joinpath("airsoftcompare/static/app.js").read_text(encoding="utf-8")
    fn = re.search(r"const pageNumbers = .*?\n  \};", js, re.S).group(0)
    out = subprocess.run(["node", "-e", fn + "\nconsole.log(JSON.stringify([[13,95],[1,95],[3,5],[95,95],[1,1]].map(([p,n]) => pageNumbers(p,n))))"],
                         capture_output=True, text=True, check=True).stdout
    assert __import__("json").loads(out) == [[1, 2, 0, 11, 12, 13, 14, 15, 0, 95], [1, 2, 3, 0, 95], [1, 2, 3, 4, 5],
                                             [1, 2, 0, 93, 94, 95], [1]]


def test_offers_without_a_price_are_not_shown(tmp_path):
    from airsoftcompare import db as dbmod
    from airsoftcompare.matching import rebuild_products
    from airsoftcompare.sources.common import Offer
    from airsoftcompare.updater import _shop_id, save_offer
    conn = dbmod.connect(str(tmp_path / "t.db"))
    sid = _shop_id(conn, {"name": "Novritsch", "url": "https://x.eu", "type": "sitemap"})
    for title, price in (("SSR9 - Build your Setup!", 0), ("SSX10 Optionals", 0), ("SSG10 Sniper", 9990)):
        save_offer(conn, sid, Offer(url=f"https://x.eu/{price}{len(title)}", title=title, price=price, currency="CZK",
                                    in_stock=True, ean=None, brand=None, image=None), {"CZK": 1.0})
    assert rebuild_products(conn) == 1
    assert [r[0] for r in conn.execute("SELECT title FROM products")] == ["SSG10 Sniper"]
