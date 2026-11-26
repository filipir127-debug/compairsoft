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
    ("pouches", "Pouches", "👝", r"\b(sumk\w*|pouch\w*|kaps\w*|dump ?pouch|admin panel)\b"),
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
    ("parts", "Parts & upgrades", "⚙️", r"\b(hop-?up\w*|kulis\w*|prepinac\w*|selector\w*|lozisk\w*|bearing\w*|bushing\w*|gearbox\w*|mechabox\w*|piest\w*|piston\w*|pruzin\w*|spring\w*|hlav\w*|barrel\w*|motor\w*|mosfet\w*|gumick\w*|bucking\w*|nozzle\w*|tryska\w*|cylind\w*|ozuben\w*|gears?|valve\w*|ventil\w*|tappet\w*|trigger ?unit|nub|o-?ring\w*|gate|titan|hpa engine|polarstar)\b"),
    ("grenades", "Grenades & pyro", "💥", r"\b(granat\w*|grenade\w*|min[ay]|pyro\w*|dymovnic\w*|smoke)\b"),
    ("clothing", "Clothing & boots", "👕", r"\b(kalhot\w*|bluz\w*|uniform\w*|kosil\w*|combat ?(shirt|pants)|pants|jacket\w*|bund\w*|cepic\w*|cap|boot\w*|boty|obuv\w*|ghillie|kuklic\w*|balaclava|nakolenik\w*|knee ?pads?)\b"),
    ("guns", "Guns", "🔫", r"\b(zbran\w*|pistol\w*|revolver\w*|samopal\w*|smg|pusk\w*|pusk[ay]|rifle\w*|carbine\w*|karabin\w*|sniper\w*|odstrelov\w*|brokovnic\w*|shotgun\w*|aeg|gbb|gbbr|aep|m4|m16|ak-?\d+|mp5|g36|scar|hk416|ump|vss|l96|vsr|glock|g17|1911|hi-?capa)\b"),
    ("gas", "Gas & CO2", "🧯", r"\b(green ?gas|red ?gas|top ?gas|black ?gas|co2)\b"),
]

CATEGORIES = {slug: (label, icon) for slug, label, icon, _ in RULES}
CATEGORIES["other"] = ("Other", "🧩")

_COMPILED = [(slug, re.compile(rx)) for slug, _, _, rx in RULES]


def _match(text: str) -> str | None:
    t = strip_accents(text.lower())
    for slug, rx in _COMPILED:
        if rx.search(t):
            return slug
    return None


def categorize(title: str, shop_category: str | None = None) -> str:
    """Use the product title first; fall back to the shop's own category path."""
    found = _match(title)
    if found:
        return found
    if shop_category:
        # Look at the most specific part of the path first ("Zbraně | Pistole | GBB")
        for part in reversed(re.split(r"\s*[|>/»]\s*", shop_category)):
            found = _match(part)
            if found:
                return found
    return "other"
