"""Machine translation of product and offer names (Czech -> English -> German).

Uses the open Argos Translate models (CTranslate2) offline, so nothing is sent to a translation
service. An airsoft glossary runs first, because the general-purpose models translate trade terms
badly ("zásobník" -> "tray" instead of "magazine"). Slovak visitors see the Czech original, which
reads better than a Czech -> English -> Slovak round trip.

Translations are cached in the database; each name is translated once.
"""
from __future__ import annotations

import logging
import os
import re
import time
import zipfile
from pathlib import Path

import requests

from . import db as dbmod

log = logging.getLogger(__name__)

LANGS = ("en", "de")
MODELS = {  # Argos Translate packages
    "cs_en": "https://argos-net.com/v1/translate-cs_en-1_9_6.argosmodel",
    "en_de": "https://argos-net.com/v1/translate-en_de-1_3.argosmodel",
}
BATCH = 48

# Czech airsoft terms -> English, applied before translating (the model leaves English words alone).
# Keys are matched case-insensitively as whole words; longest first.
GLOSSARY = {
    "zásobník": "magazine", "zásobníky": "magazines", "zásobníku": "magazine", "zásobníků": "magazines",
    "zásobníkem": "magazine", "zásobníkové": "magazine",
    "ran": "rounds", "kuliček": "BBs", "kuličky": "BBs", "kuličková": "ball", "bb kuličky": "BBs",
    "závěr": "bolt", "závěru": "bolt", "závěrem": "bolt", "trn": "pin",
    "přerušovač": "cut-off lever", "přerušovače": "cut-off lever",
    "hop-up gumička": "hop-up bucking", "gumička": "bucking", "gumičky": "buckings",
    "hlaveň": "barrel", "hlavně": "barrel", "hlavni": "barrel", "přesná hlaveň": "precision barrel",
    "píst": "piston", "pístu": "piston", "hlava pístu": "piston head", "hlava válce": "cylinder head",
    "válec": "cylinder", "válce": "cylinder", "tryska": "nozzle", "trysky": "nozzles",
    "mechabox": "gearbox", "ozubená kola": "gears", "ozubené kolo": "gear",
    "pružina": "spring", "pružiny": "springs", "pružinu": "spring",
    "spoušť": "trigger", "spouště": "trigger", "spoušťový": "trigger",
    "pažba": "stock", "pažby": "stock", "pažbička": "stock", "předpažbí": "handguard",
    "rukojeť": "grip", "rukojeti": "grip", "kolimátor": "red dot", "kolimátory": "red dots",
    "puškohled": "scope", "puškohledy": "scopes", "montáž": "mount", "montáže": "mount",
    "tlumič": "suppressor", "tlumiče": "suppressor", "plamenná": "flash", "lišta": "rail", "lišty": "rails",
    "sumka": "pouch", "sumky": "pouches", "sumku": "pouch", "nosič plátů": "plate carrier",
    "taktická vesta": "tactical vest", "vesta": "vest", "opasek": "belt", "popruh": "sling", "pouzdro": "holster",
    "nabíječka": "charger", "akumulátor": "battery", "baterie": "battery",
    "brýle": "goggles", "ochranné brýle": "safety goggles", "maska": "mask", "helma": "helmet", "přilba": "helmet",
    "rukavice": "gloves", "kalhoty": "trousers", "bunda": "jacket", "blůza": "shirt", "nášivka": "patch",
    "odstřelovací puška": "sniper rifle", "samopal": "submachine gun", "útočná puška": "assault rifle",
    "airsoftová zbraň": "airsoft gun", "airsoftová puška": "airsoft rifle", "airsoftová pistole": "airsoft pistol",
    "pistole": "pistol", "puška": "rifle", "brokovnice": "shotgun", "kulomet": "machine gun", "revolver": "revolver",
    "celokov": "full metal", "celokovová": "full metal", "kovový": "metal", "kovová": "metal", "kovové": "metal",
    "černá": "black", "černý": "black", "černé": "black", "písková": "tan", "pískový": "tan", "pískové": "tan",
    "olivová": "olive", "olivový": "olive", "zelená": "green", "zelený": "green", "šedá": "grey", "šedý": "grey",
    "hnědá": "brown", "hnědý": "brown", "bílá": "white", "bílý": "white", "červená": "red", "modrá": "blue",
    "varianta": "variant", "zvolte": "choose", "velikost": "size",
}
_GLOSS = sorted(GLOSSARY.items(), key=lambda kv: -len(kv[0]))
_GLOSS_RX = re.compile(r"(?<![\w&])(" + "|".join(re.escape(k) for k, _ in _GLOSS) + r")(?![\w&])", re.I)
# Kept exactly as written: "Heckler&Koch", "M4/AR15", model codes like "CM.090".
_PROTECT = re.compile(r"\b\w*[A-Za-z]\w*[&/.]\w+(?:[&/.]\w+)*\b|\b\w+[&/]\w+\b")


def glossary(text: str) -> str:
    return _GLOSS_RX.sub(lambda m: GLOSSARY[m.group(1).lower()], text)


def models_dir(settings: dict) -> Path:
    return Path(os.environ.get("AIRSOFT_MODELS") or Path(settings["database"]).parent / "models")


def _download(name: str, url: str, dest: Path) -> Path:
    target = dest / name
    if (target / "model").exists():
        return target
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / f"{name}.zip"
    log.info("Downloading translation model %s", name)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    with zipfile.ZipFile(tmp) as z:
        root = z.namelist()[0].split("/")[0]
        z.extractall(dest)
    (dest / root).rename(target)
    tmp.unlink()
    return target


class _Model:
    def __init__(self, path: Path, src: str, tgt: str):
        import ctranslate2
        self.tr = ctranslate2.Translator(str(path / "model"), device="cpu", compute_type="int8",
                                         intra_threads=os.cpu_count() or 2)
        if (path / "bpe.model").exists():  # subword-nmt BPE + Moses tokenisation
            from sacremoses import MosesDetokenizer, MosesTokenizer
            from subword_nmt.apply_bpe import BPE
            with open(path / "bpe.model", encoding="utf-8") as f:
                self.bpe = BPE(f)
            self.mt, self.md = MosesTokenizer(src), MosesDetokenizer(tgt)
            self.encode = lambda t: self.bpe.segment_tokens(self.mt.tokenize(t, escape=False))
            self.decode = lambda toks: self.md.detokenize(" ".join(toks).replace("@@ ", "").split())
        else:  # SentencePiece
            import sentencepiece as spm
            self.sp = spm.SentencePieceProcessor(model_file=str(path / "sentencepiece.model"))
            self.encode = lambda t: self.sp.encode(t, out_type=str)
            self.decode = lambda toks: self.sp.decode(toks).replace("▁", " ").strip()

    def __call__(self, texts: list[str]) -> list[str]:
        res = self.tr.translate_batch([self.encode(t) for t in texts], beam_size=2, max_batch_size=BATCH,
                                      max_decoding_length=160)
        return [re.sub(r"\s+", " ", self.decode(r.hypotheses[0])).replace(" - ", " - ").strip() for r in res]


class _Locker:
    """Swaps fixed terms for placeholders the model copies through, and puts them back afterwards."""

    def __init__(self, brands: set[str]):
        words = sorted((b for b in brands if len(b) > 2), key=len, reverse=True)
        self.brands = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, words)) + r")(?!\w)") if words else None

    def lock(self, text: str, use_glossary: bool) -> tuple[str, list[str]]:
        kept: list[str] = []

        def keep(value: str) -> str:
            kept.append(value)
            return f" X{len(kept) - 1}X "
        text = _PROTECT.sub(lambda m: keep(m.group(0)), text)
        if self.brands:
            text = self.brands.sub(lambda m: keep(m.group(0)), text)
        if use_glossary:
            text = _GLOSS_RX.sub(lambda m: keep(GLOSSARY[m.group(1).lower()]), text)
        return re.sub(r"\s+", " ", text).strip(), kept

    @staticmethod
    def unlock(text: str, kept: list[str]) -> str:
        for i in range(len(kept) - 1, -1, -1):  # X10X before X1X
            text = re.sub(rf"X\s*{i}\s*X", lambda _m, v=kept[i]: v, text)
        text = re.sub(r"(\w)- (\w)", r"\1-\2", text)       # "Hi- Capa" -> "Hi-Capa"
        text = re.sub(r"\s+([™®,.:;)])", r"\1", text).replace("( ", "(")
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1].upper() + text[1:]


def translate_names(cfg: dict, max_minutes: float | None = None) -> None:
    """Translate product and offer names that have no translation yet, most-compared products first."""
    settings = cfg["settings"]
    conn = dbmod.connect(settings["database"])
    conn.execute("CREATE TABLE IF NOT EXISTS translations (src TEXT, lang TEXT, text TEXT, PRIMARY KEY (src, lang))")
    deadline = time.time() + max_minutes * 60 if max_minutes is not None else None

    names = [r[0] for r in conn.execute(
        "SELECT p.title FROM products p ORDER BY p.shop_count DESC, p.in_stock_count DESC")]
    names += [r[0] for r in conn.execute(
        "SELECT o.title FROM offers o JOIN products p ON p.id = o.product_id ORDER BY p.shop_count DESC")]
    done = {r[0] for r in conn.execute("SELECT src FROM translations WHERE lang = 'de'")}
    todo = [n for n in dict.fromkeys(names) if n not in done]
    log.info("Translations: %d names cached, %d to do", len(done), len(todo))
    if not todo:
        return

    mdir = models_dir(settings)
    cs_en = _Model(_download("cs_en", MODELS["cs_en"], mdir), "cs", "en")
    en_de = _Model(_download("en_de", MODELS["en_de"], mdir), "en", "de")
    brands = {r[0].strip() for r in conn.execute(
        "SELECT brand FROM products WHERE brand IS NOT NULL GROUP BY lower(brand) HAVING COUNT(*) >= 3")}
    locker = _Locker(brands)
    count = 0
    for i in range(0, len(todo), BATCH):
        if deadline and time.time() > deadline:
            log.info("Translations: time budget used up; %d more next run", len(todo) - i)
            break
        batch = todo[i:i + BATCH]
        en_in = [locker.lock(n, use_glossary=True) for n in batch]
        en = [locker.unlock(t, kept) for t, (_, kept) in zip(cs_en([p for p, _ in en_in]), en_in)]
        de_in = [locker.lock(t, use_glossary=False) for t in en]
        de = [locker.unlock(t, kept) for t, (_, kept) in zip(en_de([p for p, _ in de_in]), de_in)]
        with conn:
            conn.executemany("INSERT OR REPLACE INTO translations VALUES (?, ?, ?)",
                             [(s, "en", e) for s, e in zip(batch, en)] + [(s, "de", d) for s, d in zip(batch, de)])
        count += len(batch)
        if count % 2400 < BATCH:
            log.info("Translations: %d of %d", count, len(todo))
    log.info("Translations: %d names translated this run", count)


def load_translations(conn) -> dict[str, dict[str, str]]:
    """lang -> {original name: translated name}"""
    out: dict[str, dict[str, str]] = {lang: {} for lang in LANGS}
    try:
        for src, lang, text in conn.execute("SELECT src, lang, text FROM translations"):
            if lang in out and text:
                out[lang][src] = text
    except Exception:  # no table yet
        pass
    return out
