"""Keyword-based product categorisation (Czech, Slovak and English keywords).

A product name says what it is in its *head*: the words before "pro / na / s / for / with",
a dash or a comma. "Sumka na zásobník" is a pouch, "Zásobník pro M4, 150 BB" a magazine,
"Pistolové pouzdro" a holster. So the categoriser looks at the head first and takes the
earliest product word in it; when that word is directly followed by another product word
("magazine pouch", "nabíjecí tryska") the second one is the noun and wins.

Gun model names (M4, Glock, VSR…) and loose hints (BB, CO2) are *weak*: they only decide when
no product word is found, because they also appear in names of parts and accessories.
"""
from __future__ import annotations

import re

from .text import strip_accents

# slug, label, icon, regex of product words (applied to lowercase text without diacritics).
# Order breaks ties between rules matching at the same place.
RULES: list[tuple[str, str, str, str]] = [
    ("bbs", "BBs", "⚪", r"\b(kulic\w*|gulick\w*|bio ?bbs?|tracer ?bbs?|bbs? \d[.,]\d+ ?g|\d[.,]\d+ ?g bbs?)\b"),
    ("gas", "Gas & CO2", "🧯", r"\b(gas|plyn\w*|propan\w*)\b(?=.*\b\d+ ?ml\b)|\bco2 ?(bombick\w*|capsul\w*|cartridg\w*|nabo\w*)|\bbombick\w*|\bplynov\w* lahe?v\w*"),
    ("holsters", "Holsters", "🪢", r"\b(holster\w*|(pistolov|stehenn|podpazn|serpa)\w* pouzdr\w*|pouzdr\w* (na|pro) (pistol|revolver)\w*)"),
    ("pouches", "Pouches & bags", "👝", r"\b(opas\w*|belt\w*|sumk\w*|pouch\w*|batoh\w*|backpack\w*|kufr\w*|case|spacak\w*|ruksak\w*|brasn\w*|bag|bags|kaps\w*|dump ?pouch|admin panel|pouzdr\w*|obal|obalu|vak|vaku|tas[ek]\w*|ledvink\w*|organiz\w*|ammo bucket|odhazov\w*|karabin[ay]|karabinou)\b"),
    ("chargers", "Chargers", "🔌", r"\b(nabij[ae]c(k\w*)?|charger\w*|nabijeci (adapter|kabel|stanic|zdroj)\w*)\b"),
    ("batteries", "Batteries", "🔋", r"\b(bateri\w*|akumulator\w*|batter\w*|lipo|li-?po[ln]?|nimh|li-?ion|li-?fe|cr123\w*)\b"),
    ("magazines", "Magazines", "📦", r"\b(zasobn\w*|magazin\w*|magazine\w*|mags?|hi-?cap|mid-?cap|low-?cap|real-?cap|drum|patron[ay]?)\b"),
    ("optics", "Optics & red dots", "🎯", r"\b(red ?dot\w*|kolimator\w*|holo\w*|holografick\w*|puskohl[ae]d\w*|scope\w*|magnifier\w*|zvetsovac\w*|optik\w*|optic\w*|reflex sight)\b"),
    ("eyewear", "Goggles & glasses", "🥽", r"\b(bryl\w*|okuliar\w*|goggle\w*|glasses|eyewear|eye protection)\b"),
    ("masks", "Masks", "😷", r"\b(mask(?!ov|ac)\w*|mesh|obliceje|face ?(guard|protect\w*)|faceprotect\w*|lower face)\b"),
    ("helmets", "Helmets", "⛑️", r"\b(helm\w*|prilb\w*|prilba)\b"),
    ("vests", "Vests & plate carriers", "🦺", r"\b(vest\w*|nosic\w*|plate ?carrier\w*|chest ?rig\w*|hrudnik\w*|jpc|avs)\b"),
    ("gloves", "Gloves", "🧤", r"\b(rukavic\w*|glove\w*)\b"),
    ("slings", "Slings", "➰", r"\b(popruh\w*|sling\w*|remen\w*)\b"),
    ("lights", "Lights & lasers", "🔦", r"\b(svitiln\w*|flashlight\w*|weapon ?light|laser\w*|peq|baterk\w*|lucern\w*|celovk\w*|svetl[oa]|svetlem)\b"),
    ("comms", "Radios & headsets", "📻", r"\b(vysilac\w*|radio\w*|headset\w*|sluchatk\w*|ptt|pmr|radiostanic\w*|nahlavn\w* soupra\w*|chranic\w* sluchu)\b"),
    ("parts", "Parts & upgrades", "⚙️", r"\b(hop-?up\w*|gumic\w*|telo|tela|zapadk\w*|miridl\w*|iron ?sight\w*|pist|pistu|pistem|pisty|pazb\w*|predpazb\w*|rukojet\w*|grip\w*|krytk\w*|spoust\w*|dorazec\w*|vack\w*|adapter\w*|podavac\w*|natahovac\w*|ramink\w*|upgrade\w*|ris|rail\w*|lista|listy|lisht\w*|montaz\w*|mount\w*|kabelaz\w*|wiring|stock|handguard|tlumic\w*|suppressor\w*|silencer\w*|flash ?hider\w*|kompenzator\w*|bipod\w*|dvojnoz\w*|udrzb\w*|cistic\w*|cisteni|sprej\w*|olej\w*|silikon\w*|lube|valec\w*|valc\w*|cylinder\w*|dil|dilu|dily|dilem|nahradn\w*|kulis\w*|prepinac\w*|selector\w*|lozisk\w*|bearing\w*|bushing\w*|gearbox\w*|mechabox\w*|piest\w*|piston\w*|pruzin\w*|spring\w*|hlav\w*|barrel\w*|motor\w*|mosfet\w*|gumick\w*|bucking\w*|nozzle\w*|tryska|trysk[yau]\w*|cylind\w*|ozuben\w*|gears?|valve\w*|ventil\w*|tappet\w*|trigger\w*|nub|o-?ring\w*|o-?krouz\w*|krouz\w*|tesnen\w*|gate|hpa engine|polarstar|zaver\w*|zachyt\w*|patk[ay]\w*|usti|klapk\w*|trn|buffer ?tube|cover|magwell|svetlovodn\w*|srouby|sroub\w*|charging handle|handle\w*|musk[ay]|cep|cepy|udernik\w*|licnic\w*)\b"),
    ("grenades", "Grenades & pyro", "💥", r"\b(granat\w*|grenade\w*|min[ay]|pyro\w*|dymovnic\w*|smoke)\b"),
    ("clothing", "Clothing & boots", "👕", r"\b(nasivk\w*|patch\w*|velcro|morale|kalhot\w*|bluz\w*|uniform\w*|kosil\w*|combat ?(shirt|pants)|pants|jacket\w*|bund\w*|cepic\w*|cap|boot\w*|boty|obuv\w*|ghillie|kuklic\w*|kukl[ay]|balaclava|nakolen\w*|naloketn\w*|knee ?pads?|chranic\w* (kolen|loktu)|mikin\w*|hoodie|satek|satk[ayu]|shemag\w*|klobouk\w*|ksiltovk\w*|trick[oa]|triko|t-?shirt|shirt|spodk\w*|ponozk\w*|kombinez\w*|natelnik\w*|brigadyrk\w*|hejkal\w*|oblek\w*)\b"),
    ("pistols", "Pistols & revolvers", "🔫", r"\b(pistol\w*|revolver\w*)\b"),
    ("snipers", "Sniper rifles", "🎯", r"\b(sniper\w*|odstrelov\w*|bolt ?action)\b"),
    ("shotguns", "Shotguns", "💨", r"\b(brokovnic\w*|shotgun\w*)\b"),
    # Not airsoft, but sold by the same shops; named so a gun model in the name can't claim them.
    ("other", "Other", "🧩", r"\b(nuz|noze|nozem|katan\w*|maceta|macet\w*|kus[ei]|luk|luky|lukem|sipk\w*|terc\w*|"
                            r"vzduchovk\w*|diabolk\w*|diabolo|paracord|karimatk\w*|sekyr\w*|tetiv\w*)\b"),
    ("guns", "Rifles & SMGs", "🪖", r"\b(kulomet\w*|machine ?gun\w*|zbran\w*|samopal\w*|smg|pusk[ayu]|puskou|rifle\w*|carbine\w*)\b"),
]

# Weak hints, used only when the name has no product word: gun models also name their parts.
WEAK: list[tuple[str, str]] = [
    ("pistols", r"\b(glock\w*|g17|hi-?capa|m?1911\w*|desert ?eagle|usp|p226|beretta|m9a?1?|m92\w*|cz ?75\w*|cz ?p-?(0[79]|10)\w*|aep)\b"),
    ("snipers", r"\b(vsr\w*|l96\w*|m24|m40\w*|srs|ssg\d*|mb\d{2,}\w*|svd|mosin\w*|kar ?98\w*)\b"),
    ("shotguns", r"\b(m870|m3 ?super|super 90|spas\w*|aa-?12)\b"),
    ("guns", r"\b(lmg|cm\.?\d{3}\w*|arp ?\d+\w*|gbb|m4\w*|m16\w*|ak-?\d*\w*|mp5\w*|g36\w*|scar\w*|hk416|416|ump\w*|vss|aug|famas|fa-mas|p90|mp7\w*|g3\w*|pdw)\b"),
    ("helmets", r"\b(fast|mich)\b"),
    ("guns", r"\b(aeg|gbbr|karabin\w*)\b"),
    ("bbs", r"\b(bbs?)\b(?! ?proof)"),
    ("gas", r"\b(green ?gas|red ?gas|top ?gas|black ?gas|co2)\b"),
]

CATEGORIES = {slug: (label, icon) for slug, label, icon, _ in RULES if slug != "other"}
CATEGORIES["other"] = ("Other", "🧩")

# Top-level groups shown in the menu; each opens into its subcategories.
GROUPS: dict[str, tuple[str, str, list[str]]] = {
    "weapons": ("Guns", "🔫", ["guns", "pistols", "snipers", "shotguns"]),
    "ammo": ("Magazines, BBs & gas", "📦", ["magazines", "bbs", "gas"]),
    "sights": ("Optics & lights", "🔭", ["optics", "lights"]),
    "upgrades": ("Parts & accessories", "⚙️", ["parts", "batteries", "chargers"]),
    "gear": ("Tactical gear", "🦺", ["vests", "pouches", "holsters", "slings"]),
    "protection": ("Protection", "🥽", ["masks", "eyewear", "helmets", "gloves"]),
    "apparel": ("Clothing & boots", "👕", ["clothing"]),
    "misc": ("Other", "🧩", ["comms", "grenades", "other"]),
}
GROUP_OF = {sub: g for g, (_, _, subs) in GROUPS.items() for sub in subs}

_COMPILED = [(slug, re.compile(rx)) for slug, _, _, rx in RULES]
_WEAK = [(slug, re.compile(rx)) for slug, rx in WEAK]
GUN_TYPES = {"guns", "pistols", "snipers", "shotguns"}
# Where the head of a name ends: a preposition, a dash, a plus, a comma or a bracket.
_HEAD_END = re.compile(r"\s(pro|pre|na|k|ke|do|s|se|z|ze|od|for|with|to|fits?|incl\w*|vcetne|w/)\s|\s[-–+|/]\s|,\s|\(")
# Czech adjective endings (accents stripped): "zásobníková", "nabíjecí", "bateriového".
_ADJ = re.compile(r"\w+(ov(y|a|e|i|eho|emu|ych|ym|ymi|ou)|n(i|iho|imu|ich|im|imi)|sk(y|e|eho|ych|ym|ou)"
                  r"|ck(y|e|eho|ych|ym|ou)|ci(ho|mu|ch|m|mi)?)")
# Words that describe rather than name the product; like adjectives, they give way to a later noun.
_MODIFIER = re.compile(r"li-?po[ln]?|lipo|nimh|li-?ion|li-?fe|holo\w*|laser\w*")
_CZECH = re.compile(r"[áčďéěíňóřšťúůýžľĺŕô]")
_HOLSTER_HINT = re.compile(r"\b(pistol\w*|revolver\w*|serpa|safariland|blackhawk|glock\w*|sig|p226|p320|1911|"
                           r"cz ?75|p-?0[79]|p-?10|beretta|m9|m92\w*|usp|walther|p99|hi-?capa)\b")


def _norm(text: str) -> str:
    return " " + re.sub(r"\s+", " ", strip_accents(text.lower())).strip() + " "


def _takes_over(old: str, new: str) -> bool:
    """A gun type never takes over from another category ("Boty Sniper Pro" are boots)."""
    return new not in GUN_TYPES


def _strong(t: str, czech: bool) -> str | None:
    """The product noun among the product words of a name.

    Czech puts the noun first ("Krytka bateriového prostoru"), so the earliest word wins unless it
    is an adjective ("Zásobníková sumka", "Nabíjecí tryska"); then the next product noun does.
    English puts it last ("Magazine pouch", "Battery cover"): a product word directly after the
    chosen one takes over.
    """
    hits = sorted((m.start(), order, m.end(), slug)
                  for order, (slug, rx) in enumerate(_COMPILED) for m in rx.finditer(t))
    if not hits:
        return None
    first = hits[0]
    if czech:
        if _ADJ.fullmatch(t[first[0]:first[2]]) or _MODIFIER.fullmatch(t[first[0]:first[2]]):
            later = [h for h in hits if h[0] > first[0] and h[3] != first[3]
                     and not _ADJ.fullmatch(t[h[0]:h[2]]) and _takes_over(first[3], h[3])]
            if later:
                return later[0][3]
        return first[3]
    _, _, end, slug = first
    while True:
        nxt = [h for h in hits if h[0] == end + 1 and h[3] != slug and _takes_over(slug, h[3])]
        if not nxt:
            return slug
        _, _, end, slug = nxt[0]


def _weak(t: str) -> str | None:
    hits = sorted((m.start(), i, slug) for i, (slug, rx) in enumerate(_WEAK) for m in [rx.search(t)] if m)
    return hits[0][2] if hits else None


def _classify(text: str) -> tuple[str | None, bool]:
    """(category, sure). Sure = a product word in the head of the name."""
    t = _norm(text)
    czech = bool(_CZECH.search(text.lower()))
    cut = _HEAD_END.search(t, 1)
    head = t[:cut.start() + 1] + " " if cut else t
    found = _strong(head, czech)
    sure = found is not None
    if not found:
        found = _weak(head) or _strong(t, czech) or _weak(t)
    if found == "pouches" and re.search(r"\bpouzdr", t) and _HOLSTER_HINT.search(t):
        found = "holsters"  # "Pouzdro Blackhawk SERPA pro Glock 17"
    return found, sure


def _match(text: str) -> str | None:
    return _classify(text)[0]


def _match_path(shop_category: str) -> str | None:
    """Category from the shop's own path, most specific part first. A gun type only counts in
    the last part: "Airsoft guns | Maintenance" is about maintenance, not guns."""
    parts = [p for p in re.split(r"\s*[|>/»]\s*", shop_category) if p]
    for i, part in enumerate(reversed(parts)):
        found = _match(part)
        if found and (found not in GUN_TYPES or i == 0):
            return found
    return None


def categorize(title: str, shop_category: str | None = None) -> str:
    """The product name decides when it names the product; otherwise the shop's own category
    path is asked before loose hints like a gun model or "CO2"."""
    found, sure = _classify(title)
    if sure:
        return found
    shop_says = _match_path(shop_category) if shop_category else None
    if shop_says and (not found or found in GUN_TYPES | {"gas", "bbs"} or shop_says not in GUN_TYPES):
        return shop_says
    return found or "other"
