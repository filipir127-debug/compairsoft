"""The comparison website (FastAPI + Jinja2, server-rendered)."""
from __future__ import annotations

import math
import os
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config as cfgmod
from . import db as dbmod
from .categories import CATEGORIES
from .text import normalize

HERE = Path(__file__).parent
PAGE_SIZE = 48
SORTS = {
    "relevance": "p.shop_count DESC, p.min_price ASC",
    "price_asc": "p.min_price ASC",
    "price_desc": "p.min_price DESC",
    "shops": "p.shop_count DESC, p.min_price ASC",
    "savings": "(p.max_price - p.min_price) DESC",
    "name": "p.title COLLATE NOCASE ASC",
}


def create_app(config_path: str | None = None) -> FastAPI:
    cfg = cfgmod.load(config_path or os.environ.get("AIRSOFT_CONFIG", "shops.yaml"))
    settings = cfg["settings"]
    conn = dbmod.connect(settings["database"])
    currency = settings["base_currency"]

    app = FastAPI(title="Airsoft price comparison")
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    tpl = Jinja2Templates(directory=HERE / "templates")

    def money(v):
        if v is None:
            return "–"
        s = f"{v:,.0f}" if currency in ("CZK", "HUF") else f"{v:,.2f}"
        return s.replace(",", " ") + {"CZK": " Kč", "EUR": " €", "PLN": " zł"}.get(currency, " " + currency)

    tpl.env.filters["money"] = money
    tpl.env.globals["CATEGORIES"] = CATEGORIES

    def category_counts():
        return {r[0]: r[1] for r in conn.execute("SELECT category, COUNT(*) FROM products GROUP BY category")}

    def search(q: str, cat: str, shop: int | None, stock: bool, multi: bool,
               pmin: float | None, pmax: float | None, sort: str, page: int, limit: int = PAGE_SIZE):
        where, args = [], []
        for word in normalize(q).split():
            where.append("p.norm_title LIKE ?")
            args.append(f"%{word}%")
        if q.strip().isdigit() and len(q.strip()) >= 8:  # EAN search
            where, args = ["p.ean LIKE ?"], [f"%{q.strip().lstrip('0')}%"]
        if cat:
            where.append("p.category = ?"); args.append(cat)
        if shop:
            where.append("EXISTS (SELECT 1 FROM offers o WHERE o.product_id = p.id AND o.shop_id = ? AND o.active = 1)")
            args.append(shop)
        if stock:
            where.append("p.in_stock_count > 0")
        if multi:
            where.append("p.shop_count > 1")
        if pmin is not None:
            where.append("p.min_price >= ?"); args.append(pmin)
        if pmax is not None:
            where.append("p.min_price <= ?"); args.append(pmax)
        sql_where = ("WHERE " + " AND ".join(where)) if where else ""
        total = conn.execute(f"SELECT COUNT(*) FROM products p {sql_where}", args).fetchone()[0]
        rows = conn.execute(
            f"SELECT p.* FROM products p {sql_where} ORDER BY {SORTS.get(sort, SORTS['relevance'])} LIMIT ? OFFSET ?",
            args + [limit, (page - 1) * limit]).fetchall()
        return total, rows

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, q: str = "", cat: str = "", shop: str = "",
              stock: bool = False, multi: bool = False, pmin: str = "", pmax: str = "",
              sort: str = "relevance", page: int = Query(1, ge=1)):
        shop = int(shop) if shop.strip().isdigit() else None
        fmin = _num(pmin)
        fmax = _num(pmax)
        total, products = search(q, cat, shop, stock, multi, fmin, fmax, sort, page)
        params = {k: v for k, v in dict(q=q, cat=cat, shop=shop or "", stock="1" if stock else "",
                                         multi="1" if multi else "", pmin=pmin, pmax=pmax, sort=sort).items() if v}
        return tpl.TemplateResponse(request, "index.html", dict(
            products=products, total=total, page=page, pages=max(1, math.ceil(total / PAGE_SIZE)),
            q=q, cat=cat, shop=shop, stock=stock, multi=multi, pmin=pmin, pmax=pmax, sort=sort,
            shops=conn.execute("SELECT * FROM shops ORDER BY name").fetchall(),
            counts=category_counts(), qs=lambda **kw: "?" + urlencode({**params, **kw}),
            stats=conn.execute("SELECT COUNT(*) AS products, SUM(shop_count > 1) AS compared FROM products").fetchone(),
            offers_total=conn.execute("SELECT COUNT(*) FROM offers WHERE active=1").fetchone()[0],
        ))

    @app.get("/product/{pid}", response_class=HTMLResponse)
    def product(request: Request, pid: str):
        p = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if not p:
            raise HTTPException(404, "Product not found – it may have been re-matched after the last update.")
        offers = conn.execute("""
            SELECT o.*, s.name AS shop_name, s.url AS shop_url FROM offers o JOIN shops s ON s.id = o.shop_id
            WHERE o.product_id = ? ORDER BY (o.in_stock = 0), o.price_base""", (pid,)).fetchall()
        history = conn.execute("""
            SELECT h.day, s.name AS shop, h.price_base FROM price_history h
            JOIN offers o ON o.id = h.offer_id JOIN shops s ON s.id = o.shop_id
            WHERE o.product_id = ? ORDER BY h.day""", (pid,)).fetchall()
        similar = conn.execute("""
            SELECT * FROM products WHERE category = ? AND id != ? AND min_price BETWEEN ? AND ?
            ORDER BY shop_count DESC, ABS(min_price - ?) LIMIT 8""",
            (p["category"], pid, p["min_price"] * 0.6, p["min_price"] * 1.6, p["min_price"])).fetchall()
        return tpl.TemplateResponse(request, "product.html", dict(
            p=p, offers=offers, chart=price_chart(history, money), similar=similar))

    @app.get("/shops", response_class=HTMLResponse)
    def shops(request: Request):
        rows = conn.execute("""
            SELECT s.*, (SELECT COUNT(*) FROM offers o JOIN products p ON p.id = o.product_id
                         WHERE o.shop_id = s.id AND o.active = 1 AND o.price_base = p.min_price AND p.shop_count > 1) AS cheapest
            FROM shops s ORDER BY s.name""").fetchall()
        return tpl.TemplateResponse(request, "shops.html", dict(shops=rows))

    @app.get("/api/products")
    def api_products(q: str = "", cat: str = "", stock: bool = False, sort: str = "relevance",
                     page: int = Query(1, ge=1), limit: int = Query(50, le=500)):
        total, rows = search(q, cat, None, stock, False, None, None, sort, page, limit)
        return {"total": total, "currency": currency, "items": [dict(r) for r in rows]}

    @app.get("/api/products/{pid}")
    def api_product(pid: str):
        p = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if not p:
            raise HTTPException(404)
        offers = conn.execute("SELECT o.*, s.name AS shop_name FROM offers o JOIN shops s ON s.id=o.shop_id "
                              "WHERE o.product_id = ? ORDER BY o.price_base", (pid,)).fetchall()
        return {**dict(p), "offers": [dict(o) for o in offers]}

    return app


def _num(v: str) -> float | None:
    try:
        return float(v.replace(",", ".").replace(" ", ""))
    except ValueError:
        return None


PALETTE = ["#4f9d69", "#d9822b", "#3a7bd5", "#c94f6d", "#8e6cc9", "#2aa7a0", "#b8a12d", "#7a7a7a"]


def price_chart(history, money, w: int = 1000, h: int = 280) -> dict | None:
    """Build an inline-SVG line chart: one line per shop."""
    if not history:
        return None
    days = sorted({r["day"] for r in history})
    if len(days) < 2:
        return None
    series = defaultdict(dict)
    for r in history:
        series[r["shop"]][r["day"]] = r["price_base"]
    vals = [r["price_base"] for r in history]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.1 or hi * 0.05 or 1
    lo, hi = lo - pad, hi + pad
    L, R, T, B = 64, 12, 10, 26
    x = lambda i: L + (w - L - R) * i / (len(days) - 1)
    y = lambda v: T + (h - T - B) * (1 - (v - lo) / (hi - lo))
    idx = {d: i for i, d in enumerate(days)}
    lines = []
    for n, (shop, pts) in enumerate(sorted(series.items())):
        coords = [(x(idx[d]), y(v)) for d, v in sorted(pts.items())]
        lines.append({"shop": shop, "color": PALETTE[n % len(PALETTE)],
                      "points": " ".join(f"{a:.1f},{b:.1f}" for a, b in coords),
                      "last": coords[-1]})
    ticks = [lo + (hi - lo) * k / 3 for k in range(4)]
    return {"w": w, "h": h, "lines": lines, "L": L, "R": R, "T": T, "B": B,
            "yticks": [(y(t), money(t)) for t in ticks],
            "xlabels": [(x(0), days[0]), (x(len(days) - 1), days[-1])]}
