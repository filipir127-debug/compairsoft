"""Inspect a shop and print a ready-to-paste shops.yaml entry."""
from __future__ import annotations

import itertools
from urllib.parse import urlsplit

from .sources import feed, sitemap
from .sources.common import Fetcher


def probe(url: str, settings: dict) -> None:
    if not url.startswith("http"):
        url = "https://" + url
    base = "{0.scheme}://{0.netloc}".format(urlsplit(url))
    f = Fetcher(settings["user_agent"], 0.5, settings["timeout"], settings["respect_robots"])
    name = urlsplit(base).netloc.removeprefix("www.")
    print(f"Probing {base} …\n")

    # 1) Common public feed locations
    for candidate in sitemap.probe_feed_urls(base):
        data = f.get_bytes(candidate, check_robots=False)
        if not data or b"<" not in data[:200]:
            continue
        offers = list(itertools.islice(feed.parse_feed(data), 5))
        if offers:
            print(f"✔ Found a product feed: {candidate}")
            for o in offers[:3]:
                print(f"    {o.title[:60]:60} {o.price} {o.currency}")
            print(f"\nAdd to shops.yaml:\n\n  - name: {name}\n    url: {base}\n    type: feed\n    feed_url: {candidate}\n")
            return
    print("✘ No public feed at the usual addresses (ask the shop – most have a Heureka/Zboží feed).")

    # 2) Sitemap + product page structured data
    maps = sitemap.find_sitemaps(f, base)
    print(f"  Sitemaps: {', '.join(maps)}")
    urls = list(itertools.islice(itertools.chain.from_iterable(sitemap.iter_sitemap(f, m) for m in maps), 5000))
    print(f"  {len(urls)} URLs in sitemap(s) (first 5000 checked)")
    if not urls:
        print("✘ No sitemap found – this shop can't be crawled automatically.")
        return
    found, tried = [], 0
    # Try URLs that look like product pages (deepest paths, .html) first
    for u in sorted(urls, key=lambda u: (-u.count("/") - u.endswith(".html") - ("-" in u.rsplit("/", 1)[-1])))[:25]:
        if not f.allowed(u):
            continue
        tried += 1
        r = f.get(u)
        if r is not None and (o := sitemap.extract_product(r.content, r.url)):
            found.append((u, o))
            if len(found) >= 3:
                break
    if not found:
        print(f"✘ Checked {tried} pages, none had machine-readable product data.")
        return
    print(f"✔ Product data found on pages, e.g.:")
    for u, o in found:
        print(f"    {o.title[:50]:50} {o.price} {o.currency}  ({'in stock' if o.in_stock else 'stock ?' if o.in_stock is None else 'out of stock'})  {u}")
    print(f"\nAdd to shops.yaml (tune 'include' so only product URLs are fetched):\n\n"
          f"  - name: {name}\n    url: {base}\n    type: sitemap\n    sitemap_url: {maps[0]}\n"
          f"    # include: '\\.html$'\n    max_pages: 3000\n")
