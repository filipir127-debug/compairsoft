from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS shops (
    id          INTEGER PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    url         TEXT,
    type        TEXT,
    last_update TEXT,
    last_status TEXT,
    offer_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS offers (
    id            INTEGER PRIMARY KEY,
    shop_id       INTEGER NOT NULL REFERENCES shops(id),
    url           TEXT NOT NULL,
    title         TEXT NOT NULL,
    norm_title    TEXT NOT NULL,
    price         REAL,
    currency      TEXT,
    price_base    REAL,
    in_stock      INTEGER,
    ean           TEXT,
    brand         TEXT,
    image         TEXT,
    shop_category TEXT,
    category      TEXT,
    product_id    TEXT,
    active        INTEGER DEFAULT 1,
    first_seen    TEXT,
    updated_at    TEXT,
    UNIQUE (shop_id, url)
);
CREATE INDEX IF NOT EXISTS offers_product ON offers(product_id);
CREATE TABLE IF NOT EXISTS price_history (
    offer_id   INTEGER NOT NULL REFERENCES offers(id),
    day        TEXT NOT NULL,
    price_base REAL,
    PRIMARY KEY (offer_id, day)
);
CREATE TABLE IF NOT EXISTS products (
    id             TEXT PRIMARY KEY,
    title          TEXT,
    norm_title     TEXT,
    category       TEXT,
    brand          TEXT,
    image          TEXT,
    ean            TEXT,
    min_price      REAL,
    max_price      REAL,
    shop_count     INTEGER,
    in_stock_count INTEGER
);
CREATE INDEX IF NOT EXISTS products_cat ON products(category, min_price);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn
