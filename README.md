# Airsoft Compare

A Heureka-style price comparison site just for airsoft. It reads the catalogues of the
e-shops you list, works out which listings are the same product (masks, magazines,
red dots, guns, BBs…), and shows each product's price at every shop, with
price history.



## Quick start

```bash
pip install -r requirements.txt
python -m airsoftcompare demo                         # fictional sample shops
python -m airsoftcompare -c demo/shops.yaml serve     # → http://localhost:8000
```

## Adding real shops

1. Find out how a shop can be read:
   ```bash
   python -m airsoftcompare probe https://www.some-airsoft-shop.cz
   ```
   It looks for a public product feed (`/heureka.xml` etc.). If there isn't one,
   it checks whether the product pages carry machine-readable data. Either way it
   prints a block to paste into `shops.yaml`.
2. Download everything and match products:
   ```bash
   python -m airsoftcompare update
   ```
3. Run the site:
   ```bash
   python -m airsoftcompare serve
   ```

Keep prices fresh with `python -m airsoftcompare update --every 12`, or schedule
`update` with Windows Task Scheduler or cron.

### Feeds vs crawling
* **Feed** (`type: feed`) – almost every Czech/Slovak shop listed on Heureka or Zboží
  generates an XML feed of its full catalogue. Reading it takes seconds. If `probe`
  can't find it, email the shop and ask for their Heureka feed URL. Many will
  share it, because it brings them customers. Google Merchant feeds work too.
* **Sitemap crawl** (`type: sitemap`) – the fallback. It fetches each product page
  politely (`request_delay`, robots.txt) and reads its schema.org/OpenGraph data. Use
  `include` / `exclude` regexes so it skips blog and category pages.

## How matching works (`airsoftcompare/matching.py`)
1. Listings with the **same EAN** are the same product.
2. Otherwise titles are **normalised**. That means removing diacritics, translating
   Czech/Slovak words to English (`maska→mask`, `černá→black`, `zásobník→magazine`…)
   and dropping filler words. The titles are then **fuzzy-compared** within a category.
3. Safety rules stop false matches: the **numbers** must be identical (120 rds ≠ 140 rds,
   SA-E05 ≠ SA-E07), **colours** must not conflict (black ≠ tan), and two listings
   from the **same shop** are never merged (they are variants).

If products that should merge don't, lower `match_threshold` (e.g. 85) or add words to
`SYNONYMS`/`STOPWORDS` in `text.py`. If wrong ones merge, raise it. Then run
`python -m airsoftcompare rematch`, which re-matches without downloading anything.
Categories are keyword rules in `categories.py`. Add your own keywords there.

## Hosting (free): GitHub Actions + Cloudflare Pages
The live site is static. Twice a day `.github/workflows/update.yml`:
1. restores the database from the Actions cache,
2. runs `python -m airsoftcompare update --batch --max-minutes 290` (feeds in seconds; crawled
   shops continue where they stopped last time),
3. runs `python -m airsoftcompare export dist`, which writes HTML shells plus JSON data
   (`data/meta.json`, `data/g/<category>.json`, `data/p/<id prefix>.json`) rendered by `static/app.js`,
4. uploads `dist/` to the Cloudflare Pages project `compairsoft`.

Needs repository secrets `CLOUDFLARE_API_TOKEN` (permission: Account → Cloudflare Pages → Edit) and
`CLOUDFLARE_ACCOUNT_ID`. Run it by hand from the Actions tab ("Run workflow"); a push to `master`
re-publishes the site without crawling. Preview an export locally with
`python -m airsoftcompare export dist && python -m http.server -d dist` (product pages need the
`_redirects` rule, so open them as `/product.html?id=<id>` locally).

`python -m airsoftcompare serve` still runs the same site as a normal web server for development.

## API
* `GET /api/products?q=tango&cat=masks&stock=true&sort=price_asc`
* `GET /api/products/{id}` – a product with all its shop offers

## Be a good citizen
Crawl slowly, respect robots.txt (both on by default) and prefer feeds. Before
publishing the site, check each shop's terms or ask permission. Most shops are
glad to be listed, which is how Heureka works.

## Tests
```bash
python -m pytest -q
```

## Security notes
Shop feeds and pages are untrusted input. Links and images are accepted only as absolute
`http(s)` URLs (`sources/common.py: safe_url`). XML entities are not expanded. Downloads are
capped at 256 MB (`MAX_DOWNLOAD_BYTES`). See [`docs/AUDIT.md`](docs/AUDIT.md) for the full
audit and open recommendations.

## Project layout
```
airsoftcompare/
  sources/feed.py      Heureka / Zboží / Google XML feeds
  sources/sitemap.py   sitemap crawler + JSON-LD/OpenGraph product parser
  categories.py        keyword categorisation
  text.py              normalisation, synonyms
  matching.py          cross-shop product grouping
  updater.py           download → DB, price history
  web.py, templates/   the website (FastAPI + Jinja2)
  probe.py, demo.py    helpers
tests/                 pytest
```
