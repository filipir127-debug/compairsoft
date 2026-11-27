"""Product parameters for the filters, read from product names.

Shops only give us a name, a price and a photo, so every parameter here is found in the name
("Li-Pol akumulátor 11,1V 1300mAh 20C - Mini Tamiya" -> chemistry, voltage, capacity, C rating,
connector, shape). A product without a value is simply not counted for that parameter.

Each category lists its parameters; the ones marked basic show in the sidebar, all of them in the
"All parameters" window, grouped into tabs (SECTIONS). Kinds:
  enum  - checkboxes; a product can have several values (an RPK is an AK and a machine gun)
  bool  - one checkbox ("Blowback", "MOLLE")
  range - a slider between the lowest and highest value found ("Capacity 1000-5000 mAh")
"""
from __future__ import annotations

import re

from .text import strip_accents


def L(en: str, cs: str | None = None, sk: str | None = None, de: str | None = None) -> list[str]:
    """Labels in the site's order of languages: en, cs, sk, de."""
    return [en, cs or en, sk or cs or en, de or en]


SECTIONS = {
    "basic": L("Basic", "Základní", "Základné", "Allgemein"),
    "power": L("Power & performance", "Pohon a výkon", "Pohon a výkon", "Antrieb & Leistung"),
    "build": L("Build", "Provedení", "Prevedenie", "Ausführung"),
    "compat": L("Compatibility", "Kompatibilita", "Kompatibilita", "Kompatibilität"),
    "size": L("Size", "Velikost a rozměry", "Veľkosť a rozmery", "Größe & Maße"),
    "features": L("Features", "Výbava", "Výbava", "Ausstattung"),
    "look": L("Colour", "Barva a vzhled", "Farba a vzhľad", "Farbe & Optik"),
    "shops": L("Shops", "Obchody", "Obchody", "Shops"),
}

# ------------------------------------------------------------------ definitions
# id: dict(kind, label, sec, [url], [tag], [unit], [values], [vp]) - url and tag default to the id.
# vp: prefix of value labels already in app.js (pw.electric, col.black …); values: own labels.
P: dict[str, dict] = {
    # already tagged by export._attrs
    "power": dict(kind="enum", tag="pw", label=L("Power source", "Pohon", "Pohon", "Antrieb"), sec="power", vp="pw."),
    "platform": dict(kind="enum", tag="pl", url="plat", label=L("Platform", "Platforma", "Platforma", "Plattform"), sec="build", vp="pl."),
    "material": dict(kind="enum", tag="mt", label=L("Material", "Materiál", "Materiál", "Material"), sec="build", vp="mt."),
    "cap": dict(kind="enum", label=L("Magazine type", "Typ zásobníku", "Typ zásobníka", "Magazintyp"), sec="basic", vp="cap."),
    "bbw": dict(kind="enum", label=L("BB weight", "Gramáž kuliček", "Gramáž guličiek", "BB-Gewicht"), sec="basic", fmt="g"),
    "airgun": dict(kind="enum", tag="ag", url="ag", label=L("Airgun type", "Typ vzduchovky", "Typ vzduchovky", "Luftdruck-Art"), sec="basic", vp="ag."),
    "caliber": dict(kind="enum", tag="cal", url="cal", label=L("Calibre", "Ráže", "Kaliber", "Kaliber"), sec="build", fmt="mm"),
    "color": dict(kind="enum", tag="col", label=L("Colour", "Barva", "Farba", "Farbe"), sec="look", vp="col."),

    # numbers
    "mps": dict(kind="range", label=L("Muzzle velocity", "Úsťová rychlost", "Úsťová rýchlosť", "Mündungsgeschwindigkeit"), unit="m/s", sec="power"),
    "joule": dict(kind="range", label=L("Energy", "Energie", "Energia", "Energie"), unit="J", sec="power"),
    "inch": dict(kind="range", label=L("Barrel length", "Délka hlavně", "Dĺžka hlavne", "Lauflänge"), unit="″", sec="size"),
    "rounds": dict(kind="range", label=L("Capacity", "Kapacita", "Kapacita", "Kapazität"), unit="BB", sec="basic"),
    "bbcount": dict(kind="range", label=L("BBs in pack", "Počet kuliček", "Počet guličiek", "BBs pro Packung"), unit="ks", sec="size"),
    "ml": dict(kind="range", label=L("Volume", "Objem", "Objem", "Volumen"), unit="ml", sec="size"),
    "zoom": dict(kind="range", label=L("Magnification", "Zvětšení", "Zväčšenie", "Vergrößerung"), unit="×", sec="basic"),
    "obj": dict(kind="range", label=L("Objective lens", "Průměr objektivu", "Priemer objektívu", "Objektivdurchmesser"), unit="mm", sec="size"),
    "lm": dict(kind="range", label=L("Brightness", "Svítivost", "Svietivosť", "Helligkeit"), unit="lm", sec="power"),
    "volt": dict(kind="range", label=L("Voltage", "Napětí", "Napätie", "Spannung"), unit="V", sec="power"),
    "mah": dict(kind="range", label=L("Capacity", "Kapacita", "Kapacita", "Kapazität"), unit="mAh", sec="power"),
    "crate": dict(kind="range", label=L("Discharge rate", "Vybíjecí proud", "Vybíjací prúd", "Entladerate"), unit="C", sec="power"),
    "watt": dict(kind="range", label=L("Power", "Výkon", "Výkon", "Leistung"), unit="W", sec="power"),
    "blen": dict(kind="range", label=L("Barrel length", "Délka hlavně", "Dĺžka hlavne", "Lauflänge"), unit="mm", sec="size"),
    "spring": dict(kind="range", label=L("Spring strength", "Síla pružiny", "Sila pružiny", "Federstärke"), unit="M", sec="power"),
    "shore": dict(kind="range", label=L("Bucking hardness", "Tvrdost gumičky", "Tvrdosť gumičky", "Gummihärte"), unit="°", sec="build"),
    "litres": dict(kind="range", label=L("Volume", "Objem", "Objem", "Volumen"), unit="l", sec="size"),
    "shoe": dict(kind="range", label=L("Shoe size (EU)", "Velikost bot (EU)", "Veľkosť obuvi (EU)", "Schuhgröße (EU)"), unit="", sec="size"),
    "grams": dict(kind="range", label=L("Weight", "Hmotnost", "Hmotnosť", "Gewicht"), unit="g", sec="size"),
    "pcs": dict(kind="range", label=L("Pieces in pack", "Počet kusů v balení", "Počet kusov v balení", "Stück pro Packung"), unit="ks", sec="size"),
    "lbs": dict(kind="range", label=L("Draw weight", "Nátahová síla", "Náťahová sila", "Zuggewicht"), unit="lb", sec="power"),

    # yes / no
    "blowback": dict(kind="bool", label=L("Blowback", "Blowback (zpětný ráz)", "Blowback (spätný ráz)", "Blowback"), sec="features"),
    "licensed": dict(kind="bool", label=L("Official licence", "Oficiální licence", "Oficiálna licencia", "Offizielle Lizenz"), sec="features"),
    "bio": dict(kind="bool", label=L("Biodegradable", "Bio (rozložitelné)", "Bio (rozložiteľné)", "Bio (abbaubar)"), sec="basic"),
    "tracer": dict(kind="bool", label=L("Tracer", "Svítící (tracer)", "Svietiace (tracer)", "Leuchtspur"), sec="features"),
    "illum": dict(kind="bool", label=L("Illuminated reticle", "Podsvícený záměrný bod", "Podsvietený zameriavací bod", "Beleuchtetes Absehen"), sec="features"),
    "usb": dict(kind="bool", label=L("Rechargeable", "Nabíjecí", "Nabíjateľné", "Wiederaufladbar"), sec="features"),
    "smart": dict(kind="bool", label=L("Smart / balancing", "Inteligentní / balancer", "Inteligentná / balancer", "Intelligent / Balancer"), sec="basic"),
    "molle": dict(kind="bool", label=L("MOLLE", "MOLLE", "MOLLE", "MOLLE"), sec="features"),
    "bungee": dict(kind="bool", label=L("Bungee (elastic)", "Pružný (bungee)", "Pružný (bungee)", "Elastisch (Bungee)"), sec="features"),
    "padded": dict(kind="bool", label=L("Padded", "Polstrovaný", "Polstrovaný", "Gepolstert"), sec="features"),
    "earpro": dict(kind="bool", label=L("Ear protection", "Ochrana uší", "Ochrana uší", "Gehörschutz"), sec="features"),
    "antifog": dict(kind="bool", label=L("Anti-fog", "Proti mlžení", "Proti zahmlievaniu", "Antibeschlag"), sec="features"),
    "ballistic": dict(kind="bool", label=L("Ballistic rated", "Balistická odolnost", "Balistická odolnosť", "Ballistisch geprüft"), sec="features"),
    "knuckle": dict(kind="bool", label=L("Knuckle protection", "Chrániče kloubů", "Chrániče kĺbov", "Knöchelschutz"), sec="features"),
    "bluetooth": dict(kind="bool", label=L("Bluetooth"), sec="features"),
    "veg": dict(kind="bool", label=L("Vegetarian / vegan", "Vegetariánské / veganské", "Vegetariánske / vegánske", "Vegetarisch / vegan"), sec="features"),
    "folding": dict(kind="bool", label=L("Folding", "Zavírací", "Zatvárací", "Klappbar"), sec="features"),
    "set": dict(kind="bool", label=L("Set / bundle", "Set / výhodné balení", "Set / výhodné balenie", "Set / Bundle"), sec="features"),
}


def enum(pid: str, label: list[str], sec: str, values: dict[str, list[str]], url: str | None = None) -> None:
    P[pid] = dict(kind="enum", label=label, sec=sec, values=values, **({"url": url} if url else {}))


enum("bbdia", L("BB diameter", "Průměr kuliček", "Priemer guličiek", "BB-Durchmesser"), "build", {"6": L("6 mm"), "8": L("8 mm")})
enum("gtype", L("Gas type", "Druh plynu", "Druh plynu", "Gasart"), "basic", {
    "green": L("Green gas"), "red": L("Red gas"), "black": L("Black gas"), "top": L("Top gas"), "blue": L("Blue gas"),
    "co2": L("CO₂"), "propane": L("Propane", "Propan", "Propán", "Propan")})
enum("co2g", L("CO₂ cartridge", "Velikost bombičky", "Veľkosť bombičky", "CO₂-Kapsel"), "size",
     {"8": L("8 g"), "12": L("12 g"), "88": L("88 g"), "90": L("90 g")})
enum("otype", L("Optic type", "Typ optiky", "Typ optiky", "Optiktyp"), "basic", {
    "reddot": L("Red dot", "Kolimátor", "Kolimátor", "Red Dot"), "holo": L("Holographic", "Holografický", "Holografický", "Holografisch"),
    "scope": L("Scope", "Puškohled", "Puškohľad", "Zielfernrohr"), "magnifier": L("Magnifier", "Zvětšovač", "Zväčšovač", "Magnifier"),
    "prism": L("Prism", "Hranolový", "Hranolový", "Prisma"), "night": L("Night vision", "Noční vidění", "Nočné videnie", "Nachtsicht"),
    "mount": L("Mounts & rings", "Montáže a kroužky", "Montáže a krúžky", "Montagen & Ringe"),
    "cover": L("Covers & protectors", "Krytky a chrániče", "Krytky a chrániče", "Schutzkappen")})
enum("omount", L("Mount", "Uchycení", "Uchytenie", "Montage"), "compat", {
    "ris": L("RIS / Picatinny 20 mm"), "dovetail": L("Dovetail 11 mm", "Rybina 11 mm", "Rybina 11 mm", "Prismenschiene 11 mm"),
    "mlok": L("M-LOK"), "keymod": L("KeyMod"), "qd": L("QD"), "helmet": L("Helmet", "Na helmu", "Na prilbu", "Helm")})
enum("ltype", L("Light type", "Typ svítilny", "Typ svietidla", "Lampentyp"), "basic", {
    "flashlight": L("Flashlight", "Svítilna", "Svietidlo", "Taschenlampe"), "weaponlight": L("Weapon light", "Svítilna na zbraň", "Svietidlo na zbraň", "Waffenlicht"),
    "laser": L("Laser", "Laser", "Laser", "Laser"), "peq": L("PEQ box", "PEQ box", "PEQ box", "PEQ-Box"),
    "headlamp": L("Headlamp", "Čelovka", "Čelovka", "Stirnlampe"), "marker": L("Marker / ID light", "Identifikační světlo", "Identifikačné svetlo", "Markierungslicht"),
    "accessory": L("Mounts & accessories", "Montáže a příslušenství", "Montáže a príslušenstvo", "Montagen & Zubehör")})
enum("lcolor", L("Laser colour", "Barva laseru", "Farba lasera", "Laserfarbe"), "build",
     {"red": L("Red", "Červený", "Červený", "Rot"), "green": L("Green", "Zelený", "Zelený", "Grün"), "ir": L("IR", "IR", "IR", "IR")})
enum("chem", L("Battery type", "Typ článků", "Typ článkov", "Zelltyp"), "basic", {
    "lipo": L("Li-Po"), "liion": L("Li-Ion"), "life": L("LiFe"), "nimh": L("NiMH"), "nicd": L("NiCd"),
    "alkaline": L("Alkaline", "Alkalické", "Alkalické", "Alkaline"), "lithium": L("Lithium (CR123 …)", "Lithiové (CR123 …)", "Lítiové (CR123 …)", "Lithium (CR123 …)")})
enum("conn", L("Connector", "Konektor", "Konektor", "Stecker"), "compat", {
    "deans": L("Deans (T-plug)"), "tamiya-mini": L("Mini Tamiya", "Malá Tamiya", "Malá Tamiya", "Mini-Tamiya"),
    "tamiya-large": L("Large Tamiya", "Velká Tamiya", "Veľká Tamiya", "Große Tamiya"), "tamiya": L("Tamiya"),
    "xt": L("XT30 / XT60"), "jst": L("JST"), "usb": L("USB")})
enum("bshape", L("Shape", "Tvar", "Tvar", "Form"), "build", {
    "stick": L("Stick", "Stick (tyčka)", "Stick (tyčka)", "Stick"), "block": L("Mini block", "Mini blok", "Mini blok", "Mini-Block"),
    "nunchuck": L("Nunchuck / split", "Dvojdílná (nunchuck)", "Dvojdielna (nunchuck)", "Nunchuck"),
    "large": L("Large", "Velká", "Veľká", "Groß"), "peq": L("PEQ / box", "Do PEQ boxu", "Do PEQ boxu", "PEQ-Box"),
    "cell": L("Single cell (AA, CR123 …)", "Článek (AA, CR123 …)", "Článok (AA, CR123 …)", "Einzelzelle (AA, CR123 …)")})
enum("ptype", L("Part", "Druh dílu", "Druh dielu", "Teil"), "basic", {
    "barrel": L("Inner barrel", "Vnitřní hlaveň", "Vnútorná hlaveň", "Innenlauf"), "bucking": L("Hop-up bucking", "Hop-up gumička", "Hop-up gumička", "Hop-up-Gummi"),
    "hopup": L("Hop-up chamber", "Hop-up komora", "Hop-up komora", "Hop-up-Kammer"), "spring": L("Spring", "Pružina", "Pružina", "Feder"),
    "gearbox": L("Gearbox", "Mechabox", "Mechabox", "Gearbox"), "motor": L("Motor", "Motor", "Motor", "Motor"),
    "piston": L("Piston", "Píst", "Piest", "Kolben"), "cylinder": L("Cylinder", "Válec", "Valec", "Zylinder"),
    "nozzle": L("Nozzle", "Tryska", "Tryska", "Düse"), "gears": L("Gears", "Ozubená kola", "Ozubené kolesá", "Zahnräder"),
    "mosfet": L("MOSFET / ETU", "MOSFET / ETU", "MOSFET / ETU", "MOSFET / ETU"), "trigger": L("Trigger", "Spoušť", "Spúšť", "Abzug"),
    "stock": L("Stock", "Pažba", "Pažba", "Schaft"), "handguard": L("Handguard", "Předpažbí", "Predpažbie", "Handschutz"),
    "grip": L("Grip", "Rukojeť", "Rukoväť", "Griff"), "rail": L("Rails & mounts", "Lišty a montáže", "Lišty a montáže", "Schienen & Montagen"),
    "suppressor": L("Suppressor", "Tlumič", "Tlmič", "Schalldämpfer"), "muzzle": L("Flash hider / muzzle", "Plamenná / kompenzátor", "Plameňová / kompenzátor", "Mündungsfeuerdämpfer"),
    "sights": L("Iron sights", "Mířidla", "Mieridlá", "Visier"), "bipod": L("Bipod", "Dvojnožka", "Dvojnožka", "Zweibein"),
    "bolt": L("Bolt / slide", "Závěr", "Záver", "Verschluss"), "catch": L("Catches & levers", "Záchyty a páky", "Záchyty a páky", "Hebel & Fänge"),
    "seals": L("O-rings & seals", "O-kroužky a těsnění", "O-krúžky a tesnenia", "O-Ringe & Dichtungen"),
    "wiring": L("Wiring", "Kabeláž", "Kabeláž", "Verkabelung"), "screws": L("Screws & pins", "Šrouby a čepy", "Skrutky a čapy", "Schrauben & Stifte"),
    "care": L("Maintenance & lube", "Údržba a mazání", "Údržba a mazanie", "Pflege & Schmierung"), "tools": L("Tools", "Nářadí", "Náradie", "Werkzeug"),
    "kit": L("Kits & sets", "Sady", "Sady", "Kits")})
enum("fits", L("Fits", "Kompatibilní s", "Kompatibilné s", "Passend für"), "compat", {
    "m4": L("M4 / M16 / AR"), "ak": L("AK"), "g36": L("G36"), "mp5": L("MP5"), "aug": L("AUG"), "p90": L("P90"), "scar": L("SCAR"),
    "g3": L("G3"), "m14": L("M14"), "sr25": L("SR-25 / M110"), "mp7": L("MP7"), "scorpion": L("Scorpion EVO"), "bren": L("BREN"),
    "vsr": L("VSR-10"), "l96": L("L96 / AWS"), "m24": L("M24 / M700"), "hicapa": L("Hi-Capa"), "1911": L("1911"), "glock": L("Glock"),
    "m9": L("M9 / M92"), "p226": L("P226"), "usp": L("USP"), "cz75": L("CZ 75 / Shadow"), "p09": L("CZ P-07 / P-09 / P-10"),
    "aap01": L("AAP-01"), "ssx": L("Novritsch SSX / SSP"), "universal": L("Universal", "Univerzální", "Univerzálne", "Universal")})
enum("gbv", L("Gearbox version", "Verze mechaboxu", "Verzia mechaboxu", "Gearbox-Version"), "compat",
     {f"v{n}": L(f"V{n}") for n in (2, 3, 6, 7)})
enum("bdia", L("Inner barrel bore", "Vnitřní průměr hlavně", "Vnútorný priemer hlavne", "Innendurchmesser"), "build",
     {d: L(d + " mm") for d in ("6.01", "6.02", "6.03", "6.04", "6.05", "6.08", "6.10", "6.13")})
enum("axle", L("Motor axle", "Délka hřídele motoru", "Dĺžka hriadeľa motora", "Motorachse"), "build",
     {"short": L("Short", "Krátká", "Krátka", "Kurz"), "medium": L("Medium", "Střední", "Stredná", "Mittel"), "long": L("Long", "Dlouhá", "Dlhá", "Lang")})
enum("thread", L("Thread", "Závit", "Závit", "Gewinde"), "compat",
     {"14ccw": L("14 mm CCW (−)", "14 mm levotočivý (−)", "14 mm ľavotočivý (−)", "14 mm Linksgewinde (−)"),
      "14cw": L("14 mm CW (+)", "14 mm pravotočivý (+)", "14 mm pravotočivý (+)", "14 mm Rechtsgewinde (+)"),
      "11cw": L("11 mm CW (+)", "11 mm pravotočivý (+)", "11 mm pravotočivý (+)", "11 mm Rechtsgewinde (+)")})
SIZES = ("xs", "s", "m", "l", "xl", "xxl", "xxxl")
enum("size", L("Size", "Velikost", "Veľkosť", "Größe"), "basic", {s: L(s.upper()) for s in SIZES})
enum("fabric", L("Fabric", "Materiál", "Materiál", "Material"), "build",
     {"500d": L("500D Cordura"), "1000d": L("1000D Cordura"), "cordura": L("Cordura (other)", "Cordura (jiná)", "Cordura (iná)", "Cordura (andere)")})
enum("vtype", L("Vest type", "Typ vesty", "Typ vesty", "Westentyp"), "basic", {
    "carrier": L("Plate carrier", "Nosič plátů", "Nosič plátov", "Plattenträger"), "chestrig": L("Chest rig"),
    "vest": L("Tactical vest", "Taktická vesta", "Taktická vesta", "Taktische Weste"), "bandolier": L("Bandolier", "Bandalír", "Bandalír", "Bandolier"),
    "panel": L("Panels & accessories", "Panely a příslušenství", "Panely a príslušenstvo", "Panels & Zubehör")})
enum("pouchtype", L("Pouch / bag type", "Typ sumky / tašky", "Typ sumky / tašky", "Taschentyp"), "basic", {
    "mag": L("Magazine pouch", "Sumka na zásobníky", "Sumka na zásobníky", "Magazintasche"),
    "pistolmag": L("Pistol magazine pouch", "Sumka na pistolové zásobníky", "Sumka na pištoľové zásobníky", "Pistolenmagazintasche"),
    "grenade": L("Grenade pouch", "Granátová sumka", "Granátová sumka", "Granatentasche"), "medic": L("Medical / IFAK", "Zdravotnická / IFAK", "Zdravotnícka / IFAK", "Sanität / IFAK"),
    "utility": L("Utility / admin", "Univerzální / admin", "Univerzálna / admin", "Mehrzweck / Admin"), "dump": L("Dump pouch", "Odhazovák", "Odhadzovák", "Abwurfsack"),
    "radio": L("Radio pouch", "Sumka na vysílačku", "Sumka na vysielačku", "Funktasche"), "hydration": L("Hydration", "Hydratační", "Hydratačná", "Trinksystem"),
    "backpack": L("Backpack", "Batoh", "Batoh", "Rucksack"), "bag": L("Bag", "Taška", "Taška", "Tasche"),
    "belt": L("Belt", "Opasek", "Opasok", "Gürtel"), "case": L("Gun case / bag", "Pouzdro / kufr na zbraň", "Puzdro / kufor na zbraň", "Waffentasche / Koffer")})
enum("hand", L("Hand", "Pro ruku", "Pre ruku", "Hand"), "basic",
     {"right": L("Right", "Pravá", "Pravá", "Rechts"), "left": L("Left", "Levá", "Ľavá", "Links"), "ambi": L("Ambidextrous", "Oboustranné", "Obojstranné", "Beidseitig")})
enum("hmount", L("Worn on", "Nošení", "Nosenie", "Trageweise"), "basic", {
    "belt": L("Belt", "Na opasek", "Na opasok", "Gürtel"), "thigh": L("Thigh / drop leg", "Stehenní", "Stehenné", "Oberschenkel"),
    "molle": L("MOLLE"), "shoulder": L("Shoulder", "Podpažní", "Podpažné", "Schulter")})
enum("hmat", L("Material", "Materiál", "Materiál", "Material"), "build",
     {"polymer": L("Polymer / Kydex"), "fabric": L("Fabric", "Textil", "Textil", "Stoff"), "leather": L("Leather", "Kůže", "Koža", "Leder")})
enum("spoints", L("Attachment points", "Počet bodů", "Počet bodov", "Befestigungspunkte"), "basic",
     {"1": L("1-point", "Jednobodový", "Jednobodový", "1-Punkt"), "2": L("2-point", "Dvoubodový", "Dvojbodový", "2-Punkt"), "3": L("3-point", "Tříbodový", "Trojbodový", "3-Punkt")})
enum("ctype", L("Clothing type", "Druh oblečení", "Druh oblečenia", "Kleidungsart"), "basic", {
    "pants": L("Trousers", "Kalhoty", "Nohavice", "Hosen"), "shirt": L("Shirts & combat shirts", "Košile a blůzy", "Košele a blúzy", "Hemden"),
    "tshirt": L("T-shirts", "Trička", "Tričká", "T-Shirts"), "jacket": L("Jackets", "Bundy", "Bundy", "Jacken"),
    "hoodie": L("Hoodies & fleece", "Mikiny a fleece", "Mikiny a fleece", "Hoodies & Fleece"), "boots": L("Boots", "Boty", "Topánky", "Stiefel"),
    "headwear": L("Caps & hats", "Čepice a kšiltovky", "Čiapky a šiltovky", "Mützen & Kappen"), "balaclava": L("Balaclavas", "Kukly", "Kukly", "Sturmhauben"),
    "ghillie": L("Ghillie suits", "Hejkalové obleky", "Hejkalové obleky", "Ghillie"), "uniform": L("Uniforms", "Uniformy", "Uniformy", "Uniformen"),
    "underwear": L("Underwear", "Spodní prádlo", "Spodná bielizeň", "Unterwäsche"), "socks": L("Socks", "Ponožky", "Ponožky", "Socken"),
    "patch": L("Patches", "Nášivky", "Nášivky", "Patches"), "pads": L("Knee & elbow pads", "Chrániče kolen a loktů", "Chrániče kolien a lakťov", "Knie- & Ellbogenschützer"),
    "scarf": L("Scarves & shemaghs", "Šátky a šály", "Šatky a šály", "Tücher")})
enum("masktype", L("Mask type", "Typ masky", "Typ masky", "Maskentyp"), "basic", {
    "full": L("Full face", "Celoobličejová", "Celotvárová", "Vollgesicht"), "lower": L("Lower face", "Spodní část obličeje", "Spodná časť tváre", "Unteres Gesicht"),
    "accessory": L("Accessories", "Příslušenství", "Príslušenstvo", "Zubehör")})
enum("lens", L("Lens", "Zorník", "Zorník", "Glas"), "basic", {
    "clear": L("Clear", "Čirý", "Číry", "Klar"), "dark": L("Smoke / dark", "Tmavý", "Tmavý", "Dunkel"), "yellow": L("Yellow / amber", "Žlutý", "Žltý", "Gelb"),
    "orange": L("Orange", "Oranžový", "Oranžový", "Orange"), "mirror": L("Mirror", "Zrcadlový", "Zrkadlový", "Verspiegelt"),
    "mesh": L("Mesh", "Mřížka", "Mriežka", "Gitter")})
enum("htype", L("Helmet type", "Typ helmy", "Typ prilby", "Helmtyp"), "basic", {
    "fast": L("FAST"), "mich": L("MICH / ACH"), "exfil": L("EXFIL"), "bump": L("Bump"), "pasgt": L("PASGT"), "ww2": L("M1 / historic", "M1 / historické", "M1 / historické", "M1 / historisch")})
enum("helmpart", L("Helmet item", "Helmy a příslušenství", "Prilby a príslušenstvo", "Helm & Zubehör"), "basic", {
    "helmet": L("Helmets", "Helmy", "Prilby", "Helme"), "cover": L("Covers", "Potahy", "Poťahy", "Bezüge"),
    "mount": L("Mounts & rails", "Montáže a lišty", "Montáže a lišty", "Montagen & Schienen"), "pads": L("Pads & straps", "Polštářky a řemínky", "Vankúšiky a remienky", "Polster & Gurte"),
    "accessory": L("Other accessories", "Ostatní příslušenství", "Ostatné príslušenstvo", "Sonstiges Zubehör")})
enum("fingers", L("Fingers", "Prsty", "Prsty", "Finger"), "basic", {"full": L("Full finger", "Celoprsté", "Celoprsté", "Vollfinger"), "half": L("Fingerless", "Bezprsté", "Bezprsté", "Fingerlos")})
enum("commtype", L("Radio & headset type", "Druh vysílačky / headsetu", "Druh vysielačky / headsetu", "Funk- & Headset-Art"), "basic", {
    "radio": L("Radios", "Vysílačky", "Vysielačky", "Funkgeräte"), "headset": L("Headsets", "Headsety", "Headsety", "Headsets"),
    "earpro": L("Hearing protection", "Chrániče sluchu", "Chrániče sluchu", "Gehörschutz"), "ptt": L("PTT"),
    "antenna": L("Antennas", "Antény", "Antény", "Antennen"), "mic": L("Microphones & earpieces", "Mikrofony a sluchátka", "Mikrofóny a slúchadlá", "Mikrofone & Hörer"),
    "power": L("Batteries & chargers", "Baterie a nabíječky", "Batérie a nabíjačky", "Akkus & Ladegeräte"),
    "accessory": L("Accessories", "Příslušenství", "Príslušenstvo", "Zubehör")})
enum("rconn", L("Radio connector", "Konektor vysílačky", "Konektor vysielačky", "Funkanschluss"), "compat",
     {"kenwood": L("Kenwood (2-pin)"), "motorola": L("Motorola"), "midland": L("Midland"), "icom": L("ICOM"), "yaesu": L("Yaesu")})
enum("foodtype", L("Food type", "Druh jídla", "Druh jedla", "Essensart"), "basic", {
    "meal": L("Main meals", "Hlavní jídla", "Hlavné jedlá", "Hauptgerichte"), "breakfast": L("Breakfast & desserts", "Snídaně a dezerty", "Raňajky a dezerty", "Frühstück & Desserts"),
    "soup": L("Soups", "Polévky", "Polievky", "Suppen"), "snack": L("Jerky & snacks", "Jerky a snacky", "Jerky a snacky", "Jerky & Snacks"),
    "ration": L("Ration packs", "Celodenní dávky", "Celodenné dávky", "Rationspakete"), "water": L("Water & drinks", "Voda a nápoje", "Voda a nápoje", "Wasser & Getränke"),
    "heater": L("Heaters", "Samoohřev", "Samoohrev", "Heizer")})
enum("grentype", L("Pyro type", "Druh pyra / granátu", "Druh pyra / granátu", "Pyro-Art"), "basic", {
    "launcher": L("Grenade launchers", "Granátomety", "Granátomety", "Granatwerfer"), "shell": L("40 mm shells", "40mm granáty", "40mm granáty", "40-mm-Granaten"),
    "hand": L("Hand grenades", "Ruční granáty", "Ručné granáty", "Handgranaten"), "smoke": L("Smoke", "Dýmovnice", "Dymovnice", "Rauch"),
    "sound": L("Flash & sound", "Výbušky", "Výbušky", "Knall"), "pyro": L("Fireworks", "Ohňostroje a petardy", "Ohňostroje a petardy", "Feuerwerk")})
enum("bowtype", L("Bow / crossbow item", "Luky a kuše – druh", "Luky a kuše – druh", "Bogen / Armbrust – Art"), "basic", {
    "bow": L("Bows", "Luky", "Luky", "Bögen"), "crossbow": L("Crossbows", "Kuše", "Kuše", "Armbrüste"), "arrows": L("Arrows & bolts", "Šípy", "Šípy", "Pfeile"),
    "tips": L("Tips", "Hroty", "Hroty", "Spitzen"), "strings": L("Strings & cables", "Tětivy a lanoví", "Tetivy a lanovie", "Sehnen"),
    "slingshot": L("Slingshots", "Praky", "Praky", "Schleudern"), "blowgun": L("Blowguns", "Foukačky", "Fúkačky", "Blasrohre"),
    "accessory": L("Accessories", "Příslušenství", "Príslušenstvo", "Zubehör")})
enum("meleetype", L("Melee type", "Druh chladné zbraně", "Druh chladnej zbrane", "Nahkampf-Art"), "basic", {
    "knife": L("Knives", "Nože", "Nože", "Messer"), "machete": L("Machetes", "Mačety", "Mačety", "Macheten"), "sword": L("Swords", "Meče a katany", "Meče a katany", "Schwerter"),
    "axe": L("Axes", "Sekery", "Sekery", "Äxte"), "baton": L("Batons", "Obušky", "Obušky", "Schlagstöcke"), "bayonet": L("Bayonets", "Bajonety", "Bajonety", "Bajonette"),
    "training": L("Training", "Tréninkové", "Tréningové", "Training"), "sharpener": L("Sharpeners", "Brousky a ocílky", "Brúsky a ocieľky", "Schärfer"),
    "accessory": L("Sheaths & accessories", "Pouzdra a příslušenství", "Puzdrá a príslušenstvo", "Scheiden & Zubehör")})
enum("targettype", L("Target type", "Typ terče", "Typ terča", "Zieltyp"), "basic", {
    "paper": L("Paper targets", "Papírové terče", "Papierové terče", "Papierziele"), "steel": L("Steel & poppers", "Ocelové a poppery", "Oceľové a poppery", "Stahl & Popper"),
    "electronic": L("Electronic", "Elektronické", "Elektronické", "Elektronisch"), "trap": L("Pellet traps", "Lapače", "Lapače", "Kugelfänge"),
    "gallery": L("Shooting galleries", "Střelnice", "Strelnice", "Schießbuden"), "stand": L("Stands & holders", "Stojany a držáky", "Stojany a držiaky", "Ständer")})
enum("agpower", L("Airgun power", "Pohon vzduchovky", "Pohon vzduchovky", "Luftdruck-Antrieb"), "power", {
    "co2": L("CO₂"), "pcp": L("PCP (pre-charged)", "PCP (předtlaková)", "PCP (predtlaková)", "PCP (Pressluft)"),
    "spring": L("Spring / break barrel", "Pružinová / zlamovací", "Pružinová / lámacia", "Feder / Knicklauf"),
    "gaspiston": L("Gas piston", "Plynový píst", "Plynový piest", "Gaskolben")})

# ------------------------------------------------------------------ per category
# The first ones marked "*" show in the sidebar (after price, availability and brand).
CATEGORY_PARAMS: dict[str, list[str]] = {
    "pistols": ["power*", "mps*", "material*", "blowback", "platform", "joule", "licensed", "set"],
    "guns": ["power*", "platform*", "mps*", "material", "inch", "blowback", "licensed", "joule", "set"],
    "smgs": ["power*", "platform*", "mps*", "material", "blowback", "licensed", "joule", "set"],
    "shotguns": ["power*", "mps*", "material*", "platform", "licensed", "set"],
    "snipers": ["power*", "mps*", "platform*", "material", "joule", "licensed", "set"],
    "airguns": ["airgun*", "caliber*", "agpower*", "joule*", "mps", "pcs", "material", "set"],
    "grenades": ["grentype*", "pcs*", "power"],
    "magazines": ["cap*", "fits*", "rounds*", "power", "material"],
    "bbs": ["bbw*", "bbcount*", "bio*", "tracer", "bbdia"],
    "gas": ["gtype*", "ml*", "co2g", "pcs"],
    "optics": ["otype*", "zoom*", "illum*", "obj", "omount"],
    "lights": ["ltype*", "lm*", "lcolor*", "usb", "omount"],
    "parts": ["ptype*", "fits*", "material*", "gbv", "bdia", "blen", "spring", "shore", "axle", "thread"],
    "batteries": ["chem*", "volt*", "mah*", "conn*", "bshape", "crate"],
    "chargers": ["chem*", "smart*", "conn", "watt"],
    "vests": ["vtype*", "size*", "molle*", "fabric"],
    "pouches": ["pouchtype*", "molle*", "fits", "litres", "fabric"],
    "holsters": ["fits*", "hand*", "hmount*", "hmat"],
    "slings": ["spoints*", "bungee*", "padded"],
    "masks": ["masktype*", "earpro*"],
    "eyewear": ["lens*", "antifog*", "ballistic*"],
    "helmets": ["helmpart*", "htype*", "size"],
    "gloves": ["size*", "fingers*", "knuckle"],
    "clothing": ["ctype*", "size*", "shoe"],
    "comms": ["commtype*", "rconn*", "bluetooth", "earpro"],
    "food": ["foodtype*", "grams*", "veg"],
    "melee": ["meleetype*", "folding"],
    "bows": ["bowtype*", "lbs*", "pcs"],
    "targets": ["targettype*", "pcs*"],
    "cables": ["conn*"],
    "magnets": [], "books": [], "other": [],
}
# Sidebar parameters of a whole group (e.g. "Guns"), whose window shows all of its subcategories' ones.
GROUP_BASIC: dict[str, list[str]] = {
    "weapons": ["power", "platform", "mps"], "ammo": ["cap", "bbw", "gtype"], "sights": ["otype", "ltype", "zoom"],
    "upgrades": ["ptype", "fits", "chem"], "gear": ["vtype", "pouchtype", "molle"], "protection": ["masktype", "lens", "helmpart"],
    "apparel": ["ctype", "size"], "radios": ["commtype", "rconn"], "food": ["foodtype"], "misc": ["meleetype", "bowtype", "targettype"],
}
COMMON = ["color"]  # brand and shop are added by the browser from the product data itself


# ------------------------------------------------------------------ reading the name
def _first(t: str, table: list[tuple[str, str]]) -> str | None:
    """The value whose pattern matches earliest in the name ("Sumka na zásobník" is a pouch)."""
    hits = [(m.start(), i, v) for i, (v, rx) in enumerate(table) for m in [re.search(rx, t)] if m]
    return min(hits)[2] if hits else None


def _all(t: str, table: list[tuple[str, str]]) -> list[str]:
    return list(dict.fromkeys(v for v, rx in table if re.search(rx, t)))


def _num(rx: str, t: str, lo: float, hi: float, group: int = 1) -> float | None:
    for m in re.finditer(rx, t):
        try:
            v = float(m.group(group).replace(",", ".").replace(" ", ""))
        except (TypeError, ValueError):
            continue
        if lo <= v <= hi:
            return round(v, 2)
    return None


FITS = [
    ("m4", r"\b(m4\w*|m16\w*|ar-?15|ar\b|hk ?416|416|m733|sr-?16|cm16|gr16|v2 mechabox|mk ?18)"),
    ("ak", r"\b(ak|akm\w*|aks\w*|ak-?\d+\w*|rpk\w*|lck\w*|v3 mechabox)\b"), ("g36", r"\bg36\w*"), ("mp5", r"\bmp-?5\w*"),
    ("aug", r"\baug\w*"), ("p90", r"\bp90\b"), ("scar", r"\bscar\w*"), ("g3", r"\bg3\w*\b"), ("m14", r"\bm14\b"),
    ("sr25", r"\b(sr-?25|m110)\w*"), ("mp7", r"\bmp-?7\w*"), ("scorpion", r"\b(scorpion|evo ?3)\b"), ("bren", r"\bbren\b"),
    ("vsr", r"\b(vsr\w*|bar-?10|cm\.?70[01])"), ("l96", r"\b(l96\w*|aws|mb-?0?1|mb44\w*)"), ("m24", r"\b(m24|m700|m40)\b"),
    ("hicapa", r"\bhi-?capa\w*"), ("1911", r"\b(m?1911\w*|meu)\b"), ("glock", r"\b(glock\w*|g17|g18\w*|g19|g-series|g series)\b"),
    ("m9", r"\b(m9\w*|m92\w*|beretta)\b"), ("p226", r"\b(p226|f226|p228|f228)\b"), ("usp", r"\busp\w*"),
    ("cz75", r"\b(cz ?75\w*|shadow ?2?)\b"), ("p09", r"\b(p-?07|p-?09|p-?10)\b"), ("aap01", r"\baap-?01\w*"),
    ("ssx", r"\b(ssx\d*|ssp\d*)\b"), ("universal", r"\b(univerzal\w*|universal\w*)\b"),
]
PART_TYPES = [
    ("barrel", r"\b(hlaven\w*|hlavne|barrel\w*)\b"), ("bucking", r"\b(gumick\w*|bucking\w*|sorbopad\w*)"),
    ("hopup", r"\b(hop-?up (komor\w*|unit|jednotk\w*)|komora|chamber)\b"), ("spring", r"\b(pruzin[ay]\w*|pruzin\b|springs?)\b"),
    ("gearbox", r"\b(mechabox\w*|gearbox\w*)\b"), ("motor", r"\bmotor\w*"), ("piston", r"\b(pist|pistu|pisty|piston\w*|pistni\w*)\b"),
    ("cylinder", r"\b(valec\w*|valc\w*|cylind\w*)\b"), ("nozzle", r"\b(trysk\w*|nozzle\w*)\b"),
    ("gears", r"\b(ozuben\w*|kol[ao]\b|sada kol|gears?|gear set)\b"), ("mosfet", r"\b(mosfet\w*|etu|elektronick\w* spoust\w*|trigger unit)\b"),
    ("trigger", r"\b(spoust\w*|trigger\w*)\b"), ("stock", r"\b(pazb[ay]\w*|pazb\b|stock\w*|buffer tube)\b"),
    ("handguard", r"\b(predpazb\w*|handguard\w*)\b"), ("grip", r"\b(rukojet\w*|grip\w*)\b"),
    ("rail", r"\b(lista|listy|lisht\w*|rail\w*|montaz\w*|mount\w*|ris)\b"), ("suppressor", r"\b(tlumic\w*|suppressor\w*|silencer\w*)\b"),
    ("muzzle", r"\b(plamenn\w*|flash ?hider\w*|kompenzator\w*|usti)\b"), ("sights", r"\b(miridl\w*|musk[ay]|hledi|iron ?sight\w*)\b"),
    ("bipod", r"\b(dvojnoz\w*|bipod\w*)\b"), ("bolt", r"\b(zaver\w*|bolt\w*|slide)\b"),
    ("catch", r"\b(zachyt\w*|pak[ay]\w*|magwell\w*|catch\w*|lever\w*)\b"),
    ("seals", r"\b(o-?krouz\w*|krouz\w*|tesnen\w*|o-?ring\w*)\b"), ("wiring", r"\b(kabelaz\w*|wiring)\b"),
    ("screws", r"\b(sroub\w*|cep\w*|screw\w*)\b"), ("care", r"\b(olej\w*|silikon\w*|maz\w*|lube\w*|cistic\w*|cisteni|udrzb\w*|sprej\w*)\b"),
    ("tools", r"\b(klic\w*|nastroj\w*|naradi|tool\w*|sroubovak\w*)\b"), ("kit", r"\b(sada|set|kit)\b"),
]
SIZE_RX = (r"(?:varianta:?|vel\.?|velikost\w*|size)\s*:?\s*(xxs|xs|s|m|l|xl|xxl|xxxl|[2-5]xl)(?:-[rls])?\b"
           r"|[\s,(-](xs|s|m|l|xl|xxl|xxxl|[2-5]xl)(?:-[rls])?\)?\s*$")
_SIZE_FIX = {"2xl": "xxl", "3xl": "xxxl", "xxs": "xs", "4xl": "xxxl", "5xl": "xxxl"}


def extract(title: str, category: str, price: float | None = None) -> tuple[list[str], dict[str, float]]:
    """Tags ("chem:lipo", "molle:y") and numbers ({"mah": 1300}) for the filters of a product."""
    t = " " + strip_accents(title.lower()) + " "
    tags: list[str] = []
    n: dict[str, float] = {}

    def tag(pid: str, value: str | None) -> None:
        if value:
            tags.append(f"{P[pid].get('tag', pid)}:{value}")

    def flag(pid: str, rx: str) -> None:
        if re.search(rx, t):
            tags.append(f"{P[pid].get('tag', pid)}:y")

    def num(pid: str, rx: str, lo: float, hi: float) -> None:
        v = _num(rx, t, lo, hi)
        if v is not None:
            n[pid] = v

    flag("set", r"\b(set|vyhodn\w* (set|balen\w*)|bundle|balicek)\b")
    if category in ("pistols", "guns", "smgs", "shotguns", "snipers", "airguns"):
        mps = _num(r"(\d{2,3}) ?(m/s|ms|mps)\b", t, 40, 400)
        if mps is None and (fps := _num(r"(\d{3}) ?fps\b", t, 150, 1000)):
            mps = round(fps * 0.3048)
        if mps:
            n["mps"] = mps
        num("joule", r"(\d{1,3}(?:[.,]\d{1,2})?) ?j\b", 0.3, 400)
        flag("blowback", r"\b(blow ?back\w*|ebb|gbbr?|blowbac\w*)\b")
        flag("licensed", r"\b(licen[cs]\w*|licensed|oficialn\w*)\b")
        num("inch", r"(?<![\d.,])(\d{1,2}(?:[.,]\d)?) ?(\"|″|''|inch\w*|palc\w*)", 3, 30)
    if category == "airguns":
        tag("agpower", _first(t, [("co2", r"\bco2\b"), ("pcp", r"\b(pcp|predtlak\w*|pre-?charged)\b"),
                                  ("gaspiston", r"\b(igt|nitro\w*|gas ?piston|plynov\w* pist\w*)\b"),
                                  ("spring", r"\b(zalamov\w*|lamac\w*|break ?barrel|pruzin\w*|spring)\b")]))
        num("pcs", r"(\d{2,5}) ?(ks|pcs|kusu)\b", 5, 10000)
    if category == "grenades":
        tag("grentype", _first(t, [
            ("launcher", r"\b(granatomet\w*|launcher\w*|m203|m320|gp-?25|m79|mgl|m32)\b"),
            ("shell", r"\b(40 ?mm|patron\w*|naboj\w*|shell\w*)\b"), ("smoke", r"\b(dym\w*|smoke\w*)\b"),
            ("sound", r"\b(vybus\w*|thunder\w*|flash ?bang|zablesk\w*|petard\w*|tornado|storm)\b"),
            ("hand", r"\b(granat\w*|grenade\w*|rg-?\d+|f-?1|m67)\b"),
            ("pyro", r"\b(pyro\w*|kompakt|raket\w*|fontan\w*|ohnostroj\w*|prskav\w*|svice)\b")]))
        num("pcs", r"(\d{1,4}) ?(ks|pcs|kusu)\b", 1, 1000)
        if re.search(r"\b(co2)\b", t):
            tags.append("pw:co2")
        elif re.search(r"\b(plyn\w*|gas)\b", t):
            tags.append("pw:gas")
    if category == "magazines":
        tags += [f"fits:{v}" for v in _all(t, FITS)]
        num("rounds", r"(\d{1,4}) ?(ran|rds|rounds|bbs?|kulic\w*|ks)\b", 5, 6000)
        tag("power", _first(t, [("co2", r"\bco2\b"), ("hpa", r"\bhpa\b"), ("gas", r"\b(gbbr?|gnb|plyn\w*|green ?gas|gas)\b"),
                                ("electric", r"\b(elektr\w*|electric|sound control|zvukov\w*)\b")]))
        if re.search(r"\b(kov\w*|celokov\w*|metal\w*|ocel\w*|hlinik\w*|steel|alu\w*)\b", t):
            tags.append("mt:metal")
        elif re.search(r"\b(plast\w*|polymer\w*|abs|nylon\w*)\b", t):
            tags.append("mt:plastic")
    if category == "bbs":
        num("bbcount", r"(\d{1,2}[ .]?\d{3}|\d{3,5}) ?(bbs?|ks|pcs|kulic\w*)\b", 100, 100000)
        flag("bio", r"\bbio\w*")
        flag("tracer", r"\b(tracer\w*|svitic\w*|glow)\b")
        tag("bbdia", "8" if re.search(r"\b8 ?mm\b", t) else "6")
    if category == "gas":
        tag("gtype", _first(t, [("green", r"\bgreen ?gas\b"), ("red", r"\bred\b"), ("black", r"\bblack\b"), ("top", r"\btop ?gas\b"),
                                ("blue", r"\bblue\b"), ("co2", r"\bco2\b"), ("propane", r"\bpropan\w*")]) or
            ("green" if re.search(r"\bgas\b|plyn", t) else None))
        num("ml", r"(\d{2,4}) ?ml\b", 20, 5000)
        if m := re.search(r"\b(8|12|88|90) ?g\b", t):
            if re.search(r"\bco2\b", t):
                tag("co2g", m.group(1))
        num("pcs", r"(\d{1,4}) ?(ks|pcs|kusu|x)\b", 1, 2000)
    if category == "optics":
        tag("otype", _first(t, [
            ("mount", r"\b(montaz\w*|mount\w*|krouz\w*|rings?|riser|zvysen\w*)\b"),
            ("cover", r"\b(krytk\w*|cover\w*|killflash|chranic\w*|protector\w*|sluneck\w*)\b"),
            ("magnifier", r"\b(zvetsov\w*|magnifier\w*)\b"), ("holo", r"\bholo\w*"), ("prism", r"\b(prism\w*|hranol\w*)\b"),
            ("night", r"\b(nocni\w*|night\w*|nvg|pvs-?\d+|termo\w*|thermal\w*)\b"),
            ("scope", r"\b(puskohl[ae]d\w*|scope\w*|optik[ay]|optics?)\b"), ("reddot", r"\b(kolimator\w*|red ?dot\w*|reflex\w*|t-?1|rmr)\b")]))
        if m := re.search(r"(?<![\d.,])(\d{1,2}(?:[.,]\d)?)(?: ?- ?(\d{1,2}))? ?x ?(\d{2})\b(?! ?mm)", t):
            n["zoom"] = float((m.group(2) or m.group(1)).replace(",", "."))
            n["obj"] = float(m.group(3))
        elif (z := _num(r"(?<![\d.,])(\d{1,2}(?:[.,]\d)?) ?x\b", t, 1, 40)) is not None:
            n["zoom"] = z
        flag("illum", r"\b(podsvic\w*|prisvit\w*|illuminat\w*|ir\b)")
        tags += [f"omount:{v}" for v in _all(t, [("ris", r"\b(ris|picatinny|20 ?mm lista|weaver)\b"), ("dovetail", r"\b(11 ?mm|rybin\w*|dovetail)\b"),
                                                ("qd", r"\bqd\b"), ("mlok", r"\bm-?lok\b"), ("keymod", r"\bkeymod\b"), ("helmet", r"\b(helm\w*|prilb\w*)\b")])]
    if category == "lights":
        tag("ltype", _first(t, [
            ("accessory", r"\b(montaz\w*|mount\w*|filtr\w*|filter\w*|spinac\w*|tlakov\w*|switch\w*|pouzdr\w*|kabel\w*)\b"),
            ("peq", r"\b(peq\w*|la-?5\w*|dbal\w*|an/?peq\w*)\b"), ("headlamp", r"\b(celovk\w*|headlamp\w*)\b"),
            ("marker", r"\b(identifik\w*|marker\w*|strob\w*|pozicni\w*|manta)\b"),
            ("laser", r"\blaser\w*"), ("weaponlight", r"\b(na zbran|weapon ?light|m300|m600|m6\d\d|x300|m720|m952|na ris)\b"),
            ("flashlight", r"\b(svitiln\w*|baterk\w*|flashlight\w*|lucern\w*|svetl[oa]|torch)\b")]))
        num("lm", r"(\d{2,5}) ?(lm|lumen\w*)\b", 5, 100000)
        tags += [f"lcolor:{v}" for v in _all(t, [("red", r"\b(cerven\w* laser|laser\w* cerven\w*|red laser|cerveny)\b"),
                                                ("green", r"\b(zelen\w* laser|laser\w* zelen\w*|green laser)\b"),
                                                ("ir", r"\b(ir|infra\w*)\b")]) if "laser" in t or v == "ir"]
        flag("usb", r"\b(nabij\w*|usb\w*|rechargeable|akumulator\w*)\b")
        tags += [f"omount:{v}" for v in _all(t, [("ris", r"\b(ris|picatinny|20 ?mm|weaver)\b"), ("mlok", r"\bm-?lok\b"),
                                                ("keymod", r"\bkeymod\b"), ("helmet", r"\b(helm\w*|prilb\w*)\b")])]
    if category in ("parts",):
        tag("ptype", _first(t, PART_TYPES[:-1]) or _first(t, PART_TYPES[-1:]))  # "Sada pružin" is springs
        tags += [f"fits:{v}" for v in _all(t, FITS)]
        if m := re.search(r"\b(?:v|ver\.? ?|verz\w* ?|version ?)([2367])\b", t):
            tag("gbv", f"v{m.group(1)}")
        if m := re.search(r"(?<![\d.,])6[.,](0[1-8]|1[03])(?!\d)", t):
            tag("bdia", "6." + m.group(1))
        if "ptype:barrel" in tags:
            num("blen", r"(\d{3}) ?mm\b", 80, 700)
        if "ptype:spring" in tags:
            num("spring", r"\bm ?(\d{2,3})\b", 70, 200)
        if "ptype:bucking" in tags:
            num("shore", r"(\d{2}) ?(°|shore|sh\b|stup)", 30, 90)
        if "ptype:motor" in tags:
            tag("axle", _first(t, [("short", r"\b(kratk\w*|short)\b"), ("medium", r"\b(stredn\w*|medium)\b"), ("long", r"\b(dlouh\w*|long)\b")]))
        tag("thread", _first(t, [("14ccw", r"(14 ?mm\W{0,3}(ccw|levo\w*|-)|-\s?14 ?mm|14 ?mm ?-)"),
                                 ("14cw", r"(14 ?mm\W{0,3}(cw|pravo\w*|\+)|\+\s?14 ?mm)"), ("11cw", r"(11 ?mm\W{0,3}(cw|pravo\w*|\+)|\+\s?11 ?mm)")]))
        if re.search(r"\b(kov\w*|celokov\w*|metal\w*|ocel\w*|hlinik\w*|steel|alu\w*|cnc|titan\w*|mosaz\w*|brass)\b", t):
            tags.append("mt:metal")
        elif re.search(r"\b(plast\w*|polymer\w*|abs|nylon\w*|polykarbon\w*)\b", t):
            tags.append("mt:plastic")
    if category == "batteries":
        tag("chem", _first(t, [("lipo", r"\b(li-?pol?|lipo)\b"), ("liion", r"\b(li-?ion|liion)\b"), ("life", r"\b(li-?fe\w*)\b"),
                               ("nimh", r"\bnimh\b"), ("nicd", r"\bnicd\b"), ("alkaline", r"\balkal\w*"),
                               ("lithium", r"\b(cr123\w*|cr2032|lithiov\w*|lithium)\b")]))
        num("volt", r"(\d{1,2}[.,]\d) ?v\b", 1, 30)
        if "volt" not in n:
            num("volt", r"\b(\d{1,2}) ?v\b", 1, 30)
        num("mah", r"(\d{3,5}) ?mah\b", 100, 30000)
        num("crate", r"(\d{1,3}) ?(?:-\d+ ?)?c\b", 5, 150)
        tags += [f"conn:{v}" for v in _batt_conn(t)]
        tag("bshape", _first(t, [("peq", r"\b(peq|anpeq|box)\b"), ("nunchuck", r"\b(nunchuck|butterfly|dvojdil\w*|3 dil\w*|split)\b"),
                                 ("large", r"\b(large|velk\w* typ|velka|velky blok)\b"), ("block", r"\b(block|blok|mini typ|mini block)\b"),
                                 ("stick", r"\b(stick|cqb|mini|ak stick|tycka)\b"), ("cell", r"\b(aa|aaa|cr123\w*|18650|16340|cr2032|18350)\b")]))
    if category == "chargers":
        tags += [f"chem:{v}" for v in _all(t, [("lipo", r"\b(li-?pol?|lipo)\b"), ("liion", r"\b(li-?ion|liion)\b"),
                                               ("life", r"\bli-?fe\b"), ("nimh", r"\bnimh\b"), ("nicd", r"\bnicd\b")])]
        flag("smart", r"\b(intelig\w*|smart|balanc\w*|digital\w*|mikroproces\w*|automatick\w*)\b")
        num("watt", r"(\d{1,4}) ?w\b", 1, 2000)
        tags += [f"conn:{v}" for v in _batt_conn(t)]
    if category in ("vests", "pouches", "holsters"):
        flag("molle", r"\bmolle\b")
        if m := re.search(r"\b(500|1000) ?d\b", t):
            tag("fabric", m.group(1) + "d")
        elif "cordura" in t:
            tag("fabric", "cordura")
    if category == "vests":
        tag("vtype", _first(t, [("panel", r"\b(panel\w*|klop\w*|kamerband\w*|cummerbund|adapter\w*|vlozk\w*|stahovan\w*)\b"),
                                ("carrier", r"\b(nosic\w*|plate ?carrier|jpc|avs|apc|mtpc)\b"), ("chestrig", r"\bchest ?rig\w*"),
                                ("bandolier", r"\b(bandalir\w*|bandolier\w*)\b"), ("vest", r"\b(vest[ay]\w*|vest)\b")]))
    if category == "pouches":
        tag("pouchtype", _first(t, [
            ("case", r"\b(kufr\w*|pouzdr\w* na (zbran|pusk)\w*|obal\w* na (zbran|pusk)\w*|rifle case|gun case|prepravni pouzdr\w*)\b"),
            ("dump", r"\b(odhazov\w*|dump)\b"), ("radio", r"\b(vysilac\w*|radio\w*|radiostanic\w*)\b"),
            ("hydration", r"\b(hydrat\w*|pici vak|camelbak|hydration)\b"), ("medic", r"\b(zdravot\w*|ifak|medic\w*|prvni pomoc\w*)\b"),
            ("grenade", r"\bgranat\w*"), ("pistolmag", r"\bpistol\w* zasobn\w*|zasobn\w* (na|pro) pistol\w*"),
            ("mag", r"\b(zasobn\w*|mag pouch|magazine pouch|taco|stanag|m4|ak)\b"),
            ("utility", r"\b(univerzal\w*|utility|admin|organiz\w*)\b"), ("backpack", r"\b(batoh\w*|backpack\w*|ruksak\w*)\b"),
            ("belt", r"\b(opas\w*|belt\w*)\b"), ("bag", r"\b(task\w*|brasn\w*|bag\w*|vak\w*|ledvink\w*)\b")]))
        num("litres", r"(\d{1,3}) ?(l|litr\w*)\b", 1, 150)
        tags += [f"fits:{v}" for v in _all(t, FITS)]
    if category == "holsters":
        tags += [f"fits:{v}" for v in _all(t, FITS)]
        tag("hand", _first(t, [("ambi", r"\b(oboustr\w*|ambi\w*)\b"), ("right", r"\b(prav\w*|right|rh)\b"), ("left", r"\b(lev[aeyi]\w*|left|lh)\b")]))
        tags += [f"hmount:{v}" for v in _all(t, [("thigh", r"\b(stehen\w*|thigh|drop)\b"), ("shoulder", r"\b(podpaz\w*|shoulder)\b"),
                                                ("molle", r"\bmolle\b"), ("belt", r"\b(opask\w*|na opasek|belt|pasov\w*)\b")])]
        tag("hmat", _first(t, [("polymer", r"\b(polymer\w*|kydex|plast\w*|serpa)\b"), ("leather", r"\b(kozen\w*|leather|kuze)\b"),
                               ("fabric", r"\b(cordura|textil\w*|latk\w*|nylon\w*)\b")]))
    if category == "slings":
        tag("spoints", _first(t, [("1", r"\b(jednobod\w*|1-?bod\w*|1-?point|single ?point)\b"), ("2", r"\b(dvoubod\w*|2-?bod\w*|2-?point|two ?point)\b"),
                                  ("3", r"\b(tribod\w*|3-?bod\w*|3-?point|three ?point)\b")]))
        flag("bungee", r"\b(bungee|pruzn\w*|elasti\w*)\b")
        flag("padded", r"\b(polstr\w*|padded|vycpav\w*)\b")
    if category in ("vests", "helmets", "gloves", "clothing"):
        if m := re.search(SIZE_RX, t):
            s = m.group(1) or m.group(2)
            tag("size", _SIZE_FIX.get(s, s))
    if category == "clothing":
        tag("ctype", _first(t, [
            ("patch", r"\b(nasivk\w*|patch\w*|velcro)\b"), ("pads", r"\b(nakolen\w*|naloket\w*|chranic\w* (kolen|loktu)|knee|elbow)\b"),
            ("boots", r"\b(boty|bot\b|obuv\w*|boot\w*|kanad\w*)\b"), ("ghillie", r"\b(ghillie|hejkal\w*|maskovac\w* oblek)\b"),
            ("uniform", r"\b(uniform\w*|kombinez\w*)\b"), ("pants", r"\b(kalhot\w*|pants|trousers|nohavic\w*|shorts|kratas\w*)\b"),
            ("tshirt", r"\b(trick\w*|triko|t-?shirt\w*|natelnik\w*|tilko)\b"), ("hoodie", r"\b(mikin\w*|hoodie\w*|fleece\w*|flis\w*|svetr\w*)\b"),
            ("shirt", r"\b(kosil\w*|bluz\w*|shirt\w*|ubacs)\b"), ("jacket", r"\b(bund\w*|jacket\w*|parka|softshell|vetrovk\w*|kabat\w*)\b"),
            ("balaclava", r"\b(kukl\w*|balaclava\w*)\b"), ("headwear", r"\b(cepic\w*|ksiltovk\w*|klobouk\w*|cap|hat|baret\w*|brigadyrk\w*|cepice)\b"),
            ("underwear", r"\b(spodk\w*|boxerk\w*|spodn\w* pradl\w*|underwear)\b"), ("socks", r"\b(ponozk\w*|socks?)\b"),
            ("scarf", r"\b(satek|satk\w*|shemag\w*|sal\b|nakrcnik\w*)\b")]))
        if "ctype:boots" in tags:
            num("shoe", r"(?:varianta:?\s*(?:eu\s*)?|vel\.?\s*|eu\s*|velikost\s*)(3[4-9]|4[0-9]|50)(?:[.,]5)?\b", 34, 50)
    if category == "masks":
        tag("masktype", _first(t, [("accessory", r"\b(obal\w*|pouzdr\w*|nahradn\w*|popruh\w*|montaz\w*|mount|ventilator\w*|fan\b|klips\w*)\b"),
                                   ("full", r"\b(full ?face|celoobliceje\w*|celoobl\w*|celkov\w*)\b"),
                                   ("lower", r"\b(lower|spodni|dolni|mesh|mrizk\w*|sitova|sitov\w*|faceprotect\w*|face ?protect\w*|face ?guard)\b")])
            or ("full" if re.search(r"\bmask[ay]?\b", t) else None))
        flag("earpro", r"\b(chranic\w* (usi|sluchu)|ear\w*)\b")
    if category == "eyewear":
        tags += [f"lens:{v}" for v in _all(t, [("clear", r"\b(cir[ayeoi]\w*|clear)\b"), ("dark", r"\b(tmav\w*|smoke\w*|kour\w*|grey|sed[ayeo]\w*|polariz\w*)\b"),
                                              ("yellow", r"\b(zlut\w*|yellow|amber)\b"), ("orange", r"\b(oranz\w*|orange)\b"),
                                              ("mirror", r"\b(zrcad\w*|mirror\w*)\b"), ("mesh", r"\b(mrizk\w*|mesh|sitov\w*)\b")])]
        flag("antifog", r"\b(anti-?fog\w*|nemlz\w*|proti mlz\w*|ventil\w*|fan\b)")
        flag("ballistic", r"\b(balist\w*|ballist\w*|ansi|z87|en ?166|mil-?prf|stanag)\b")
    if category == "helmets":
        tag("helmpart", _first(t, [("cover", r"\b(potah\w*|cover\w*)\b"), ("pads", r"\b(polstar\w*|polstr\w*|pads?|remin\w*|reminek|strap\w*|remen\w*|retenc\w*)\b"),
                                   ("mount", r"\b(montaz\w*|mount\w*|lista|listy|rail\w*|adapter\w*|shroud|nvg)\b"),
                                   ("accessory", r"\b(sroub\w*|zavazi|counterweight|identifik\w*|velcro|suchy zip|suchych zip\w*|panel\w*|krytk\w*|sit\w*)\b"),
                                   ("helmet", r"\b(helm[ay]\b|helma|prilb[ay]\b|prilba|helmet\b|replika balist\w* helm\w*)")]) or "helmet")
        tag("htype", _first(t, [("fast", r"\bfast\b"), ("mich", r"\b(mich|ach)\b"), ("exfil", r"\bexfil\b"), ("bump", r"\bbump\b"),
                                ("pasgt", r"\bpasgt\b"), ("ww2", r"\b(m1|stahlhelm|m35|ww ?ii|vz\.? ?(32|53))\b")]))
    if category == "gloves":
        tag("fingers", "half" if re.search(r"\b(bezprst\w*|half|fingerless|polo ?prst\w*|bez prstu)\b", t) else "full")
        flag("knuckle", r"\b(kloub\w*|knuckle\w*|chranic\w*|tvrzen\w*|hard)\b")
    if category == "comms":
        tag("commtype", _first(t, [
            ("power", r"\b(baterie|akumulator\w*|nabij\w*|charger|adapter\w*|zdroj\w*)\b"), ("antenna", r"\banten\w*"),
            ("ptt", r"\bptt\b"), ("mic", r"\b(mikrofon\w*|handsfree|sluchatk\w* do ucha|zvukovod\w*|earpiece|reproduktor\w*)\b"),
            ("earpro", r"\b(chranic\w* sluchu|spunt\w*|ear ?pro\w*|m31|m32|m300)\b"),
            ("headset", r"\b(headset\w*|nahlavn\w* soupra\w*|sluchatk\w*|comtac|sordin|peltor)\b"),
            ("radio", r"\b(vysilac\w*|radiostanic\w*|pmr|uv-?5r\w*|uv-?82|bf-?\w+|walkie)\b"),
            ("accessory", r"\b(pouzdr\w*|obal\w*|klips\w*|zaves\w*|kabel\w*|montaz\w*|adapter\w*)\b")]))
        tag("rconn", _first(t, [("kenwood", r"\b(kenwood|2-?pin|baofeng)\b"), ("motorola", r"\bmotorola\b"), ("midland", r"\bmidland\b"),
                                ("icom", r"\bicom\b"), ("yaesu", r"\byaesu\b")]))
        flag("bluetooth", r"\bbluetooth\b")
        flag("earpro", r"\b(chranic\w* sluchu|elektronick\w* sluchat\w*|ear ?pro\w*|m31|m32|m300|spunt\w*)\b")
    if category == "food":
        tag("foodtype", _first(t, [
            ("heater", r"\bsamoohrev\w*"), ("water", r"\b(vod[ay]\b|water|napoj\w*|drink\w*)\b"),
            ("ration", r"\b(davk[ay]\w*|ration\w*|full-?day|half-?day|imre|mre box|survival|emergency food|food/water)\b"),
            ("snack", r"\b(jerky|snack\w*|salami|susen\w* maso|tycink\w*|biltong)\b"), ("soup", r"\bpolevk\w*"),
            ("breakfast", r"\b(kase|nakyp\w*|zemlovk\w*|snidan\w*|dezert\w*|vajick\w*|ovesn\w*|musli)\b")]) or "meal")
        num("grams", r"(\d{2,4}) ?g\b", 10, 5000)
        flag("veg", r"\b(vegan\w*|vegetar\w*|veggie)\b")
    if category == "melee":
        tag("meleetype", _first(t, [("training", r"\b(trenin\w*|training|plast\w* nuz|gumov\w*|rubber)\b"),
                                    ("sharpener", r"\b(ocilk\w*|brous\w*|sharpen\w*)\b"), ("bayonet", r"\bbajonet\w*"),
                                    ("baton", r"\b(obus\w*|baton)\b"), ("machete", r"\b(macet\w*|machete\w*|kukri)\b"),
                                    ("axe", r"\b(sekyr\w*|sekerk\w*|tomahawk\w*|axe)\b"), ("sword", r"\b(mec|mece|katan\w*|sword\w*|sabl\w*|wakizashi)\b"),
                                    ("accessory", r"\b(pochv\w*|pouzdr\w*|zaves\w*|sheath)\b"), ("knife", r"\b(nuz|noze|nozem|knife|knives|karambit\w*|dyk\w*)\b")]))
        flag("folding", r"\b(zaviraci|folding|skladaci|zavirak)\b")
    if category == "bows":
        tag("bowtype", _first(t, [("strings", r"\b(tetiv\w*|lanov\w*|string\w*)\b"), ("tips", r"\bhrot\b"),
                                  ("arrows", r"\b(sip|sipy|sipu|arrow\w*|bolt\w*|sipk\w*)\b"),
                                  ("crossbow", r"\b(kuse|kusi|crossbow\w*)\b"), ("slingshot", r"\bprak\w*"), ("blowgun", r"\bfoukack\w*"),
                                  ("bow", r"\b(luk|luky|lukem|bow|recurve|compound)\b")]) or "accessory")
        num("lbs", r"(\d{2,3}) ?(lb|lbs|liber)\b", 5, 300)
        num("pcs", r"(\d{1,3}) ?(ks|pcs|kusu)\b", 1, 500)
    if category == "targets":
        tag("targettype", _first(t, [("electronic", r"\b(elektron\w*|bluetooth|electronic|bada bang)\b"), ("trap", r"\b(lapac\w*|trap)\b"),
                                     ("gallery", r"\bstrelnic\w*"), ("stand", r"\b(stojan\w*|drzak\w*|stand|holder)\b"),
                                     ("steel", r"\b(ocel\w*|steel|popper\w*|kovov\w*)\b"), ("paper", r"\b(terc\w*|target\w*)\b")]))
        num("pcs", r"(\d{1,4}) ?(ks|pcs|kusu)\b", 1, 5000)
    if category == "cables":
        tags += [f"conn:{v}" for v in _batt_conn(t)]
    return list(dict.fromkeys(tags)), n


def _batt_conn(t: str) -> list[str]:
    found = _all(t, [("deans", r"\b(t-?dean\w*|dean\w*-?t?|deans|t-?plug)\b"),
                     ("tamiya-mini", r"\b(mini ?tamiya|tamiya mini|mal[ay]\w* (tamiya|konektor)|tamiya mal\w*|small tamiya|mini konektor)"),
                     ("tamiya-large", r"\b(large ?tamiya|tamiya large|velk[ay]\w* (tamiya|konektor)|tamiya velk\w*)"),
                     ("xt", r"\bxt-?(30|60|90)\b"), ("jst", r"\bjst\b"), ("usb", r"\busb\w*")])
    if "tamiya" in t and not any(v.startswith("tamiya") for v in found):
        found.append("tamiya")
    return found


def meta_defs() -> dict:
    """What the browser needs to build the filters: definitions, tabs, and which category uses what."""
    defs = {}
    for pid, d in P.items():
        out = {"k": d["kind"], "l": d["label"], "s": d["sec"]}
        for key, short in (("url", "u"), ("tag", "t"), ("unit", "un"), ("vp", "vp"), ("fmt", "f")):
            if key in d:
                out[short] = d[key]
        if "values" in d:
            out["v"] = d["values"]
        defs[pid] = out
    cats = {}
    for cat, plist in CATEGORY_PARAMS.items():
        cats[cat] = {"b": [p.rstrip("*") for p in plist if p.endswith("*")], "a": [p.rstrip("*") for p in plist] + COMMON}
    from .categories import GROUPS
    for g, (_, _, subs) in GROUPS.items():
        allp = list(dict.fromkeys(p for s in subs for p in cats.get(s, {"a": []})["a"]))
        cats[g] = {"b": GROUP_BASIC.get(g, []), "a": allp or COMMON}
    return {"params": defs, "paramSections": SECTIONS, "catParams": cats}
