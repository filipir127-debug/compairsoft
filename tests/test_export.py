"""Static site export (Cloudflare Pages): unsafe URLs from old databases, security headers."""
import json
import re

from airsoftcompare import db
from airsoftcompare.export import SECURITY_HEADERS, export_site


def _site(tmp_path):
    """A database written before URL checks existed: one offer and one image carry javascript: URLs."""
    conn = db.connect(tmp_path / "t.db")
    conn.execute("INSERT INTO shops(id, name, url, type) VALUES (1, 'Good', 'https://good.cz', 'feed'), "
                 "(2, 'Evil', 'javascript:alert(1)', 'feed')")
    rows = [(1, 1, "https://good.cz/mask", "aa11"), (2, 2, "javascript:alert(2)", "aa11"),
            (3, 1, "https://good.cz/gloves", "bb22")]
    for oid, sid, url, pid in rows:
        conn.execute("INSERT INTO offers(id, shop_id, url, title, norm_title, price, currency, price_base, in_stock, "
                     "category, product_id) VALUES (?, ?, ?, 'Mask', 'mask', 100, 'CZK', 100, 1, 'masks', ?)",
                     (oid, sid, url, pid))
    conn.execute("INSERT INTO products VALUES ('aa11', 'Mask', 'mask', 'masks', NULL, 'javascript:alert(3)', NULL, "
                 "100, 100, 2, 2)")
    conn.execute("INSERT INTO products VALUES ('bb22', 'Gloves', 'gloves', 'gloves', NULL, 'https://good.cz/g.jpg', "
                 "NULL, 100, 100, 1, 1)")
    conn.commit()
    out = tmp_path / "dist"
    export_site({"settings": {"database": str(tmp_path / "t.db"), "base_currency": "CZK"}, "shops": []}, out)
    return out


def test_export_drops_unsafe_urls_from_old_database(tmp_path):
    out = _site(tmp_path)
    everything = "".join(p.read_text(encoding="utf-8") for p in out.rglob("*.json"))
    assert "javascript:" not in everything
    mask = json.loads((out / "data/p/aa.json").read_text(encoding="utf-8"))["aa11"]
    assert [o["u"] for o in mask["o"]] == ["https://good.cz/mask"]  # the javascript: offer is left out
    assert mask["p"]["i"] == ""                                         # unsafe image → no image
    gloves = json.loads((out / "data/p/bb.json").read_text(encoding="utf-8"))["bb22"]
    assert gloves["p"]["i"] == "https://good.cz/g.jpg"                  # safe image kept
    shops = {s["name"]: s["url"] for s in json.loads((out / "data/meta.json").read_text(encoding="utf-8"))["shops"]}
    assert shops == {"Good": "https://good.cz", "Evil": None}          # shop listed, without a link


def test_export_writes_security_headers_and_no_inline_script(tmp_path):
    out = _site(tmp_path)
    headers = (out / "_headers").read_text(encoding="utf-8")
    assert headers.startswith("/*\n")
    for name, value in SECURITY_HEADERS.items():
        assert f"  {name}: {value}\n" in headers
    assert "Cache-Control: public, max-age=600" in headers  # existing cache rules kept
    # The CSP has no 'unsafe-inline', so the pages must not carry inline scripts or handlers.
    assert (out / "static/site.js").read_text(encoding="utf-8").startswith("window.SITE = {")
    for page in ("index", "product", "shops", "404"):
        html = (out / f"{page}.html").read_text(encoding="utf-8")
        assert not re.search(r"<script(?![^>]*\bsrc=)", html), page  # every script is an external file
        assert not re.search(r"\son[a-z]+=", html) and 'style="' not in html, page
    app = (out / "static/app.js").read_text(encoding="utf-8")
    assert "onerror=" not in app and "onchange=" not in app and 'style="' not in app
