"""Shared pieces for all data sources: the Offer record, HTTP fetching, price parsing."""
from __future__ import annotations

import gzip
import io
import ipaddress
import logging
import re
import socket
import threading
import time
import unicodedata
import zlib
from dataclasses import dataclass
from urllib import robotparser
from urllib.parse import urljoin, urlsplit

import requests

log = logging.getLogger(__name__)

# Largest download we accept (feeds of big shops are tens of MB). Own limit, not from a spec.
MAX_DOWNLOAD_BYTES = 256 * 1024 * 1024
# robots.txt: RFC 9309 section 2.5 asks crawlers to parse at least 500 KiB; anything beyond is cut off.
MAX_ROBOTS_BYTES = 512 * 1024


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
        # GTIN-8/12/13 and a GTIN-14 with a leading 0 are the same number padded differently.
        core = digits.lstrip("0")
        return core.zfill(13) if len(core) <= 13 else core
    return None


def safe_url(value, base: str | None = None) -> str | None:
    """Absolute http(s) URL, or None. Shop data is untrusted: a feed could carry
    `javascript:` links that would run in our visitors' browsers."""
    if not value:
        return None
    url = str(value).strip()
    if base:
        url = urljoin(base, url)
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        return None
    return url


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
            r = self._fetch(base + "/robots.txt", MAX_ROBOTS_BYTES, truncate=True)
            rp.parse(r.text.splitlines() if r is not None else [])
            self._robots[base] = rp
        rp = self._robots[base]
        return rp is None or rp.can_fetch(self.session.headers["User-Agent"], url)

    def _fetch(self, url: str, cap: int, truncate: bool = False) -> requests.Response | None:
        """GET with a size cap: the body is streamed and dropped once it exceeds `cap` bytes,
        or with `truncate`, cut to its first `cap` bytes (robots.txt: an oversized file must
        still be obeyed, so we read its beginning instead of ignoring it)."""
        if not public_host(url):
            log.warning("GET %s refused: not a public internet address", url)
            return None
        try:
            r = self.session.get(url, timeout=self.timeout, stream=True, hooks={"response": _refuse_private_redirect})
        except requests.RequestException as e:
            log.warning("GET %s failed: %s", url, e)
            return None
        try:
            if r.status_code != 200:
                log.debug("GET %s -> %s", url, r.status_code)
                return None
            try:
                declared = int(r.headers.get("Content-Length") or 0)
            except ValueError:
                declared = 0
            if declared > cap and not truncate:
                log.warning("GET %s: %d bytes announced, limit is %d, skipped", url, declared, cap)
                return None
            chunks, size, cut = [], 0, False
            for chunk in r.iter_content(1 << 16):
                size += len(chunk)
                if size > cap:
                    if truncate:
                        chunks.append(chunk[:len(chunk) - (size - cap)])
                        cut = True
                        break
                    log.warning("GET %s: response larger than %d bytes, skipped", url, cap)
                    return None
                chunks.append(chunk)
        except requests.RequestException as e:
            log.warning("GET %s failed while reading: %s", url, e)
            return None
        finally:
            r.close()
        body = b"".join(chunks)
        if cut:  # drop the half line: "Allow: /shop/x" cut to "Allow: /" would allow everything
            body = body[:body.rfind(b"\n") + 1]
        r._content = body  # later .content / .text read from memory
        return r

    def get(self, url: str, check_robots: bool = True) -> requests.Response | None:
        if check_robots and not self.allowed(url):
            log.info("robots.txt disallows %s", url)
            return None
        self._wait(urlsplit(url).netloc)
        return self._fetch(url, MAX_DOWNLOAD_BYTES)

    def get_bytes(self, url: str, check_robots: bool = True) -> bytes | None:
        r = self.get(url, check_robots)
        if r is None:
            return None
        data = r.content
        if data[:2] == b"\x1f\x8b":
            data = _gunzip(data, url)
        return data


def public_host(url: str) -> bool:
    """True when every address the URL's host resolves to is on the public internet. Shop data
    (sitemaps, redirects) must not make the crawler reach localhost, private networks or cloud
    metadata services."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80))
    except (socket.gaierror, UnicodeError):
        return True  # let the request itself fail with a normal network error
    return all(ipaddress.ip_address(info[4][0].split("%")[0]).is_global for info in infos)


def _refuse_private_redirect(r: requests.Response, *args, **kwargs):
    if r.is_redirect:
        target = urljoin(r.url, r.headers.get("Location", ""))
        if not public_host(target):
            raise requests.exceptions.InvalidURL(f"redirect to a non-public address refused: {target}")


def _gunzip(data: bytes, url: str) -> bytes | None:
    """Decompress a .gz body, refusing anything that expands beyond MAX_DOWNLOAD_BYTES."""
    chunks, size = [], 0
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
            while chunk := gz.read(1 << 20):
                size += len(chunk)
                if size > MAX_DOWNLOAD_BYTES:
                    log.warning("%s: unpacks to more than %d bytes, skipped", url, MAX_DOWNLOAD_BYTES)
                    return None
                chunks.append(chunk)
    except (OSError, EOFError, zlib.error) as e:  # truncated / corrupt .gz must not abort the shop
        log.warning("%s: broken gzip data: %s", url, e)
        return None
    return b"".join(chunks)
