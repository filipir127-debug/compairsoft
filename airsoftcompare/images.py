"""Small local copies of product photos.

Each product photo is downloaded once, shrunk to fit 450 x 450 and stored as WebP next to the
database (``thumbs/``). The site shows these copies; the shop's original is only loaded when a
visitor opens the photo on a product page.

Cloudflare Pages allows 20 000 files per project, so the copies are split over a few image-only
Pages projects by the first character of their file name (see ``bucket``).
"""
from __future__ import annotations

import hashlib
import io
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from . import db as dbmod
from .sources.common import Fetcher, safe_url

log = logging.getLogger(__name__)

SIZE = 450
QUALITY = 78
BUCKETS = 3                 # image projects; ~11 000 photos each today, room to grow to ~57 000
MAX_PER_BUCKET = 19_500     # stay under the Pages limit of 20 000 files
MAX_SOURCE_BYTES = 15 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 40_000_000  # refuse decompression bombs


def thumb_name(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:20] + ".webp"


def bucket(name: str) -> int:
    return int(name[0], 16) % BUCKETS


def thumbs_dir(settings: dict) -> Path:
    return Path(settings["database"]).parent / "thumbs"


def make_thumb(data: bytes) -> bytes | None:
    """Fit inside SIZE x SIZE (never enlarged), flatten transparency onto white, encode WebP."""
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.draft("RGB", (SIZE * 2, SIZE * 2))  # fast JPEG downscale while decoding
            im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
            im.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
            if im.mode == "RGBA":
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.getchannel("A"))
                im = bg
            out = io.BytesIO()
            im.save(out, "WEBP", quality=QUALITY, method=4)
            return out.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as e:
        log.debug("not an image: %s", e)
        return None


def cache_images(cfg: dict, max_minutes: float | None = None) -> None:
    """Create missing thumbnails, most-compared products first, until the time budget runs out."""
    settings = cfg["settings"]
    conn = dbmod.connect(settings["database"])
    out = thumbs_dir(settings)
    out.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max_minutes * 60 if max_minutes is not None else None
    fetcher = Fetcher(settings["user_agent"], 0.5, 30, settings["respect_robots"])

    urls = [r[0] for r in conn.execute(
        "SELECT image FROM products WHERE image IS NOT NULL ORDER BY shop_count DESC, in_stock_count DESC")]
    todo = [u for u in dict.fromkeys(safe_url(u) for u in urls) if u and not (out / thumb_name(u)).exists()]
    failed_marker = out / ".failed"
    failed = set(failed_marker.read_text().split()) if failed_marker.exists() else set()
    todo = [u for u in todo if thumb_name(u) not in failed]
    log.info("Photos: %d cached, %d to do", sum(1 for _ in out.glob("*.webp")), len(todo))

    def one(url: str) -> None:
        if deadline and time.time() > deadline:
            return
        r = fetcher.get(url)  # per-shop delay and robots.txt, like the crawler
        thumb = make_thumb(r.content) if r is not None and len(r.content) <= MAX_SOURCE_BYTES else None
        if thumb:
            (out / thumb_name(url)).write_bytes(thumb)
        else:
            failed.add(thumb_name(url))  # don't retry broken links every run

    # Photos come from many shops; each keeps its own polite delay, so shops are fetched side by side.
    with ThreadPoolExecutor(max_workers=8) as pool:
        for n, _ in enumerate(pool.map(one, todo), 1):
            if n % 1000 == 0:
                log.info("Photos: %d of %d", n, len(todo))
    if deadline and time.time() > deadline:
        log.info("Photos: time budget used up; the rest continues next run")
    failed_marker.write_text("\n".join(sorted(failed)))
    log.info("Photos: %d cached in total", sum(1 for _ in out.glob("*.webp")))


def published_thumbs(settings: dict) -> dict[str, str]:
    """image URL hash name -> public URL, for thumbnails that exist and fit the per-project limit."""
    base = settings.get("image_hosts") or []
    out = thumbs_dir(settings)
    if len(base) < BUCKETS or not out.exists():
        return {}
    counts = [0] * BUCKETS
    result = {}
    for f in sorted(out.glob("*.webp")):
        b = bucket(f.name)
        if counts[b] < MAX_PER_BUCKET:
            counts[b] += 1
            result[f.name] = f"{base[b].rstrip('/')}/{f.name}"
    return result


def export_buckets(settings: dict, dest: Path) -> list[Path]:
    """Folders img-0 .. img-N, each ready to upload as its own Pages project."""
    out = thumbs_dir(settings)
    published = published_thumbs(settings)
    import shutil
    if dest.exists():
        shutil.rmtree(dest)
    dirs = []
    for b in range(BUCKETS):
        d = dest / f"img-{b}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "_headers").write_text(
            "/*\n  Cache-Control: public, max-age=31536000, immutable\n  X-Content-Type-Options: nosniff\n"
            "  Cross-Origin-Resource-Policy: cross-origin\n", encoding="utf-8")
        (d / "index.html").write_text("<!doctype html><title>images</title>", encoding="utf-8")
        dirs.append(d)
    for name in published:
        target = dest / f"img-{bucket(name)}" / name
        try:
            target.hardlink_to(out / name)
        except OSError:
            target.write_bytes((out / name).read_bytes())
    log.info("Photo folders: %s", ", ".join(f"{d.name}: {sum(1 for _ in d.glob('*.webp'))}" for d in dirs))
    return dirs
