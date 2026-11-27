"""Browser-side URL guard and inline-code checks for the static site.

Ported from Max287954's branch fix/client-side-url-guard, adapted to the current app.js.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent / "airsoftcompare"
APP_JS = (ROOT / "static/app.js").read_text(encoding="utf-8")

# The only things allowed at the start of href="${…}" / src="${…}" / data-orig="${…}" in app.js:
SAFE_STARTS = (
    "esc(safeUrl(",   # shop data: links and photos, absolute http(s) only
    "url(",           # same-site links built from the current address
    "catHref(",       # same-site category link, known categories only
    "more}",          # homepage section links, constants from the export
)


def test_every_interpolated_link_goes_through_a_guard():
    found = re.findall(r'(?:href|src|data-orig)="\$\{([^"]*)', APP_JS)
    assert len(found) > 10
    for expr in found:
        assert expr.startswith(SAFE_STARTS), f"unguarded URL in app.js: ${{{expr[:60]}"


def test_shop_data_urls_are_never_used_raw():
    for raw in ("esc(o.u)", "esc(p.i)", "esc(s.url)", "esc(p.orig", "esc(z.dataset.orig)"):
        assert raw not in APP_JS, raw


def test_no_inline_code_or_styles():
    for f in [ROOT / "static/app.js", *ROOT.joinpath("site").glob("*.html"), *ROOT.joinpath("site").glob("*.svg")]:
        text = f.read_text(encoding="utf-8")
        assert not re.search(r"\son[a-z]+=\"", text), f"inline event handler in {f.name}"
        assert 'style="' not in text, f"inline style in {f.name}"
    base = (ROOT / "site/base.html").read_text(encoding="utf-8")
    for tag in re.findall(r"<script[^>]*>", base):
        assert "src=" in tag or 'type="application/json"' in tag, tag


def test_safe_url_in_a_js_engine():
    if not shutil.which("node"):
        pytest.skip("node not installed")
    fn = re.search(r"const safeUrl = \(u\) => \{.*?\n  \};", APP_JS, re.S).group(0)
    cases = ["https://a.cz/p", "http://a.cz/i.jpg", "javascript:alert(1)", " JavaScript:alert(1)", "java\tscript:x",
             "data:text/html,x", "vbscript:x", "/relative", "#", "", None]
    script = fn + "\nconsole.log(JSON.stringify(%s.map(safeUrl)));" % json.dumps(cases)
    out = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    assert out == ["https://a.cz/p", "http://a.cz/i.jpg"] + [""] * 9
