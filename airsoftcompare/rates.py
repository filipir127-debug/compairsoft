"""Daily exchange rates from the Czech National Bank (CZK per unit), with the config as fallback."""
from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)
CNB_URL = ("https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/"
           "kurzy-devizoveho-trhu/denni_kurz.txt")
SHOWN = ("CZK", "EUR", "USD", "GBP", "PLN")  # currencies offered in the site's currency picker


def parse_cnb(text: str) -> tuple[str, dict[str, float]]:
    lines = text.strip().splitlines()
    day = lines[0].split()[0]
    rates = {"CZK": 1.0}
    for line in lines[2:]:
        parts = line.split("|")
        if len(parts) == 5:
            _, _, amount, code, rate = parts
            rates[code] = float(rate.replace(",", ".")) / float(amount)
    return day, rates


def current_rates(settings: dict) -> tuple[str | None, dict[str, float]]:
    """(date, rates). Falls back to settings.exchange_rates when the ČNB can't be reached."""
    fallback = {"CZK": 1.0, **settings.get("exchange_rates", {})}
    if settings.get("base_currency", "CZK") != "CZK":
        return None, fallback
    try:
        r = requests.get(CNB_URL, timeout=20, headers={"User-Agent": settings.get("user_agent", "AirsoftCompare")})
        r.raise_for_status()
        day, rates = parse_cnb(r.text)
        return day, {**fallback, **rates}
    except (requests.RequestException, ValueError, IndexError) as e:
        log.warning("ČNB exchange rates unavailable (%s); using the rates from the config", e)
        return None, fallback
