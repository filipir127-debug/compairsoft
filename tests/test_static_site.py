"""Static site (Cloudflare Pages): CSP in _headers, no inline code, client-side URL guard in app.js."""
import json
import re
from pathlib import Path

from airsoftcompare import db
from airsoftcompare.export import CONTENT_SECURITY_POLICY, export_site

APP_JS = Path(__file__).resolve().parent.parent / "airsoftcompare/static/app.js"


def _export(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    conn.execute("INSERT INTO shops(id, name, url, type) VALUES (1, 'Good', 'https://good.cz', 'feed')")
    conn.execute("INSERT INTO offers(id, shop_id, url, title, norm_title, price, currency, price_base, in_stock, "
                 "category, product_id) VALUES (1, 1, 'https://good.cz/m', 'Mask', 'mask', 100, 'CZK', 100, 1, "
                 "'masks', 'aa11')")
    conn.execute("INSERT INTO products VALUES ('aa11', 'Mask', 'mask', 'masks', NULL, 'https://good.cz/m.jpg', NULL, "
                 "100, 100, 1, 1)")
    conn.commit()
    out = tmp_path / "dist"
    export_site({"settings": {"database": str(tmp_path / "t.db"), "base_currency": "CZK"},
                 "shops": [{"name": "Good"}]}, out)
    return out


def test_headers_carry_csp_for_self_hosted_site(tmp_path):
    headers = (_export(tmp_path) / "_headers").read_text(encoding="utf-8")
    block = headers.split("/data/*")[0]  # the /* block, applied to every page
    assert f"  Content-Security-Policy: {CONTENT_SECURITY_POLICY}\n" in block
    assert "X-Content-Type-Options: nosniff" in block and "Permissions-Policy:" in block
    assert "Cache-Control: public, max-age=600" in headers
    csp = dict(d.split(" ", 1) for d in CONTENT_SECURITY_POLICY.split("; "))
    assert csp["font-src"] == "'self'" and csp["style-src"] == "'self'" and csp["script-src"] == "'self'"
    assert "google" not in CONTENT_SECURITY_POLICY and "unsafe-inline" not in CONTENT_SECURITY_POLICY


def test_pages_have_no_inline_scripts_or_handlers(tmp_path):
    out = _export(tmp_path)
    site = (out / "static/site.js").read_text(encoding="utf-8")
    assert site.startswith("window.SITE = {") and json.loads(site[len("window.SITE = "):].rstrip().rstrip(";"))
    assert any((out / "static/fonts").glob("*.woff2"))
    for page in ("index", "product", "shops", "404"):
        html = (out / f"{page}.html").read_text(encoding="utf-8")
        assert not re.search(r"<script(?![^>]*\bsrc=)", html), page  # every script is an external file
        assert not re.search(r"\son[a-z]+=", html) and 'style="' not in html, page
        assert "fonts.googleapis" not in html and "fonts.gstatic" not in html, page
    app = (out / "static/app.js").read_text(encoding="utf-8")
    assert not re.search(r"\son[a-z]+=", app) and 'style="' not in app


def test_app_js_guards_every_url_from_data():
    app = APP_JS.read_text(encoding="utf-8")
    assert 'x.protocol === "http:" || x.protocol === "https:"' in app
    # Data URLs reach href/src only through safeUrl(): never as esc(o.u), esc(p.i), esc(s.url).
    for raw in ("esc(o.u)", "esc(p.i)", "esc(s.url)"):
        assert raw not in app, raw
    assert "safeUrl(o.u)" in app and "safeUrl(p.i)" in app and "safeUrl(s.url)" in app
    assert 'rel="noopener noreferrer nofollow"' in app
