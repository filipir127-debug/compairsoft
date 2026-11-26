from __future__ import annotations

from pathlib import Path

import yaml

DEFAULTS = {
    "database": "airsoft.db",
    "base_currency": "CZK",
    "exchange_rates": {"CZK": 1.0, "EUR": 25.0, "PLN": 5.9, "USD": 23.0, "GBP": 29.5, "HUF": 0.063},
    "user_agent": "AirsoftCompare/0.1 (personal price comparison)",
    "request_delay": 1.5,
    "timeout": 30,
    "respect_robots": True,
    "match_threshold": 90,
    "recrawl_hours": 20,
    "parallel_shops": 4,
}


def load(path: str | Path = "shops.yaml") -> dict:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = {**DEFAULTS, **(data.get("settings") or {})}
    settings["exchange_rates"] = {**DEFAULTS["exchange_rates"], **(settings.get("exchange_rates") or {})}
    db = Path(settings["database"])
    if not db.is_absolute():
        settings["database"] = str((path.parent / db).resolve())
    shops = [s for s in (data.get("shops") or []) if s.get("enabled", True)]
    for s in shops:
        for key in ("feed_url", "sitemap_url"):
            v = s.get(key)
            if v and not v.startswith(("http://", "https://")):
                s[key] = str((path.parent / v).resolve())
    return {"settings": settings, "shops": shops}
