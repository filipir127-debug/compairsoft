"""Pages and pictures for promoting the site, built with every export.

* ``/slevy`` – this week's deals: products that got cheaper in the last 7 days, and products where
  the cheapest shop is well below the next cheapest one. Czech, server-rendered, so it can be
  shared and found by search engines without running the app.
* ``/slevy.png`` (1080 x 1350, for a Facebook or Instagram post) and ``/slevy-og.png``
  (1200 x 630, the preview when the /slevy link is shared): the top deals as a picture.
* ``/nejlevnejsi/`` and ``/nejlevnejsi/<guide>``: "the cheapest …" guides for common searches
  (beginner AEGs, 0.25 g BBs by price per 1000, CO2 pistols, …), filled from live prices.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

from .text import strip_accents

log = logging.getLogger(__name__)

HERE = Path(__file__).parent
FONTS = HERE / "assets"  # Inter (OFL), cut down to Latin and Czech letters, for the pictures
WEEK = 7
MAX_DROP = 0.5       # a bigger "discount" is almost always a wrong match or a typo in a feed


def czk(v: float) -> str:
    return f"{round(v):,}".replace(",", " ") + " Kč"


# ---------------------------------------------------------------- deals
def _price_on(series: list[list], day: str) -> float | None:
    """A shop's price on a given day, from its change points ([[day, price], …], oldest first).
    A shop first seen after that day counts with its first known price."""
    price = series[0][1] if series else None
    for d, v in series:
        if d > day:
            break
        price = v
    return price


def find_deals(products: list[dict], offers: dict, history: dict, shop_name: dict, today: date | None = None,
               limit: int = 24) -> dict[str, list[dict]]:
    """Two lists of deals, each item: product id, now (cheapest in-stock price), was, pct, shop.

    "drops": the cheapest in-stock price is 10 %+ below the product's cheapest price a week ago.
    "gaps": the cheapest in-stock shop is 12 %+ (and 100 Kč+) below the next cheapest shop.
    """
    week_ago = ((today or date.today()) - timedelta(days=WEEK)).isoformat()
    drops, gaps = [], []
    for p in products:
        live = [o for o in offers.get(p["id"], []) if o["active"] and o["price_base"]]
        stocked = [o for o in live if o["in_stock"]]
        if not stocked:
            continue
        best = min(stocked, key=lambda o: o["price_base"])
        now = best["price_base"]
        if now < 100:
            continue
        item = {"id": p["id"], "now": now, "shop": shop_name.get(best["shop_id"], "")}
        old = [v for s in history.get(p["id"], {}).values() if (v := _price_on(s, week_ago))]
        if old and min(old) > now and 0.10 <= 1 - now / min(old) <= MAX_DROP:
            drops.append({**item, "was": min(old), "pct": 1 - now / min(old)})
        others = [o["price_base"] for o in live if o["shop_id"] != best["shop_id"]]
        if others:
            nxt = min(others)
            if nxt - now >= 100 and 0.12 <= 1 - now / nxt <= MAX_DROP:
                gaps.append({**item, "was": nxt, "pct": 1 - now / nxt})
    # Biggest saving in Kč first: a 20 % cheaper gun beats a 45 % cheaper spare part.
    key = lambda d: (-(d["was"] - d["now"]), -d["pct"])
    cat = {p["id"]: p.get("category") for p in products}
    drops = _varied(sorted(drops, key=key), cat, 3, limit)
    seen = {d["id"] for d in drops}
    gaps = _varied([d for d in sorted(gaps, key=key) if d["id"] not in seen], cat, 3, limit)
    return {"drops": drops, "gaps": gaps}


def _varied(items: list[dict], cat: dict, per_cat: int, limit: int) -> list[dict]:
    """At most per_cat items of one category, so six machine guns don't fill the list."""
    out, n = [], {}
    for d in items:
        c = cat.get(d["id"])
        if n.get(c, 0) < per_cat:
            out.append(d)
            n[c] = n.get(c, 0) + 1
        if len(out) == limit:
            break
    return out


# ---------------------------------------------------------------- guides
@dataclass
class Guide:
    slug: str
    title: str          # the H1 and <title>
    short: str          # link text on the guides page
    intro: list[str]    # paragraphs
    match: Callable[[dict], bool]
    more: str           # the same products in the app, with all filters
    per: Callable[[dict], float | None] | None = None   # unit price to sort by (BBs: per 1000)
    per_label: str = ""
    tips: list[str] = field(default_factory=list)
    need: str = ""      # the title (lower case, no accents) must match this, e.g. a gun word


# Accessories and spare parts that land in a gun or gear category by mistake, and damaged goods.
_NOT = re.compile(r"\b(prevlek|ghillie|pouzdr|tas(ka|ku)|schrank|pas(ek|ku)|trojnoz|dvojnoz|bipod|tripod|chrono|meric|"
                  r"zasobnik|naboj|nahradni|dil(y|u)?\b|hlaven|poskozen|vadn|baterie|nabijeck|montaz|kryt|popruh|remen|"
                  r"tlumic|optik|kolimator|svitiln|laser|rukojet|pazb|sada|kit\b|prislusenstvi|o-krouz|tesneni|pruzin|"
                  r"bombick|lahev|cistic|olej|mazivo|vesta|ter[cč]|stojan|zavesn|obal|cepic|pasky|set\b|zornik|ubrous|"
                  r"replika pistole|kresadl|perkusn|rucnim natahov|manualni)", re.I)


def _has(c: dict, *tags: str) -> bool:
    return all(t in c.get("a", []) for t in tags)


def _per_1000(c: dict) -> float | None:
    n = (c.get("n") or {}).get("bbcount")
    return c["p"] / n * 1000 if n and n >= 500 else None


GUIDES = [
    Guide("airsoftove-zbrane-pro-zacatecniky", "Nejlevnější airsoftové zbraně pro začátečníky (AEG do 5 000 Kč)",
          "Zbraně pro začátečníky do 5 000 Kč",
          ["Elektrická zbraň (AEG) je pro začátek nejjednodušší volba: stačí nabitá baterie a kuličky, nepotřebuje plyn "
           "a funguje i v zimě. Tady jsou nejlevnější elektrické pušky a samopaly do 5 000 Kč, které má teď některý "
           "český obchod skladem."],
          lambda c: c["c"] in ("guns", "smgs") and _has(c, "pw:electric") and 1500 <= c["p"] <= 5000,
          "/?cat=weapons&power=electric&pmax=5000&stock=1&sort=price_asc",
          need=r"\b(zbran|puska|samopal|karabin|aeg|rifle|carbine|smg|m4|ak|mp5)",
          tips=["Zkontrolujte, jestli je v balení baterie a nabíječka. Pokud ne, počítejte s dalšími 500–1 000 Kč.",
                "Kovová převodovka a kovové ozubení vydrží déle než plastové.",
                "Pro první hry stačí kuličky 0,25 g."]),
    Guide("bb-kulicky-0-25g", "Nejlevnější BB kuličky 0,25 g (cena za 1 000 ks)", "Kuličky 0,25 g podle ceny za 1 000 ks",
          ["Kuličky 0,25 g jsou nejběžnější gramáž pro elektrické zbraně i pistole. Balení se liší velikostí, proto je "
           "porovnáváme podle ceny za 1 000 kusů. Jsou tu jen balení, která má některý obchod skladem."],
          lambda c: c["c"] == "bbs" and _has(c, "bbw:0.25"),
          "/?cat=bbs&bbw=0.25&stock=1&sort=price_asc", per=_per_1000, per_label="za 1 000 ks",
          need=r"\b(kulic|bb)",
          tips=["Bio kuličky se v přírodě rozloží; na mnoha hřištích jsou povinné.",
                "Levné kuličky s otřepy můžou poškodit hlaveň a hop-up. Vyplatí se ověřená značka."]),
    Guide("airsoftove-pistole-co2", "Nejlevnější airsoftové pistole na CO2", "Pistole na CO2",
          ["Pistole na CO2 používají malé 12g bombičky. CO2 funguje lépe než green gas i v chladném počasí, "
           "proto jsou oblíbené po celý rok. Seznam ukazuje nejlevnější CO2 pistole skladem v českých obchodech."],
          lambda c: c["c"] == "pistols" and _has(c, "pw:co2") and c["p"] >= 500,
          "/?cat=pistols&power=co2&stock=1&sort=price_asc",
          need=r"\b(pistol|revolver|co2)",
          tips=["Bombičky CO2 se prodávají zvlášť; jedna vystačí zhruba na jeden až dva zásobníky.",
                "Pistole s blowbackem (pohyblivým závěrem) jsou realističtější, ale spotřebují víc plynu."]),
    Guide("airsoftove-pistole-na-plyn", "Nejlevnější plynové airsoftové pistole (green gas, GBB)", "Plynové pistole (green gas)",
          ["Plynové pistole (GBB) se plní green gasem přímo do zásobníku. Mají realistický zpětný ráz a snadno se "
           "dobíjejí. V chladu pod 10 °C ale ztrácejí výkon. Tady jsou nejlevnější plynové pistole skladem."],
          lambda c: c["c"] == "pistols" and _has(c, "pw:gas") and c["p"] >= 800,
          "/?cat=pistols&power=gas&stock=1&sort=price_asc",
          need=r"\b(pistol|gbb|green ?gas|plyn)",
          tips=["Plyn (green gas) se kupuje zvlášť, láhev vydrží na stovky výstřelů.",
                "Náhradní zásobník se hodí: každý má vlastní zásobu plynu."]),
    Guide("odstrelovaci-pusky", "Nejlevnější airsoftové odstřelovací pušky (sniperky)", "Odstřelovací pušky",
          ["Odstřelovací pušky jsou nejčastěji na pružinu: před každým výstřelem se natahují závěrem, takže nepotřebují "
           "baterii ani plyn. Tady jsou nejlevnější sniperky, které má teď některý obchod skladem."],
          lambda c: c["c"] == "snipers" and c["p"] >= 1500,
          "/?cat=snipers&stock=1&sort=price_asc",
          need=r"\b(sniper|odstrelovac|puska|rifle|vsr|l96|m40|m24|awm|mb\d)",
          tips=["Na hřištích mají sniperky obvykle povolený vyšší výkon, ale i minimální vzdálenost střelby.",
                "Pro přesnou střelbu se používají těžší kuličky, 0,36 g a víc."]),
    Guide("airsoftove-brokovnice", "Nejlevnější airsoftové brokovnice", "Brokovnice",
          ["Airsoftové brokovnice střílí jednu nebo více kuliček najednou, na pružinu nebo na plyn. Hodí se hlavně "
           "do budov (CQB). Tady jsou nejlevnější brokovnice skladem v českých obchodech."],
          lambda c: c["c"] == "shotguns" and c["p"] >= 500,
          "/?cat=shotguns&stock=1&sort=price_asc", need=r"\b(brokovnic|shotgun)"),
    Guide("ochranne-bryle", "Nejlevnější ochranné brýle na airsoft", "Ochranné brýle",
          ["Ochrana očí je na každé airsoftové akci povinná. Seznam ukazuje nejlevnější ochranné brýle a "
           "uzavřené brýle (goggles) skladem. Vybírejte takové, které odolají zásahu kuličkou (norma EN 166 nebo ANSI Z87.1)."],
          lambda c: c["c"] == "eyewear" and c["p"] >= 150,
          "/?cat=eyewear&stock=1&sort=price_asc",
          need=r"\b(bryle|goggle|glasses)",
          tips=["Uzavřené brýle chrání lépe než otevřené, ale víc se mlží. Pomůže větrání nebo ventilátor.",
                "Spodní část obličeje chrání síťka nebo maska."]),
]
LIMIT = 24


def guide_items(g: Guide, cards: list[dict]) -> list[dict]:
    """The guide's products, cheapest first: in stock, unit price (BBs) or price."""
    rows = []
    for c in cards:
        title = strip_accents(c["t"].lower())
        if not (c.get("k") and g.match(c)) or (g.need and not re.search(g.need, title)) or _NOT.search(title):
            continue
        unit = g.per(c) if g.per else c["p"]
        if unit is not None:
            rows.append({**c, "unit": unit})
    rows.sort(key=lambda c: (c["unit"], -c["s"]))
    return rows[:LIMIT]


# ---------------------------------------------------------------- pictures
def _font(size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / f"Inter-{weight}.otf"), size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int, lines: int) -> list[str]:
    out, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
            continue
        if cur:
            out.append(cur)
        cur = word
        if len(out) == lines:
            break
    if cur and len(out) < lines:
        out.append(cur)
    if len(out) == lines and " ".join(out) != " ".join(text.split()):
        last = out[-1]
        while last and draw.textlength(last + "…", font=font) > width:
            last = last[:-1]
        out[-1] = last.rstrip(" ,-–") + "…"
    return out


# the site's "tactical" colours: black-olive ground, olive panels, paper text, signal orange
BG, PANEL, INK, MUTED, ORANGE, GREEN = "#17190f", "#2a2f1b", "#f4f1e6", "#c7bc96", "#ff8a3d", "#7fbf3f"


def deals_picture(items: list[dict], titles: dict, thumbs: Callable[[str], Path | None], size: tuple[int, int],
                  day: date, path: Path) -> None:
    """The top deals as a picture: dark background, one row per product with photo and prices."""
    w, h = size
    tall = h > w
    img = Image.new("RGB", size, BG)
    d = ImageDraw.Draw(img)
    pad = 56 if tall else 48
    d.text((pad, pad - 6), "Slevy týdne", font=_font(84 if tall else 64), fill=INK)
    sub = f"Nejlevnější ceny z českých airsoft obchodů · {day.day}. {day.month}. {day.year}"
    d.text((pad, pad + (100 if tall else 76)), sub, font=_font(30 if tall else 24, "Medium"), fill=MUTED)
    top = pad + (170 if tall else 130)
    foot = 96 if tall else 70
    n = min(len(items), 6 if tall else 3)
    gap = 18
    row_h = (h - top - foot - gap * (n - 1)) // max(n, 1) if n else 0
    name_f, price_f, was_f, small_f = _font(32 if tall else 28, "SemiBold"), _font(46 if tall else 40), _font(28 if tall else 24, "Medium"), _font(24 if tall else 20, "Medium")
    for i, it in enumerate(items[:n]):
        y = top + i * (row_h + gap)
        d.rounded_rectangle((pad, y, w - pad, y + row_h), radius=2, fill=PANEL)
        ph = row_h - 28
        px = pad + 14
        d.rounded_rectangle((px, y + 14, px + ph, y + 14 + ph), radius=2, fill="#ffffff")
        src = thumbs(it["id"])
        if src:
            try:
                photo = Image.open(src).convert("RGBA")
                photo.thumbnail((ph - 16, ph - 16))
                img.paste(photo, (px + (ph - photo.width) // 2, y + 14 + (ph - photo.height) // 2), photo)
            except OSError:
                pass
        x = px + ph + 24
        right = w - pad - 24
        price_w = 300 if tall else 270
        lines = _wrap(d, titles.get(it["id"], ""), name_f, right - price_w - x, 2 if row_h > 120 else 1)
        lh = name_f.size + 8
        ty = y + (row_h - lh * len(lines) - small_f.size - 10) // 2
        for k, line in enumerate(lines):
            d.text((x, ty + k * lh), line, font=name_f, fill=INK)
        d.text((x, ty + len(lines) * lh + 6), it["shop"], font=small_f, fill=MUTED)
        badge = f"−{round(it['pct'] * 100)} %"
        bw = d.textlength(badge, font=small_f) + 24
        py = y + row_h // 2 - price_f.size + 4
        d.text((right, py), czk(it["now"]), font=price_f, fill=ORANGE, anchor="ra")
        was = czk(it["was"])
        ww = d.textlength(was, font=was_f)
        wy = py + price_f.size + 14
        d.text((right - bw - 14, wy), was, font=was_f, fill=MUTED, anchor="ra")
        mid = wy + was_f.size * 0.6
        d.line((right - bw - 14 - ww, mid, right - bw - 14, mid), fill=MUTED, width=2)
        d.rounded_rectangle((right - bw, wy - 2, right, wy + small_f.size + 10), radius=2, fill=GREEN)
        d.text((right - bw / 2, wy + 3), badge, font=small_f, fill="#052e16", anchor="ma")
    d.text((pad, h - foot + (26 if tall else 16)), "compairsoft.eu", font=_font(40 if tall else 32), fill=ORANGE)
    d.text((w - pad, h - foot + (36 if tall else 24)), "Porovnání cen airsoftu na jednom místě",
           font=_font(26 if tall else 22, "Medium"), fill=MUTED, anchor="ra")
    img.save(path, optimize=True)


# ---------------------------------------------------------------- pages
def export_promo(env, out: Path, ctx: dict, products: list[dict], offers: dict, history: dict, shop_name: dict,
                 cards: dict, thumb_of: Callable[[str], Path | None], today: date | None = None) -> list[str]:
    """Write /slevy, its pictures and the guides. Returns their paths for the sitemap."""
    today = today or date.today()
    deals = find_deals(products, offers, history, shop_name, today)
    for kind in deals.values():
        for d in kind:
            d["card"] = cards[d["id"]]
    # The picture: the best price drops and shop gaps, taking turns, one product per category.
    cat = {p["id"]: p.get("category") for p in products}
    turns = [d for pair in zip(deals["drops"] + [None] * 24, deals["gaps"] + [None] * 24) for d in pair if d]
    pics = _varied(turns, cat, 1, 6)
    titles = {d["id"]: d["card"]["t"] for d in pics}
    deals_picture(pics, titles, thumb_of, (1080, 1350), today, out / "slevy.png")
    deals_picture(pics, titles, thumb_of, (1200, 630), today, out / "slevy-og.png")
    site = ctx["site_url"]
    (out / "slevy.html").write_text(env.get_template("deals.html").render(
        page="deals", deals=deals, day=today, czk=czk, guides=GUIDES, **ctx), encoding="utf-8")
    all_cards = list(cards.values())
    (out / "nejlevnejsi").mkdir(exist_ok=True)
    counts = {}
    for g in GUIDES:
        items = guide_items(g, all_cards)
        counts[g.slug] = len(items)
        (out / "nejlevnejsi" / f"{g.slug}.html").write_text(env.get_template("guide.html").render(
            page="guide", g=g, items=items, day=today, czk=czk, guides=GUIDES, **ctx), encoding="utf-8")
    (out / "nejlevnejsi" / "index.html").write_text(env.get_template("guides.html").render(
        page="guide", guides=GUIDES, counts=counts, day=today, **ctx), encoding="utf-8")
    log.info("Promo: %d price drops, %d shop gaps, %d guides", len(deals["drops"]), len(deals["gaps"]), len(GUIDES))
    return ["/slevy", "/nejlevnejsi/"] + [f"/nejlevnejsi/{g.slug}" for g in GUIDES]
