"""Text normalisation used for searching and for matching the same product across shops."""
from __future__ import annotations

import re
import unicodedata


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


# Words that differ between shops but don't change what the product is.
STOPWORDS = {
    "airsoft", "airsoftova", "airsoftovy", "airsoftove", "asg", "novinka", "new", "akce", "sale",
    "vyprodej", "skladem", "ks", "kus", "the", "for", "pro", "na", "s", "se", "with", "a", "and",
    "replika", "replica", "barva", "color", "colour", "verze", "version", "model",
    "sight", "zamerovac", "takticke", "takticky", "tactical", "upgrade", "carbine", "pcs", "spodni", "casti",
}

COLORS = {"black", "green", "olive", "tan", "brown", "grey", "white", "red", "blue", "multicam",
          "woodland", "coyote", "ranger", "wolf", "atacs", "flecktarn", "vz95", "camo", "pink", "orange"}

# Unify Czech/Slovak/English spellings of the same thing.
SYNONYMS = {
    "cerna": "black", "cerny": "black", "cerne": "black", "cierna": "black", "cierny": "black", "bk": "black", "blk": "black",
    "zelena": "green", "zeleny": "green", "olivova": "olive", "od": "olive", "olive drab": "olive",
    "piskova": "tan", "piskovy": "tan", "de": "tan", "fde": "tan", "desert": "tan", "khaki": "tan",
    "hneda": "brown", "seda": "grey", "sedy": "grey", "gray": "grey", "bila": "white", "biela": "white",
    "cervena": "red", "modra": "blue",
    "maska": "mask", "masky": "mask", "zasobnik": "magazine", "zasobniky": "magazine", "mag": "magazine",
    "mags": "magazine", "kolimator": "reddot", "red dot": "reddot", "puskohled": "scope",
    "kulicky": "bbs", "bb": "bbs", "brýle": "goggles", "bryle": "goggles", "rukavice": "gloves",
    "nabojnice": "shell", "rana": "rds", "ran": "rds", "rd": "rds", "rounds": "rds", "nabojov": "rds",
    "pistole": "pistol", "puska": "rifle", "baterie": "battery", "akumulator": "battery",
    "helma": "helmet", "prilba": "helmet", "pruzina": "spring", "gumicka": "bucking", "svitilna": "light",
    "zvetsovac": "magnifier", "popruh": "sling", "dvoubodovy": "two point", "jednobodovy": "one point",
    "nosic platu": "plate carrier", "hrudnik": "chest rig", "sumka": "pouch", "holograficky": "holo",
    "plyn": "gas", "montazi": "mount", "montaz": "mount", "montazou": "mount", "rukavice": "gloves",
    "coyote brown": "coyote", "ranger green": "ranger", "green gas": "greengas", "red gas": "redgas",
    "black gas": "blackgas", "top gas": "topgas",
    "midcap": "mid cap", "hicap": "hi cap", "lowcap": "low cap", "realcap": "real cap",
}

_MULTI = sorted((k for k in SYNONYMS if " " in k), key=len, reverse=True)


def normalize(title: str) -> str:
    t = strip_accents(title.lower())
    t = re.sub(r"(\d)[.,](\d)", r"\1\2", t)               # 1.000 → 1000, 0,25 → 025
    t = re.sub(r"(\d+)\s*(rds?|ran|bb|ks|mah|g|j|fps)\b", r"\1 \2", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    for phrase in _MULTI:
        t = re.sub(rf"\b{phrase}\b", SYNONYMS[phrase], t)
    words = [SYNONYMS.get(w, w) for w in t.split()]
    seen, out = set(), []
    for w in " ".join(words).split():  # drop stopwords and repeated words
        if w not in STOPWORDS and w not in seen:
            seen.add(w)
            out.append(w)
    return " ".join(out)


def numbers(norm: str) -> frozenset[str]:
    """Numbers in a title (capacity, model, mAh…). Two offers must share them to match."""
    return frozenset(n.lstrip("0") or "0" for n in re.findall(r"\d+", norm))


def colors(norm: str) -> frozenset[str]:
    return frozenset(w for w in norm.split() if w in COLORS)
