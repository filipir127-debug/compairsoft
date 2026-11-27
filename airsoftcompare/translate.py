"""Machine translation of product and offer names (Czech -> English -> German / Slovak).

Uses the open Argos Translate models (CTranslate2) offline, so nothing is sent to a translation
service. An airsoft glossary runs first, because the general-purpose models translate trade terms
badly ("zásobník" -> "tray" instead of "magazine"). There is no Czech -> Slovak model, so Slovak
goes through English like German does.

Translations are cached in the database; each name is translated once per VERSION. Raise VERSION
after changing the glossary or the rules: names are then translated again (most-compared first),
and the old text is shown until its replacement is ready.
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

LANGS = ("en", "de", "sk")
VERSION = 2
MODELS = {  # Argos Translate packages
    "cs_en": "https://argos-net.com/v1/translate-cs_en-1_9_6.argosmodel",
    "en_de": "https://argos-net.com/v1/translate-en_de-1_3.argosmodel",
    "en_sk": "https://argos-net.com/v1/translate-en_sk-1_9.argosmodel",
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
    "lučík": "trigger guard", "lučíku": "trigger guard", "lučík spouště": "trigger guard",
    "sada kol": "gear set", "sady kol": "gear set", "kola": "gears", "kol": "gears",
    "zátěžová": "high-torque", "zátěžové": "high-torque", "rychlostní": "high-speed",
    "šachta": "magwell", "šachty": "magwell", "patka zásobníku": "magazine base plate", "patka": "base plate",
    "záchyt zásobníku": "magazine catch", "záchyt závěru": "bolt catch", "záchyt": "catch",
    "zásobníková": "magazine", "zásobníkový": "magazine", "opasková": "belt", "opaskový": "belt", "opaskové": "belt",
    "bubnový zásobník": "drum magazine", "tlačný": "mid-cap", "točný": "hi-cap",
    "imitace dřeva": "imitation wood", "pravé dřevo": "real wood", "dřevo": "wood",
    "výsuvná pažba": "retractable stock", "sklopná pažba": "folding stock", "sklopnou pažbou": "folding stock",
    "mířidla": "sights", "mířidlo": "sight", "muška": "front sight", "hledí": "rear sight",
    "dvojnožka": "bipod", "dvojnožkou": "bipod", "lícnice": "cheek rest", "odhazovák": "dump pouch",
    "kukla": "balaclava", "maskáče": "camo", "maskovací": "camouflage", "nosič": "carrier",
    "náhradní díl": "spare part", "díl": "part", "dílů": "parts", "upgrade": "upgrade",
    "manuální": "manual", "manuál": "manual", "dávka": "full auto", "blowback": "blowback",
}
# Words already in English in Czech names (colours, brand words). Kept as written, because the
# models "correct" them: desert -> "dessert", "S&T Armament" -> "S&T Rüstung".
_KEEP = re.compile(r"\b(desert|coyote(?: brown)?|multicam\w*|ranger green|wolf grey|olive drab|foliage green|"
                   r"armament|arms|works)\b", re.I)
# Brand words: any case in a Czech name; in English text only capitalised ("Emerson Gear", not "tactical gear").
_KEEP_BRANDWORDS = re.compile(r"\b(gear|tactical|optics|defen[cs]e)\b", re.I)
_KEEP_BRANDWORDS_EN = re.compile(r"(?<=\w )(Gear|GEAR|Tactical|TACTICAL|Optics|OPTICS|Defen[cs]e|DEFEN[CS]E)\b")
_GLOSS = sorted(GLOSSARY.items(), key=lambda kv: -len(kv[0]))
_GLOSS_RX = re.compile(r"(?<![\w&])(" + "|".join(re.escape(k) for k, _ in _GLOSS) + r")(?![\w&])", re.I)

# English airsoft terms -> target language, for the second step (the models read "magazine" as a
# journal, "barrel" as a keg, "stock" as a warehouse).
GLOSSARY_OUT = {
    "sk": {
        "magazine": "zásobník", "magazines": "zásobníky", "drum magazine": "bubnový zásobník",
        "hi-cap magazine": "hi-cap zásobník", "mid-cap magazine": "mid-cap zásobník", "magazine pouch": "zásobníková sumka",
        "magazine catch": "záchyt zásobníka", "magazine base plate": "pätka zásobníka", "base plate": "pätka",
        "barrel": "hlaveň", "inner barrel": "vnútorná hlaveň", "precision barrel": "presná hlaveň",
        "bolt": "záver", "bolt catch": "záchyt záveru", "metal bolt": "kovový záver", "catch": "záchyt",
        "stock": "pažba", "folding stock": "sklopná pažba", "retractable stock": "výsuvná pažba",
        "handguard": "predpažbie", "grip": "rukoväť", "trigger": "spúšť", "trigger guard": "lučík",
        "sight": "mieridlo", "sights": "mieridlá", "front sight": "predné mieridlo", "rear sight": "zadné mieridlo",
        "scope": "puškohľad", "scopes": "puškohľady",
        "mount": "montáž", "rail": "lišta", "rails": "lišty", "suppressor": "tlmič", "silencer": "tlmič",
        "piston": "piest", "piston head": "hlava piestu", "cylinder": "valec", "cylinder head": "hlava valca",
        "nozzle": "tryska", "nozzles": "trysky", "loading nozzle": "nabíjacia tryska", "gearbox": "mechabox",
        "gear set": "sada ozubených kolies", "gears": "ozubené kolesá", "gear": "ozubené koleso",
        "spring": "pružina", "springs": "pružiny", "bucking": "gumička", "buckings": "gumičky",
        "hop-up bucking": "hop-up gumička", "hop-up chamber": "hop-up komora", "selector": "prepínač",
        "shooting mode": "režim streľby", "fire selector": "prepínač režimu streľby", "magwell": "magwell",
        "pouch": "sumka", "pouches": "sumky", "dump pouch": "odhadzovák", "plate carrier": "nosič plátov",
        "chest rig": "chest rig", "vest": "vesta", "tactical vest": "taktická vesta", "belt": "opasok",
        "sling": "popruh", "holster": "puzdro", "battery": "batéria", "charger": "nabíjačka",
        "goggles": "okuliare", "safety goggles": "ochranné okuliare", "glasses": "okuliare", "mask": "maska",
        "helmet": "prilba", "gloves": "rukavice", "trousers": "nohavice", "jacket": "bunda", "shirt": "košeľa",
        "patch": "nášivka", "balaclava": "kukla", "knee pads": "chrániče kolien",
        "sniper rifle": "odstreľovacia puška", "submachine gun": "samopal", "assault rifle": "útočná puška",
        "airsoft gun": "airsoftová zbraň", "airsoft submachine gun": "airsoftový samopal", "airsoft rifle": "airsoftová puška", "airsoft pistol": "airsoftová pištoľ",
        "electric pistol": "elektrická pištoľ", "gas pistol": "plynová pištoľ", "pistol": "pištoľ", "pistols": "pištole",
        "rifle": "puška", "shotgun": "brokovnica", "machine gun": "guľomet", "weapons": "zbrane", "weapon": "zbraň",
        "full metal": "celokov", "full auto": "dávka", "blowback": "blowback", "rounds": "nábojov",
        "BBs": "guličky", "gas": "plyn", "bipod": "dvojnožka", "cheek rest": "lícnica",
        "imitation wood": "imitácia dreva", "real wood": "pravé drevo", "wood": "drevo",
        "spare part": "náhradný diel", "part": "diel", "parts": "diely", "flashlight": "baterka",
        "tactical flashlight": "taktická baterka", "radio": "vysielačka", "grenade": "granát",
        "black": "čierna", "tan": "piesková", "olive": "olivová", "grey": "sivá", "white": "biela", "green": "zelená",
        "brown": "hnedá", "red": "červená", "blue": "modrá", "camo": "maskáčová", "camouflage": "maskovací",
        "different lengths": "rôzne dĺžky", "choose length": "zvoľte dĺžku", "steel": "oceľový",
    },
    "de": {
        "magazine": "Magazin", "magazines": "Magazine", "drum magazine": "Trommelmagazin",
        "magazine pouch": "Magazintasche", "barrel": "Lauf", "inner barrel": "Innenlauf",
        "precision barrel": "Präzisionslauf", "bolt": "Verschluss", "metal bolt": "Metallverschluss",
        "stock": "Schaft", "folding stock": "Klappschaft", "retractable stock": "Teleskopschaft",
        "trigger": "Abzug", "trigger guard": "Abzugsbügel", "front sight": "Korn", "rear sight": "Kimme",
        "red dot": "Red Dot", "scope": "Zielfernrohr", "mount": "Montage", "suppressor": "Schalldämpfer",
        "piston": "Kolben", "cylinder": "Zylinder", "nozzle": "Düse", "gearbox": "Gearbox",
        "gear set": "Zahnradsatz", "gears": "Zahnräder", "spring": "Feder", "springs": "Federn",
        "bucking": "Hop-Up-Gummi", "hop-up bucking": "Hop-Up-Gummi", "pouch": "Tasche",
        "plate carrier": "Plattenträger", "sling": "Trageriemen", "holster": "Holster", "helmet": "Helm",
        "goggles": "Schutzbrille", "gloves": "Handschuhe", "airsoft gun": "Airsoft-Waffe",
        "airsoft pistol": "Airsoft-Pistole", "airsoft rifle": "Airsoft-Gewehr", "full metal": "Vollmetall",
        "ball bearings": "Kugellager", "BBs": "BBs",
    },
}
_GLOSS_OUT_RX = {
    lang: re.compile(r"(?<![\w&-])(" + "|".join(re.escape(k) for k in sorted(g, key=len, reverse=True)) + r")(?![\w&-])", re.I)
    for lang, g in GLOSSARY_OUT.items()}
_GLOSS_OUT = {lang: {k.lower(): v for k, v in g.items()} for lang, g in GLOSSARY_OUT.items()}
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

    def lock(self, text: str, use_glossary: bool, lang: str | None = None) -> tuple[str, list[str]]:
        """use_glossary: Czech airsoft terms (first step). lang: target-language terms (second step)."""
        kept: list[str] = []

        def keep(value: str) -> str:
            kept.append(value)
            return f" X{len(kept) - 1}X "
        # "černá/stříbrná" is two words to translate, not a model code like "M4/AR15"
        text = re.sub(r"\b([^\W\d_]{3,})/([^\W\d_]{3,})\b",
                      lambda m: m.group(0) if m.group(0) != m.group(0).lower() else f"{m.group(1)} / {m.group(2)}", text)
        text = _PROTECT.sub(lambda m: keep(m.group(0)), text)
        text = _KEEP.sub(lambda m: keep(m.group(0)), text)
        text = (_KEEP_BRANDWORDS if use_glossary else _KEEP_BRANDWORDS_EN).sub(lambda m: keep(m.group(0)), text)
        if self.brands:
            text = self.brands.sub(lambda m: keep(m.group(0)), text)
        if use_glossary:
            text = _GLOSS_RX.sub(lambda m: keep(GLOSSARY[m.group(1).lower()]), text)
        if lang in _GLOSS_OUT_RX:
            text = _GLOSS_OUT_RX[lang].sub(lambda m: keep(_GLOSS_OUT[lang][m.group(1).lower()]), text)
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
    """Translate names that lack a current translation in some language, most-compared first."""
    settings = cfg["settings"]
    conn = dbmod.connect(settings["database"])
    conn.execute("CREATE TABLE IF NOT EXISTS translations (src TEXT, lang TEXT, text TEXT, PRIMARY KEY (src, lang))")
    if "v" not in {r[1] for r in conn.execute("PRAGMA table_info(translations)")}:
        conn.execute("ALTER TABLE translations ADD COLUMN v INTEGER NOT NULL DEFAULT 1")
    deadline = time.time() + max_minutes * 60 if max_minutes is not None else None

    names = [r[0] for r in conn.execute(
        "SELECT p.title FROM products p ORDER BY p.shop_count DESC, p.in_stock_count DESC")]
    names += [r[0] for r in conn.execute(
        "SELECT o.title FROM offers o JOIN products p ON p.id = o.product_id ORDER BY p.shop_count DESC")]
    current: dict[str, set[str]] = {}
    for src, lang in conn.execute("SELECT src, lang FROM translations WHERE v >= ?", (VERSION,)):
        current.setdefault(src, set()).add(lang)
    names = list(dict.fromkeys(names))
    todo = [n for n in names if current.get(n, set()) != set(LANGS)]
    log.info("Translations: %d names up to date, %d to do", len(names) - len(todo), len(todo))
    if not todo:
        return

    mdir = models_dir(settings)
    cs_en = _Model(_download("cs_en", MODELS["cs_en"], mdir), "cs", "en")
    targets = {lang: _Model(_download(f"en_{lang}", MODELS[f"en_{lang}"], mdir), "en", lang)
               for lang in LANGS if lang != "en"}
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
        rows = [(s, "en", e, VERSION) for s, e in zip(batch, en)]
        for lang, model in targets.items():
            tgt_in = [locker.lock(t, use_glossary=False, lang=lang) for t in en]
            out = [locker.unlock(t, kept) for t, (_, kept) in zip(model([p for p, _ in tgt_in]), tgt_in)]
            rows += [(s, lang, t, VERSION) for s, t in zip(batch, out)]
        with conn:
            conn.executemany("INSERT OR REPLACE INTO translations (src, lang, text, v) VALUES (?, ?, ?, ?)", rows)
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
