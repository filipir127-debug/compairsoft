"""Shared pieces for all data sources: the Offer record, HTTP fetching, price parsing."""
from __future__ import annotations

import gzip
import logging
import re
import threading
import time
import unicodedata
from dataclasses import dataclass
from urllib import robotparser
from urllib.parse import urlsplit

import requests

log = logging.getLogger(__name__)


@dataclass
class Offer:
    url: str
    title: str
    price: float | None
    currency: str = "CZK"
    in_stock: bool | None = None
    ean: str | None = None
    brand: str | None = None
    image: str | None = None
    shop_category: str | None = None


# ---------------------------------------------------------------- prices

_CURRENCY_HINTS = [
    (re.compile(r"kč|czk", re.I), "CZK"),
    (re.compile(r"€|eur", re.I), "EUR"),
    (re.compile(r"zł|pln", re.I), "PLN"),
    (re.compile(r"\$|usd", re.I), "USD"),
    (re.compile(r"£|gbp", re.I), "GBP"),
    (re.compile(r"ft|huf", re.I), "HUF"),
]


def parse_currency(text: str | None, default: str = "CZK") -> str:
    if not text:
        return default
    for rx, code in _CURRENCY_HINTS:
        if rx.search(str(text)):
            return code
    return default


def parse_price(value) -> float | None:
    """Parse '1 299 Kč', '1.299,00 €', '1299.00 CZK', 1299 → 1299.0."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).replace("\xa0", " ").replace(" ", " ")
    m = re.search(r"\d[\d .,']*", s)
    if not m:
        return None
    num = re.sub(r"[ ']", "", m.group(0)).rstrip(".,")
    if "," in num and "." in num:
        if num.rfind(",") > num.rfind("."):
            num = num.replace(".", "").replace(",", ".")
        else:
            num = num.replace(",", "")
    elif "," in num:
        head, _, tail = num.rpartition(",")
        num = head.replace(",", "") + ("." + tail if len(tail) in (1, 2) else tail)
    elif num.count(".") > 1 or (num.count(".") == 1 and len(num.rpartition(".")[2]) == 3):
        num = num.replace(".", "")  # dots used as thousands separators
    try:
        return float(num)
    except ValueError:
        return None


def clean_ean(value) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", str(value))
    if 8 <= len(digits) <= 14 and set(digits) != {"0"}:
        return digits.lstrip("0").zfill(13) if len(digits) <= 13 else digits
    return None


def parse_availability(value) -> bool | None:
    if value is None:
        return None
    s = "".join(c for c in unicodedata.normalize("NFKD", str(value).strip().lower()) if not unicodedata.combining(c))
    if s in ("0", "true", "yes", "1"):  # Heureka DELIVERY_DATE 0 = in stock
        return True
    if re.search(r"out ?of ?stock|out_of_stock|soldout|sold out|discontinued|preorder|backorder|nen[i]? skladem|vyprodano|nedostup", s):
        return False
    if re.search(r"instock|in[ _]stock|skladem|limitedavailability|onlineonly|na sklade", s):
        return True
    if s.isdigit():  # delivery in N days
        return int(s) <= 1
    return None


# ---------------------------------------------------------------- HTTP

class Fetcher:
    """Polite HTTP client: one request per `delay` seconds per host, honours robots.txt."""

    def __init__(self, user_agent: str, delay: float = 1.0, timeout: float = 30, respect_robots: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Language": "cs,sk;q=0.9,en;q=0.8",
        })
        self.delay = delay
        self.timeout = timeout
        self.respect_robots = respect_robots
        self._last: dict[str, float] = {}
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}
        self._lock = threading.Lock()

    def _wait(self, host: str) -> None:
        with self._lock:
            last = self._last.get(host, 0.0)
            wait = last + self.delay - time.monotonic()
            self._last[host] = max(time.monotonic(), last + self.delay)
        if wait > 0:
            time.sleep(wait)

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            rp = robotparser.RobotFileParser()
            try:
                r = self.session.get(base + "/robots.txt", timeout=self.timeout)
                rp.parse(r.text.splitlines() if r.ok else [])
            except requests.RequestException:
                rp.parse([])
            self._robots[base] = rp
        rp = self._robots[base]
        return rp is None or rp.can_fetch(self.session.headers["User-Agent"], url)

    def get(self, url: str, check_robots: bool = True) -> requests.Response | None:
        if check_robots and not self.allowed(url):
            log.info("robots.txt disallows %s", url)
            return None
        self._wait(urlsplit(url).netloc)
        try:
            r = self.session.get(url, timeout=self.timeout)
        except requests.RequestException as e:
            log.warning("GET %s failed: %s", url, e)
            return None
        if r.status_code != 200:
            log.debug("GET %s -> %s", url, r.status_code)
            return None
        return r

    def get_bytes(self, url: str, check_robots: bool = True) -> bytes | None:
        r = self.get(url, check_robots)
        if r is None:
            return None
        data = r.content
        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        return data
