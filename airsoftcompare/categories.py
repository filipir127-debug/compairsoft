"""Keyword-based product categorisation (Czech, Slovak and English keywords).

Order matters: the first matching rule wins, so e.g. "sumka na zásobník"
(magazine pouch) is caught by *pouches* before *magazines*, and "M4 gearbox"
by *parts* before *guns*.  Add your own keywords freely.
"""
from __future__ import annotations

import re

from .text import strip_accents

# slug, label, icon, regex (applied to lowercase text without diacritics)
RULES: list[tuple[str, str, str, str]] = [
    ("bbs", "BBs", "⚪", r"^(?!.*\b(lozisk\w*|bearing\w*)).*\b(kulic\w*|gulick\w*|bbs?|bio ?bbs?|tracer bbs?)\b"),
    # Gas *products* (a can with a volume, CO2 capsules) – gun titles often say "green gas" too.
    ("gas", "Gas & CO2", "🧯", r"\b(gas|plyn\w*|propan\w*)\b.*\b\d+ ?ml\b|\b\d+ ?ml\b.*\b(gas|plyn\w*)\b|\bco2 ?(bombick\w*|capsul\w*|cartridg\w*|nabo\w*)|\bbombick\w*"),
    ("pouches", "Pouches & bags", "👝", r"\b(opas\w*|belt\w*|sumk\w*|pouch\w*|batoh\w*|backpack\w*|kufr\w*|case|spacak\w*|ruksak\w*|brasn\w*|bag|bags|kaps\w*|dump ?pouch|admin panel)\b"),
    ("chargers", "Chargers", "🔌", r"\b(nabij\w*|charger\w*)\b"),
    ("batteries", "Batteries", "🔋", r"\b(bateri\w*|akumulator\w*|batter\w*|lipo|li-?po|nimh|li-?ion|li-?fe)\b"),
    ("magazines", "Magazines", "📦", r"\b(zasobn\w*|magazin\w*|magazine\w*|mags?|hi-?cap|mid-?cap|low-?cap|real-?cap|drum)\b"),
    ("optics", "Optics & red dots", "🎯", r"\b(red ?dot\w*|kolimator\w*|holo\w*|holografick\w*|puskohled\w*|scope\w*|magnifier\w*|zvetsovac\w*|optik\w*|optic\w*|reflex sight)\b"),
    ("eyewear", "Goggles & glasses", "🥽", r"\b(bryl\w*|okuliar\w*|goggle\w*|glasses|eyewear|eye protection)\b"),
    ("masks", "Masks", "😷", r"\b(mask\w*|mesh|obliceje|face ?(guard|protect\w*)|lower face)\b"),
    ("helmets", "Helmets", "⛑️", r"\b(helm\w*|prilb\w*|prilba|fast|mich)\b"),
    ("vests", "Vests & plate carriers", "🦺", r"\b(vest\w*|nosic\w*|plate ?carrier\w*|chest ?rig\w*|hrudnik\w*|jpc|avs)\b"),
    ("gloves", "Gloves", "🧤", r"\b(rukavic\w*|glove\w*)\b"),
    ("holsters", "Holsters", "🪢", r"\b(pouzdr\w*|holster\w*)\b"),
    ("slings", "Slings", "➰", r"\b(popruh\w*|sling\w*|remen\w*)\b"),
    ("lights", "Lights & lasers", "🔦", r"\b(svitiln\w*|flashlight\w*|weapon ?light|laser\w*|peq|baterk\w*)\b"),
    ("comms", "Radios & headsets", "📻", r"\b(vysilac\w*|radio\w*|headset\w*|sluchatk\w*|ptt)\b"),
    ("parts", "Parts & upgrades", "⚙️", r"\b(hop-?up\w*|gumic\w*|telo|tela|zapadk\w*|miridl\w*|iron ?sight\w*|pist|pistu|pistem|pisty|pazb\w*|predpazb\w*|rukojet\w*|grip\w*|krytk\w*|spoust\w*|dorazec\w*|vack\w*|adapter\w*|podavac\w*|natahovac\w*|ramink\w*|upgrade\w*|ris|rail\w*|lista|listy|lisht\w*|montaz\w*|mount\w*|kabelaz\w*|wiring|stock|handguard|tlumic\w*|suppressor\w*|silencer\w*|flash ?hider\w*|kompenzator\w*|bipod\w*|dvojnoz\w*|udrzb\w*|cistic\w*|cisteni|sprej\w*|olej\w*|silikon\w*|lube|valec\w*|valc\w*|cylinder\w*|dil|dilem|nahradn\w*|kulis\w*|prepinac\w*|selector\w*|lozisk\w*|bearing\w*|bushing\w*|gearbox\w*|mechabox\w*|piest\w*|piston\w*|pruzin\w*|spring\w*|hlav\w*|barrel\w*|motor\w*|mosfet\w*|gumick\w*|bucking\w*|nozzle\w*|tryska\w*|cylind\w*|ozuben\w*|gears?|valve\w*|ventil\w*|tappet\w*|trigger ?unit|nub|o-?ring\w*|gate|titan|hpa engine|polarstar)\b"),
    ("grenades", "Grenades & pyro", "💥", r"\b(granat\w*|grenade\w*|min[ay]|pyro\w*|dymovnic\w*|smoke)\b"),
    ("clothing", "Clothing & boots", "👕", r"\b(nasivk\w*|patch\w*|velcro|morale|kalhot\w*|bluz\w*|uniform\w*|kosil\w*|combat ?(shirt|pants)|pants|jacket\w*|bund\w*|cepic\w*|cap|boot\w*|boty|obuv\w*|ghillie|kuklic\w*|balaclava|nakolenik\w*|knee ?pads?)\b"),
    ("pistols", "Pistols & revolvers", "🔫", r"\b(pistol\w*|revolver\w*|glock\w*|hi-?capa|m?1911\w*|desert ?eagle|usp|p226|beretta|m9a?1?|cz ?75\w*|cz ?p-?0[79]|p-?0[79]|aep)\b"),
    ("snipers", "Sniper rifles", "🎯", r"\b(sniper\w*|odstrelov\w*|bolt ?action|vsr\w*|l96\w*|m24|m40|srs|ssg\d*|mb\d{2,})\b"),
    ("shotguns", "Shotguns", "💨", r"\b(brokovnic\w*|shotgun\w*|m870|m3 ?super)\b"),
    ("guns", "Rifles & SMGs", "🪖", r"\b(kulomet\w*|machine ?gun\w*|lmg|cm\d{2}\w*|arp ?\d+\w*|zbran\w*|pistol\w*|revolver\w*|samopal\w*|smg|pusk\w*|pusk[ay]|rifle\w*|carbine\w*|karabin\w*|sniper\w*|odstrelov\w*|brokovnic\w*|shotgun\w*|aeg|gbb|gbbr|aep|m4|m16|ak-?\d+|mp5|g36|scar|hk416|ump|vss|l96|vsr|glock|g17|1911|hi-?capa)\b"),
    ("gas", "Gas & CO2", "🧯", r"\b(green ?gas|red ?gas|top ?gas|black ?gas|co2)\b"),
]

CATEGORIES = {slug: (label, icon) for slug, label, icon, _ in RULES}
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


def _match(text: str) -> str | None:
    t = strip_accents(text.lower())
    for slug, rx in _COMPILED:
        if rx.search(t):
            return slug
    return None


GUN_TYPES = {"guns", "pistols", "snipers", "shotguns"}


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
    """Use the product title first; fall back to the shop's own category path."""
    found = _match(title)
    if found in GUN_TYPES and shop_category:
        # "M4" or "AK" in a title also names parts for that gun; trust the shop if it files it elsewhere.
        shop_says = _match_path(shop_category)
        if shop_says and shop_says not in GUN_TYPES:
            return shop_says
    if found:
        return found
    return (_match_path(shop_category) if shop_category else None) or "other"
