"""Command line:  python -m airsoftcompare <command>

  update [--shop NAME ...]   download all (or selected) shops and re-match products
  rematch                     only re-run product matching (after editing keywords/threshold)
  serve [--port 8000]         start the website
  probe URL                   inspect a shop and suggest a shops.yaml entry
  demo                        load fictional sample shops so you can try the site
"""
from __future__ import annotations

import argparse
import logging
import os
import sys


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="airsoftcompare", description="Airsoft e-shop price comparison")
    ap.add_argument("-c", "--config", default="shops.yaml", help="config file (default: shops.yaml)")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("update", help="download shops and rebuild comparisons")
    up.add_argument("--shop", action="append", help="only update this shop (repeatable)")
    up.add_argument("--every", type=float, metavar="HOURS", help="keep running, updating every N hours")
    up.add_argument("--max-minutes", type=float, help="stop crawling after this long; the rest continues next run")
    up.add_argument("--batch", action="store_true", help="match products once at the end (for scheduled jobs)")
    ex = sub.add_parser("export", help="write the whole site as static files (for Cloudflare Pages)")
    ex.add_argument("out", nargs="?", default="dist")
    sub.add_parser("rematch", help="re-run product matching only")
    sv = sub.add_parser("serve", help="run the website")
    sv.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    sv.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    sv.add_argument("--update-every", type=float, metavar="HOURS",
                    help="also download shop prices in the background every N hours")
    pr = sub.add_parser("probe", help="inspect a shop URL and suggest config")
    pr.add_argument("url")
    sub.add_parser("demo", help="load sample data from fictional shops")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    for noisy in ("urllib3", "charset_normalizer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    from . import config as cfgmod

    if args.cmd == "probe":
        from .probe import probe
        cfg = cfgmod.load(args.config) if os.path.exists(args.config) else {"settings": cfgmod.DEFAULTS}
        probe(args.url, cfg["settings"])
        return

    if args.cmd == "demo":
        from .demo import load_demo
        load_demo()
        return

    if not os.path.exists(args.config):
        sys.exit(f"Config file {args.config} not found.")
    cfg = cfgmod.load(args.config)

    if args.cmd == "update":
        from .updater import update_all
        import time
        while True:
            update_all(cfg, args.shop, args.max_minutes, args.batch)
            if not args.every:
                break
            logging.info("Next update in %.1f h", args.every)
            time.sleep(args.every * 3600)
    elif args.cmd == "export":
        from .export import export_site
        export_site(cfg, args.out)
    elif args.cmd == "rematch":
        from . import db
        from .categories import categorize
        from .matching import rebuild_products
        from .text import normalize
        conn = db.connect(cfg["settings"]["database"])
        rows = conn.execute("SELECT id, title, shop_category FROM offers").fetchall()
        with conn:
            conn.executemany("UPDATE offers SET norm_title = ?, category = ? WHERE id = ?",
                             [(normalize(r["title"]), categorize(r["title"], r["shop_category"]), r["id"]) for r in rows])
        n = rebuild_products(conn, cfg["settings"]["match_threshold"])
        logging.info("Matched %d offers into %d products.", len(rows), n)
    elif args.cmd == "serve":
        import uvicorn
        os.environ["AIRSOFT_CONFIG"] = os.path.abspath(args.config)
        if args.update_every:
            import threading
            import time
            from .updater import update_all

            def loop():
                while True:
                    try:
                        update_all(cfg)
                    except Exception:
                        logging.exception("Background update failed")
                    time.sleep(args.update_every * 3600)
            threading.Thread(target=loop, daemon=True).start()
        print(f"Open http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}")
        uvicorn.run("airsoftcompare.web:create_app", factory=True, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
