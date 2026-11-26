"""Group offers from different shops into products.

1. Offers with the same EAN are the same product.
2. Offers with an identical normalised title are the same product.
3. Remaining groups in the same category (or where one side is 'other') are fuzzy-matched by title, but only if
   - the similarity is >= threshold,
   - both titles contain exactly the same numbers (so "M4 120 rds" never merges
     with "M4 300 rds", or "SA-E05" with "SA-E07"),
   - they don't name different colours (black vs tan),
   - the two groups don't already contain an offer from the same shop
     (a shop listing two items means they are different variants).
"""
from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter, defaultdict

import numpy as np
from rapidfuzz import fuzz, process

from .text import colors, numbers


MAX_PRICE_RATIO = 3.0


class _UF:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, a: int) -> int:
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a: int, b: int) -> int:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)
        return min(ra, rb)


def _similarity(queries: list[str], choices: list[str], threshold: int) -> np.ndarray:
    """Word-order independent similarity that tolerates one shop adding a few extra words
    ("Specna Arms M4 mid-cap" vs "M4 mid-cap"). Uses two native rapidfuzz passes."""
    sort = process.cdist(queries, choices, scorer=fuzz.token_sort_ratio, workers=-1, dtype=np.uint8)
    subset = process.cdist(queries, choices, scorer=fuzz.token_set_ratio, workers=-1, dtype=np.uint8)
    # A short title being a subset of a long one ("AK-74" vs "AK-74 fire selector") is not a match.
    qn = np.array([len(t.split()) for t in queries])[:, None]
    cn = np.array([len(t.split()) for t in choices])[None, :]
    comparable = np.minimum(qn, cn) >= 0.6 * np.maximum(qn, cn)
    score = np.maximum(sort, np.where(comparable, subset.astype(np.int16) - 4, 0)).astype(np.uint8)
    score[score < threshold] = 0
    return score


def cluster(offers: list[dict], threshold: int = 90, chunk: int = 2000) -> list[int]:
    """Return a group index (root) for each offer."""
    n = len(offers)
    uf = _UF(n)

    first_by: dict[tuple, int] = {}
    for i, o in enumerate(offers):
        for key in (("ean", o["ean"]) if o["ean"] else None, ("t", o["category"], o["norm_title"])):
            if key is None:
                continue
            if key in first_by:
                uf.union(first_by[key], i)
            else:
                first_by[key] = i

    shops: dict[int, set] = defaultdict(set)
    for i, o in enumerate(offers):
        shops[uf.find(i)].add(o["shop_id"])

    by_cat: dict[str, list[int]] = defaultdict(list)
    for i in range(n):
        if uf.find(i) == i:
            by_cat[offers[i]["category"]].append(i)
    others = by_cat.pop("other", [])
    buckets = [roots + others for roots in by_cat.values()] + [others]

    pairs: dict[tuple[int, int], float] = {}
    for roots in buckets:
        if len(roots) < 2:
            continue
        titles = [offers[r]["norm_title"] for r in roots]
        nums = [numbers(t) for t in titles]
        cols = [colors(t) for t in titles]
        for start in range(0, len(roots), chunk):
            m = _similarity(titles[start:start + chunk], titles, threshold)
            for a, b in zip(*m.nonzero()):
                a += start
                if a < b and nums[a] == nums[b] and (not cols[a] or not cols[b] or cols[a] == cols[b]):
                    pairs[(roots[a], roots[b])] = int(m[a - start, b])

    prices: dict[int, tuple[float, float]] = {}
    for i, o in enumerate(offers):
        r, p = uf.find(i), o.get("price_base") or 0
        lo, hi = prices.get(r, (p, p))
        prices[r] = (min(lo, p), max(hi, p))

    for (a, b), _ in sorted(pairs.items(), key=lambda kv: -kv[1]):
        ra, rb = uf.find(a), uf.find(b)
        if ra == rb or shops[ra] & shops[rb]:
            continue
        lo, hi = min(prices[ra][0], prices[rb][0]), max(prices[ra][1], prices[rb][1])
        if lo > 0 and hi > MAX_PRICE_RATIO * lo:  # a gun and its spare part are not the same product
            continue
        r = uf.union(ra, rb)
        shops[r] = shops[ra] | shops[rb]
        prices[r] = (lo, hi)

    return [uf.find(i) for i in range(n)]


def rebuild_products(conn: sqlite3.Connection, threshold: int = 90) -> int:
    rows = [dict(r) for r in conn.execute(
        "SELECT id, shop_id, title, norm_title, ean, brand, image, category, price_base, in_stock "
        "FROM offers WHERE active = 1 AND price_base IS NOT NULL")]
    groups: dict[int, list[dict]] = defaultdict(list)
    for o, root in zip(rows, cluster(rows, threshold)):
        groups[root].append(o)

    products, assignments = [], []
    for members in groups.values():
        # One offer per shop: a shop listing the same item twice shows its best one.
        best: dict[int, dict] = {}
        for m in sorted(members, key=lambda m: (not m["in_stock"], m["price_base"])):
            best.setdefault(m["shop_id"], m)
        members = list(best.values())
        eans = sorted({m["ean"] for m in members if m["ean"]})
        anchor = f"ean:{eans[0]}" if eans else "t:" + min(m["norm_title"] for m in members)
        pid = hashlib.sha1(anchor.encode()).hexdigest()[:12]
        cheapest = min(members, key=lambda m: m["price_base"])
        # The most common title wins; ties go to the longest (usually the most descriptive).
        title = max(Counter(m["title"] for m in members).items(), key=lambda kv: (kv[1], len(kv[0])))[0]
        prices = [m["price_base"] for m in members]
        products.append((
            pid, title, cheapest["norm_title"],
            (Counter(m["category"] for m in members if m["category"] != "other").most_common(1) or [("other",)])[0][0],
            next((m["brand"] for m in members if m["brand"]), None),
            next((m["image"] for m in members if m["image"]), None),
            eans[0] if eans else None,
            min(prices), max(prices),
            len({m["shop_id"] for m in members}),
            len({m["shop_id"] for m in members if m["in_stock"]}),
        ))
        assignments.extend((pid, m["id"]) for m in members)

    with conn:
        conn.execute("DELETE FROM products")
        conn.executemany("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?)", products)
        conn.execute("UPDATE offers SET product_id = NULL")
        conn.executemany("UPDATE offers SET product_id = ? WHERE id = ?", assignments)
    return len(products)
