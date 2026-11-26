"use strict";
(() => {
  const SITE = JSON.parse(document.getElementById("site-config").textContent);
  const { groups: GROUPS, groupOf: GROUP_OF, icons: ICONS, currency: CUR, cats: CATS } = SITE;
  const V = document.documentElement.dataset.v;
  const app = document.getElementById("app");
  const PAGE_SIZE = 48;
  const LANGS = ["cs", "sk", "en", "de"];

  // ---------------------------------------------------------------- translations
  const T = {
    en: {
      "search.ph": "Search guns, magazines, red dots…", "search.btn": "Search", "nav.shops": "Shops", loading: "Loading…",
      "foot.about": "Compare airsoft prices across Czech shops in one place.", "foot.browse": "Browse", "foot.know": "Good to know",
      "foot.disclaimer": "Prices are read from each shop's public feed or product pages and may be out of date. Always check the shop before buying.",
      updated: "Prices last updated {d}.", all: "All products", "sec.most": "Compared in the most shops", "sec.diff": "Biggest price differences",
      "nf.title": "Page not found", "nf.home": "Back to the homepage", home: "Home",
      "hero.title": "Find the cheapest airsoft gear", "hero.text": "We compare <b>{offers}</b> offers from <b>{shops}</b> airsoft shops, so you don't have to open every one.",
      "stat.products": "products", "stat.compared": "compared across shops", "stat.shops": "shops", categories: "Categories",
      nprod: "{n} products", nprod1: "1 product", browseAll: "Browse all {n} products", showAll: "Show all ›",
      filters: "Filters", price: "Price", from: "from", to: "to", avail: "Availability", inStockOnly: "In stock only", clear: "Clear filters",
      showMore: "Show more", showLess: "Show less", any: "Any", allOf: "All", results: "Show {n} products",
      "sort.relevance": "Most compared", "sort.price_asc": "Cheapest", "sort.price_desc": "Most expensive", "sort.savings": "Biggest saving", "sort.name": "Name",
      prev: "‹ Previous", next: "Next ›", pageOf: "Page {p} of {n}", nothing: "Nothing matches these filters.",
      inStock: "In stock", inStockOf: "In stock · {k} of {s} shops", outOfStock: "Out of stock", fromP: "from", compareN: "Compare {n} shops ›", oneShop: "1 shop",
      compareOffers: "Compare {n} offers", compareOffer: "Compare 1 offer", priceCmp: "Price comparison", priceHist: "Price history", similar: "Similar products",
      brand: "Brand", category: "Category", upTo: "up to {v}", save: "save", inStockAt: "In stock at {k} of {s} shops", outEverywhere: "Out of stock everywhere",
      removed: "Removed", unknown: "Availability unknown", goShop: "Go to shop", cheapest: "Cheapest",
      "pnf.title": "Product not found", "pnf.text": "It may have been merged with another listing after the last update.", "pnf.link": "Search for it on the homepage",
      "shops.title": "Shops we compare", nshops: "{n} shops", offersLbl: "offers", cheapestOn: "cheapest on", updatedLbl: "Updated {d}", feed: "feed", crawled: "crawled",
      showProducts: "Show products", failed: "Update failed", upToDate: "Up to date", pending: "Loading…",
      cheapestNote: "“Cheapest on” counts products that this shop sells for the lowest price among the shops that carry it.",
      loadError: "Couldn't load the data. Please refresh the page.",
      "f.minshops": "Sold in", "f.save": "Saving at least", "f.brand": "Brand", "f.color": "Colour", "f.power": "Power source", "f.material": "Material",
      "f.cap": "Magazine type", "f.bbw": "BB weight", "f.shop": "Shop", shopsPlus: "{n}+ shops",
      "pw.electric": "Electric (AEG)", "pw.gas": "Gas (GBB)", "pw.co2": "CO2", "pw.hpa": "HPA", "pw.spring": "Spring / manual",
      "mt.metal": "Metal", "mt.plastic": "Plastic / ABS", "cap.low": "Low-cap", "cap.mid": "Mid-cap", "cap.hi": "Hi-cap", "cap.real": "Real-cap",
      "col.black": "Black", "col.green": "Green", "col.olive": "Olive", "col.tan": "Tan", "col.brown": "Brown", "col.grey": "Grey", "col.white": "White",
      "col.red": "Red", "col.blue": "Blue", "col.pink": "Pink", "col.orange": "Orange", "col.camo": "Camo",
      "theme": "Dark / light mode", lang: "Language", privacy: "Privacy", zoom: "Show the original photo", showEmail: "Show email address",
    },
    cs: {
      "search.ph": "Hledat zbraně, zásobníky, kolimátory…", "search.btn": "Hledat", "nav.shops": "Obchody", loading: "Načítání…",
      "foot.about": "Porovnání cen airsoftu napříč českými obchody na jednom místě.", "foot.browse": "Procházet", "foot.know": "Dobré vědět",
      "foot.disclaimer": "Ceny čteme z veřejných feedů a stránek obchodů a nemusí být aktuální. Před nákupem vždy ověřte cenu v obchodě.",
      updated: "Ceny naposledy aktualizovány {d}.", all: "Všechny produkty", "sec.most": "Porovnáno v nejvíce obchodech", "sec.diff": "Největší rozdíly v cenách",
      "nf.title": "Stránka nenalezena", "nf.home": "Zpět na úvod", home: "Úvod",
      "hero.title": "Najděte nejlevnější airsoftové vybavení", "hero.text": "Porovnáváme <b>{offers}</b> nabídek z <b>{shops}</b> airsoftových obchodů, abyste nemuseli procházet každý zvlášť.",
      "stat.products": "produktů", "stat.compared": "porovnáno mezi obchody", "stat.shops": "obchodů", categories: "Kategorie",
      nprod: "{n} produktů", nprod1: "1 produkt", browseAll: "Zobrazit všech {n} produktů", showAll: "Zobrazit vše ›",
      filters: "Filtry", price: "Cena", from: "od", to: "do", avail: "Dostupnost", inStockOnly: "Pouze skladem", clear: "Zrušit filtry",
      showMore: "Zobrazit více", showLess: "Zobrazit méně", any: "Libovolně", allOf: "Vše", results: "Zobrazit {n} produktů",
      "sort.relevance": "Nejvíce porovnávané", "sort.price_asc": "Nejlevnější", "sort.price_desc": "Nejdražší", "sort.savings": "Největší úspora", "sort.name": "Název",
      prev: "‹ Předchozí", next: "Další ›", pageOf: "Strana {p} z {n}", nothing: "Těmto filtrům nic neodpovídá.",
      inStock: "Skladem", inStockOf: "Skladem · {k} z {s} obchodů", outOfStock: "Není skladem", fromP: "od", compareN: "Porovnat {n} obchodů ›", oneShop: "1 obchod",
      compareOffers: "Porovnat {n} nabídek", compareOffer: "Zobrazit nabídku", priceCmp: "Porovnání cen", priceHist: "Vývoj ceny", similar: "Podobné produkty",
      brand: "Značka", category: "Kategorie", upTo: "až {v}", save: "ušetříte", inStockAt: "Skladem v {k} z {s} obchodů", outEverywhere: "Nikde skladem",
      removed: "Odstraněno", unknown: "Dostupnost neznámá", goShop: "Do obchodu", cheapest: "Nejlevnější",
      "pnf.title": "Produkt nenalezen", "pnf.text": "Po poslední aktualizaci mohl být sloučen s jinou nabídkou.", "pnf.link": "Vyhledejte ho na úvodní stránce",
      "shops.title": "Obchody, které porovnáváme", nshops: "{n} obchodů", offersLbl: "nabídek", cheapestOn: "nejlevnější u", updatedLbl: "Aktualizováno {d}", feed: "feed", crawled: "procházeno",
      showProducts: "Zobrazit produkty", failed: "Aktualizace selhala", upToDate: "Aktuální", pending: "Načítá se…",
      cheapestNote: "„Nejlevnější u“ udává, u kolika produktů má obchod nejnižší cenu ze všech obchodů, které je prodávají.",
      loadError: "Data se nepodařilo načíst. Obnovte prosím stránku.",
      "f.minshops": "Prodává", "f.save": "Úspora alespoň", "f.brand": "Značka", "f.color": "Barva", "f.power": "Pohon", "f.material": "Materiál",
      "f.cap": "Typ zásobníku", "f.bbw": "Gramáž kuliček", "f.shop": "Obchod", shopsPlus: "{n}+ obchodů",
      "pw.electric": "Elektrický (AEG)", "pw.gas": "Plynový (GBB)", "pw.co2": "CO2", "pw.hpa": "HPA", "pw.spring": "Pružinový / manuální",
      "mt.metal": "Kov", "mt.plastic": "Plast / ABS", "cap.low": "Low-cap", "cap.mid": "Mid-cap", "cap.hi": "Hi-cap", "cap.real": "Real-cap",
      "col.black": "Černá", "col.green": "Zelená", "col.olive": "Olivová", "col.tan": "Písková", "col.brown": "Hnědá", "col.grey": "Šedá", "col.white": "Bílá",
      "col.red": "Červená", "col.blue": "Modrá", "col.pink": "Růžová", "col.orange": "Oranžová", "col.camo": "Maskáčová",
      "theme": "Tmavý / světlý režim", lang: "Jazyk", privacy: "Ochrana soukromí", zoom: "Zobrazit původní fotku", showEmail: "Zobrazit e-mail",
    },
    sk: {
      "search.ph": "Hľadať zbrane, zásobníky, kolimátory…", "search.btn": "Hľadať", "nav.shops": "Obchody", loading: "Načítava sa…",
      "foot.about": "Porovnanie cien airsoftu naprieč českými obchodmi na jednom mieste.", "foot.browse": "Prehliadať", "foot.know": "Dobré vedieť",
      "foot.disclaimer": "Ceny čítame z verejných feedov a stránok obchodov a nemusia byť aktuálne. Pred nákupom vždy overte cenu v obchode.",
      updated: "Ceny naposledy aktualizované {d}.", all: "Všetky produkty", "sec.most": "Porovnané v najviac obchodoch", "sec.diff": "Najväčšie rozdiely v cenách",
      "nf.title": "Stránka sa nenašla", "nf.home": "Späť na úvod", home: "Úvod",
      "hero.title": "Nájdite najlacnejšie airsoftové vybavenie", "hero.text": "Porovnávame <b>{offers}</b> ponúk z <b>{shops}</b> airsoftových obchodov, aby ste nemuseli prechádzať každý zvlášť.",
      "stat.products": "produktov", "stat.compared": "porovnaných medzi obchodmi", "stat.shops": "obchodov", categories: "Kategórie",
      nprod: "{n} produktov", nprod1: "1 produkt", browseAll: "Zobraziť všetkých {n} produktov", showAll: "Zobraziť všetko ›",
      filters: "Filtre", price: "Cena", from: "od", to: "do", avail: "Dostupnosť", inStockOnly: "Iba skladom", clear: "Zrušiť filtre",
      showMore: "Zobraziť viac", showLess: "Zobraziť menej", any: "Ľubovoľne", allOf: "Všetko", results: "Zobraziť {n} produktov",
      "sort.relevance": "Najviac porovnávané", "sort.price_asc": "Najlacnejšie", "sort.price_desc": "Najdrahšie", "sort.savings": "Najväčšia úspora", "sort.name": "Názov",
      prev: "‹ Predchádzajúca", next: "Ďalšia ›", pageOf: "Strana {p} z {n}", nothing: "Týmto filtrom nič nezodpovedá.",
      inStock: "Skladom", inStockOf: "Skladom · {k} z {s} obchodov", outOfStock: "Nie je skladom", fromP: "od", compareN: "Porovnať {n} obchodov ›", oneShop: "1 obchod",
      compareOffers: "Porovnať {n} ponúk", compareOffer: "Zobraziť ponuku", priceCmp: "Porovnanie cien", priceHist: "Vývoj ceny", similar: "Podobné produkty",
      brand: "Značka", category: "Kategória", upTo: "až {v}", save: "ušetríte", inStockAt: "Skladom v {k} z {s} obchodov", outEverywhere: "Nikde skladom",
      removed: "Odstránené", unknown: "Dostupnosť neznáma", goShop: "Do obchodu", cheapest: "Najlacnejšie",
      "pnf.title": "Produkt sa nenašiel", "pnf.text": "Po poslednej aktualizácii mohol byť zlúčený s inou ponukou.", "pnf.link": "Vyhľadajte ho na úvodnej stránke",
      "shops.title": "Obchody, ktoré porovnávame", nshops: "{n} obchodov", offersLbl: "ponúk", cheapestOn: "najlacnejšie pri", updatedLbl: "Aktualizované {d}", feed: "feed", crawled: "prechádzané",
      showProducts: "Zobraziť produkty", failed: "Aktualizácia zlyhala", upToDate: "Aktuálne", pending: "Načítava sa…",
      cheapestNote: "„Najlacnejšie pri“ udáva, pri koľkých produktoch má obchod najnižšiu cenu zo všetkých obchodov, ktoré ich predávajú.",
      loadError: "Dáta sa nepodarilo načítať. Obnovte prosím stránku.",
      "f.minshops": "Predáva", "f.save": "Úspora aspoň", "f.brand": "Značka", "f.color": "Farba", "f.power": "Pohon", "f.material": "Materiál",
      "f.cap": "Typ zásobníka", "f.bbw": "Gramáž guličiek", "f.shop": "Obchod", shopsPlus: "{n}+ obchodov",
      "pw.electric": "Elektrický (AEG)", "pw.gas": "Plynový (GBB)", "pw.co2": "CO2", "pw.hpa": "HPA", "pw.spring": "Pružinový / manuálny",
      "mt.metal": "Kov", "mt.plastic": "Plast / ABS", "cap.low": "Low-cap", "cap.mid": "Mid-cap", "cap.hi": "Hi-cap", "cap.real": "Real-cap",
      "col.black": "Čierna", "col.green": "Zelená", "col.olive": "Olivová", "col.tan": "Piesková", "col.brown": "Hnedá", "col.grey": "Sivá", "col.white": "Biela",
      "col.red": "Červená", "col.blue": "Modrá", "col.pink": "Ružová", "col.orange": "Oranžová", "col.camo": "Maskáčová",
      "theme": "Tmavý / svetlý režim", lang: "Jazyk", privacy: "Ochrana súkromia", zoom: "Zobraziť pôvodnú fotku", showEmail: "Zobraziť e-mail",
    },
    de: {
      "search.ph": "Waffen, Magazine, Red Dots suchen…", "search.btn": "Suchen", "nav.shops": "Shops", loading: "Wird geladen…",
      "foot.about": "Airsoft-Preise tschechischer Shops an einem Ort vergleichen.", "foot.browse": "Stöbern", "foot.know": "Gut zu wissen",
      "foot.disclaimer": "Die Preise stammen aus öffentlichen Feeds und Produktseiten der Shops und können veraltet sein. Bitte vor dem Kauf im Shop prüfen.",
      updated: "Preise zuletzt aktualisiert am {d}.", all: "Alle Produkte", "sec.most": "In den meisten Shops verglichen", "sec.diff": "Größte Preisunterschiede",
      "nf.title": "Seite nicht gefunden", "nf.home": "Zur Startseite", home: "Start",
      "hero.title": "Finde die günstigste Airsoft-Ausrüstung", "hero.text": "Wir vergleichen <b>{offers}</b> Angebote aus <b>{shops}</b> Airsoft-Shops, damit du nicht jeden einzeln öffnen musst.",
      "stat.products": "Produkte", "stat.compared": "shopübergreifend verglichen", "stat.shops": "Shops", categories: "Kategorien",
      nprod: "{n} Produkte", nprod1: "1 Produkt", browseAll: "Alle {n} Produkte anzeigen", showAll: "Alle anzeigen ›",
      filters: "Filter", price: "Preis", from: "von", to: "bis", avail: "Verfügbarkeit", inStockOnly: "Nur auf Lager", clear: "Filter zurücksetzen",
      showMore: "Mehr anzeigen", showLess: "Weniger anzeigen", any: "Beliebig", allOf: "Alle", results: "{n} Produkte anzeigen",
      "sort.relevance": "Meist verglichen", "sort.price_asc": "Günstigste", "sort.price_desc": "Teuerste", "sort.savings": "Größte Ersparnis", "sort.name": "Name",
      prev: "‹ Zurück", next: "Weiter ›", pageOf: "Seite {p} von {n}", nothing: "Keine Produkte passen zu diesen Filtern.",
      inStock: "Auf Lager", inStockOf: "Auf Lager · {k} von {s} Shops", outOfStock: "Nicht auf Lager", fromP: "ab", compareN: "{n} Shops vergleichen ›", oneShop: "1 Shop",
      compareOffers: "{n} Angebote vergleichen", compareOffer: "Angebot ansehen", priceCmp: "Preisvergleich", priceHist: "Preisverlauf", similar: "Ähnliche Produkte",
      brand: "Marke", category: "Kategorie", upTo: "bis {v}", save: "Ersparnis", inStockAt: "Auf Lager in {k} von {s} Shops", outEverywhere: "Überall ausverkauft",
      removed: "Entfernt", unknown: "Verfügbarkeit unbekannt", goShop: "Zum Shop", cheapest: "Günstigster",
      "pnf.title": "Produkt nicht gefunden", "pnf.text": "Es wurde nach dem letzten Update eventuell mit einem anderen Angebot zusammengeführt.", "pnf.link": "Auf der Startseite suchen",
      "shops.title": "Verglichene Shops", nshops: "{n} Shops", offersLbl: "Angebote", cheapestOn: "am günstigsten bei", updatedLbl: "Aktualisiert {d}", feed: "Feed", crawled: "gecrawlt",
      showProducts: "Produkte anzeigen", failed: "Update fehlgeschlagen", upToDate: "Aktuell", pending: "Wird geladen…",
      cheapestNote: "„Am günstigsten bei“ zählt die Produkte, die dieser Shop unter allen Anbietern am günstigsten verkauft.",
      loadError: "Daten konnten nicht geladen werden. Bitte Seite neu laden.",
      "f.minshops": "Erhältlich in", "f.save": "Ersparnis mindestens", "f.brand": "Marke", "f.color": "Farbe", "f.power": "Antrieb", "f.material": "Material",
      "f.cap": "Magazintyp", "f.bbw": "BB-Gewicht", "f.shop": "Shop", shopsPlus: "{n}+ Shops",
      "pw.electric": "Elektrisch (AEG)", "pw.gas": "Gas (GBB)", "pw.co2": "CO2", "pw.hpa": "HPA", "pw.spring": "Feder / manuell",
      "mt.metal": "Metall", "mt.plastic": "Kunststoff / ABS", "cap.low": "Low-Cap", "cap.mid": "Mid-Cap", "cap.hi": "Hi-Cap", "cap.real": "Real-Cap",
      "col.black": "Schwarz", "col.green": "Grün", "col.olive": "Oliv", "col.tan": "Tan", "col.brown": "Braun", "col.grey": "Grau", "col.white": "Weiß",
      "col.red": "Rot", "col.blue": "Blau", "col.pink": "Rosa", "col.orange": "Orange", "col.camo": "Tarn",
      "theme": "Dunkel / hell", lang: "Sprache", privacy: "Datenschutz", zoom: "Originalfoto anzeigen", showEmail: "E-Mail-Adresse anzeigen",
    },
  };
  const CAT_NAMES = {
    // order: en, cs, sk, de
    weapons: ["Guns", "Zbraně", "Zbrane", "Waffen"], ammo: ["Magazines, BBs & gas", "Zásobníky, kuličky a plyn", "Zásobníky, guličky a plyn", "Magazine, BBs & Gas"],
    sights: ["Optics & lights", "Optika a svítilny", "Optika a svietidlá", "Optik & Licht"], upgrades: ["Parts & accessories", "Díly a příslušenství", "Diely a príslušenstvo", "Teile & Zubehör"],
    gear: ["Tactical gear", "Taktická výstroj", "Taktická výstroj", "Taktische Ausrüstung"], protection: ["Protection", "Ochrana", "Ochrana", "Schutz"],
    apparel: ["Clothing & boots", "Oblečení a obuv", "Oblečenie a obuv", "Kleidung & Schuhe"], misc: ["Other", "Ostatní", "Ostatné", "Sonstiges"],
    guns: ["Rifles & SMGs", "Útočné pušky a samopaly", "Útočné pušky a samopaly", "Gewehre & MPs"], pistols: ["Pistols & revolvers", "Pistole a revolvery", "Pištole a revolvery", "Pistolen & Revolver"],
    snipers: ["Sniper rifles", "Odstřelovací pušky", "Odstreľovacie pušky", "Scharfschützengewehre"], shotguns: ["Shotguns", "Brokovnice", "Brokovnice", "Schrotflinten"],
    magazines: ["Magazines", "Zásobníky", "Zásobníky", "Magazine"], bbs: ["BBs", "Kuličky", "Guličky", "BBs"], gas: ["Gas & CO2", "Plyn a CO2", "Plyn a CO2", "Gas & CO2"],
    optics: ["Optics & red dots", "Optika a kolimátory", "Optika a kolimátory", "Optiken & Red Dots"], lights: ["Lights & lasers", "Svítilny a lasery", "Svietidlá a lasery", "Lampen & Laser"],
    parts: ["Parts & upgrades", "Díly a upgrady", "Diely a upgrady", "Teile & Tuning"], batteries: ["Batteries", "Baterie", "Batérie", "Akkus"], chargers: ["Chargers", "Nabíječky", "Nabíjačky", "Ladegeräte"],
    vests: ["Vests & plate carriers", "Vesty a nosiče plátů", "Vesty a nosiče plátov", "Westen & Plattenträger"], pouches: ["Pouches & bags", "Sumky a tašky", "Sumky a tašky", "Taschen & Rucksäcke"],
    holsters: ["Holsters", "Pouzdra", "Puzdrá", "Holster"], slings: ["Slings", "Popruhy", "Popruhy", "Tragegurte"],
    masks: ["Masks", "Masky", "Masky", "Masken"], eyewear: ["Goggles & glasses", "Brýle", "Okuliare", "Schutzbrillen"], helmets: ["Helmets", "Helmy", "Prilby", "Helme"], gloves: ["Gloves", "Rukavice", "Rukavice", "Handschuhe"],
    clothing: ["Clothing & boots", "Oblečení a obuv", "Oblečenie a obuv", "Kleidung & Schuhe"],
    comms: ["Radios & headsets", "Vysílačky a headsety", "Vysielačky a headsety", "Funk & Headsets"], grenades: ["Grenades & pyro", "Granáty a pyro", "Granáty a pyro", "Granaten & Pyro"],
    other: ["Other", "Ostatní", "Ostatné", "Sonstiges"],
  };
  let lang = LANGS.includes(document.documentElement.lang) ? document.documentElement.lang : "en";
  const t = (key, vars) => {
    let s = (T[lang] && T[lang][key]) ?? T.en[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v);
    return s;
  };
  const catName = (slug) => (CAT_NAMES[slug] || CAT_NAMES.other)[["en", "cs", "sk", "de"].indexOf(lang)];
  const nprod = (n) => (n === 1 ? t("nprod1") : t("nprod", { n: fmt(n) }));

  // ---------------------------------------------------------------- helpers
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cache = {};
  const json = (u) => (cache[u] ||= fetch(`${u}?v=${V}`).then((r) => { if (!r.ok) throw new Error(`${u}: ${r.status}`); return r.json(); }));
  const fold = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const fmt = (n) => Math.round(n).toLocaleString("cs-CZ").replace(/\s/g, " ");
  const money = (v) => {
    if (v == null) return "–";
    const s = CUR === "CZK" ? fmt(v) : v.toLocaleString("cs-CZ", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return s + ({ CZK: " Kč", EUR: " €", PLN: " zł" }[CUR] || " " + CUR);
  };
  const icon = (name, cls = "ic") => `<svg class="${cls}"><use href="#i-${name}"/></svg>`;
  const groupIcon = (c) => icon(ICONS[GROUP_OF[c] || c] || "image", "ph");
  const P = () => new URLSearchParams(location.search);
  const url = (over) => {
    const p = P();
    for (const [k, v] of Object.entries(over)) (v === "" || v == null) ? p.delete(k) : p.set(k, v);
    const s = p.toString();
    return "/" + (s ? "?" + s : "");
  };
  // Only categories the site defines; anything else from the address bar is ignored.
  const knownCat = (v) => (v && (GROUPS[v] || CATS[v]) ? v : "");
  const list = (p, k) => (p.get(k) || "").split(",").filter(Boolean);

  // ---------------------------------------------------------------- shell: language, theme
  function applyShell() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
    document.querySelectorAll(".catbar [data-group] span").forEach((el) => { el.textContent = catName(el.parentElement.dataset.group); });
    const sel = document.getElementById("lang");
    sel.value = lang; sel.setAttribute("aria-label", t("lang"));
    document.getElementById("theme").setAttribute("aria-label", t("theme"));
  }
  const store = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } };
  document.getElementById("lang").addEventListener("change", (e) => {
    lang = e.target.value; store("lang", lang); applyShell(); route();
  });
  document.getElementById("theme").addEventListener("click", () => {
    const d = document.documentElement;
    const dark = d.dataset.theme ? d.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    d.dataset.theme = dark ? "light" : "dark"; store("theme", d.dataset.theme);
  });

  // ---------------------------------------------------------------- pieces
  function card(p) {
    const save = p.s > 1 && p.x > p.p ? `<span class="badge-save">−${Math.round((1 - p.p / p.x) * 100)} %</span>` : "";
    const stock = p.k ? `<div class="stock yes">${p.s > 1 ? t("inStockOf", { k: p.k, s: p.s }) : t("inStock")}</div>` : `<div class="stock no">${t("outOfStock")}</div>`;
    return `<a class="card" href="/product/${p.id}">
      <div class="thumb">${groupIcon(p.c)}${p.i ? `<img src="${esc(p.i)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ""}${save}</div>
      <div class="card-body">
        ${p.b ? `<div class="card-brand">${esc(p.b)}</div>` : ""}<div class="name">${esc(p.t)}</div>${stock}
        <div class="price-row"><div class="price">${p.s > 1 ? `<small>${t("fromP")}</small> ` : ""}${money(p.p)}</div></div>
        <div class="cmp ${p.s > 1 ? "multi" : ""}">${p.s > 1 ? t("compareN", { n: p.s }) : t("oneShop")}</div>
      </div></a>`;
  }
  const row = (title, more, items) => items.length ? `
    <div class="sec-head"><h2 class="sec-title">${esc(title)}</h2>${more ? `<a href="${more}">${t("showAll")}</a>` : ""}</div>
    <div class="row-one">${items.map(card).join("")}</div>` : "";
  const markGroup = (g) => document.querySelectorAll(".catbar a").forEach((a) => a.classList.toggle("on", a.dataset.group === g));

  // ---------------------------------------------------------------- home
  // On the homepage the category bar slides in only once the category tiles have scrolled away.
  let tilesObserver = null;
  function catbarFollow(target) {
    const top = document.querySelector(".top");
    if (tilesObserver) { tilesObserver.disconnect(); tilesObserver = null; }
    if (!target || !("IntersectionObserver" in window)) {
      top.classList.remove("cats-hidden"); document.documentElement.classList.remove("home-start"); return;
    }
    tilesObserver = new IntersectionObserver(([entry]) => {
      top.classList.toggle("cats-hidden", entry.isIntersecting);
      document.documentElement.classList.remove("home-start");
    }, { threshold: 0 });
    tilesObserver.observe(target);
  }
  function home(m) {
    markGroup(null);
    document.title = `CompAirsoft – ${t("hero.title")}`;
    const tiles = Object.entries(GROUPS).map(([g, [, , subs]]) => {
      const total = subs.reduce((n, s) => n + (m.counts[s] || 0), 0);
      if (!total) return "";

      const links = subs.length > 1 ? `<div class="tile-subs">${subs.filter((s) => m.counts[s]).map((s) => `<a href="/?cat=${s}">${esc(catName(s))}</a>`).join("")}</div>` : "";
      return `<div class="tile"><a class="tile-main" href="/?cat=${g}">
<span class="tile-img"><svg class="illu" viewBox="0 0 160 90" aria-hidden="true"><use href="#cat-${g}"/></svg></span>
          <span class="tile-text"><span class="tile-name">${esc(catName(g))}</span><span class="tile-n">${nprod(total)}</span></span></a>${links}</div>`;
    }).join("");
    const titles = { "Compared in the most shops": t("sec.most"), "Biggest price differences": t("sec.diff") };
    app.innerHTML = `
      <section class="hero"><div><h1>${t("hero.title")}</h1><p>${t("hero.text", { offers: fmt(m.stats.offers), shops: m.stats.shops })}</p></div>
        <div class="hero-stats"><div><b>${fmt(m.stats.products)}</b><span>${t("stat.products")}</span></div>
          <div><b>${fmt(m.stats.compared)}</b><span>${t("stat.compared")}</span></div><div><b>${m.stats.shops}</b><span>${t("stat.shops")}</span></div></div></section>
      <div class="hero-cats"><h2 class="sec-title">${t("categories")}</h2><section class="tiles">${tiles}</section></div>
      ${m.sections.map((s) => row(titles[s.title] || s.title, s.more, s.items)).join("")}
      <div class="center"><a class="btn btn-big" href="/?all=1">${t("browseAll", { n: fmt(m.stats.products) })}</a></div>`;
    catbarFollow(app.querySelector(".hero-cats"));
  }

  // ---------------------------------------------------------------- listing with facets
  function matcher(q, syn) {
    const words = fold(q).split(/[^a-z0-9.]+/).filter(Boolean);
    const alts = words.map((w) => [w, ...(syn[w] || [])]);
    return (p) => { const s = (p._f ||= fold(p.t + " " + (p.b || ""))); return alts.every((o) => o.some((x) => s.includes(x))); };
  }
  const tagVals = (prefix) => (p) => (p.a || []).filter((x) => x.startsWith(prefix)).map((x) => x.slice(prefix.length));
  // name, url param, values of a product, label of a value
  const FACETS = [
    ["brand", "brand", (p) => (p.b ? [p.b] : []), (v) => v],
    ["power", "power", tagVals("pw:"), (v) => t("pw." + v)],
    ["material", "material", tagVals("mt:"), (v) => t("mt." + v)],
    ["cap", "cap", tagVals("cap:"), (v) => t("cap." + v)],
    ["bbw", "bbw", tagVals("bbw:"), (v) => v.replace(".", ",") + " g"],
    ["color", "color", tagVals("col:"), (v) => t("col." + v) !== "col." + v ? t("col." + v) : v[0].toUpperCase() + v.slice(1)],
    ["shop", "shop", (p) => p.h.map(String), null],
  ];
  let itemsCache = { key: null, items: [] };
  async function loadItems(group) {
    const key = group || "*";
    if (itemsCache.key !== key) {
      const files = group ? [group] : Object.keys(GROUPS);
      itemsCache = { key, items: (await Promise.all(files.map((g) => json(`/data/g/${g}.json`)))).flat() };
    }
    return itemsCache.items;
  }

  async function listing(m) {
    const p = P();
    const q = p.get("q") || "", c = knownCat(p.get("cat"));
    const group = GROUPS[c] ? c : GROUP_OF[c];
    const stock = p.has("stock");
    const minShops = Math.max(+p.get("minshops") || 0, p.has("multi") ? 2 : 0);
    const minSave = +p.get("save") || 0;
    const pmin = parseFloat(p.get("pmin")), pmax = parseFloat(p.get("pmax"));
    const sort = p.get("sort") || "relevance", page = Math.max(1, +p.get("page") || 1);
    markGroup(group);
    document.querySelector(".search input").value = q;
    if (itemsCache.key !== (group || "*")) app.innerHTML = `<div class="loading">${t("loading")}</div>`;

    let base = await loadItems(group);
    if (c && !GROUPS[c]) base = base.filter((x) => x.c === c);
    if (q) base = base.filter(matcher(q, m.syn));
    if (stock) base = base.filter((x) => x.k > 0);
    if (minShops) base = base.filter((x) => x.s >= minShops);
    if (minSave) base = base.filter((x) => x.s > 1 && x.x > 0 && (1 - x.p / x.x) * 100 >= minSave);
    if (!isNaN(pmin)) base = base.filter((x) => x.p >= pmin);
    if (!isNaN(pmax)) base = base.filter((x) => x.p <= pmax);

    const chosen = Object.fromEntries(FACETS.map(([n, k]) => [n, new Set(list(p, k))]));
    const passes = (x, except) => FACETS.every(([n, , vals]) => n === except || !chosen[n].size || vals(x).some((v) => chosen[n].has(v)));
    const items = base.filter((x) => passes(x, null));
    const facetCounts = Object.fromEntries(FACETS.map(([n, , vals]) => {
      const cnt = new Map();
      for (const x of base) if (passes(x, n)) for (const v of new Set(vals(x))) cnt.set(v, (cnt.get(v) || 0) + 1);
      return [n, cnt];
    }));

    const by = {
      relevance: (a, b) => b.s - a.s || a.p - b.p, shops: (a, b) => b.s - a.s || a.p - b.p, price_asc: (a, b) => a.p - b.p, price_desc: (a, b) => b.p - a.p,
      savings: (a, b) => (b.x - b.p) - (a.x - a.p), name: (a, b) => a.t.localeCompare(b.t, lang),
    }[sort] || ((a, b) => b.s - a.s || a.p - b.p);
    items.sort(by);
    const total = items.length, pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const shown = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
    const shopName = Object.fromEntries(m.shops.map((s) => [String(s.id), s.name]));

    const facetBox = (name, key, label) => {
      const cnt = facetCounts[name];
      if (!cnt.size || (cnt.size === 1 && !chosen[name].size && name !== "shop")) return "";
      const vals = [...cnt.entries()].sort((a, b) => (chosen[name].has(b[0]) - chosen[name].has(a[0])) || b[1] - a[1]);
      const lbl = FACETS.find((f) => f[0] === name)[3] || ((v) => shopName[v] || v);
      const rows = vals.map(([v, n], i) => {
        const on = chosen[name].has(v);
        const next = new Set(chosen[name]); on ? next.delete(v) : next.add(v);
        return `<a class="opt ${on ? "on" : ""} ${i >= 6 && !on ? "extra" : ""}" href="${url({ [key]: [...next].join(","), page: "" })}">
          <span class="box"></span><span class="opt-l">${esc(lbl(v))}</span><span class="opt-n">${fmt(n)}</span></a>`;
      }).join("");
      const more = vals.length > 6 ? `<button type="button" class="more-btn" data-more>${t("showMore")}</button>` : "";
      return `<div class="f-group" data-facet="${name}"><div class="f-title">${t("f." + name)}</div><div class="opts">${rows}</div>${more}</div>`;
    };
    const radio = (key, cur, options, label) => `<div class="f-group"><div class="f-title">${label}</div><div class="opts">${options.map(([v, l]) =>
      `<a class="opt radio ${String(cur) === String(v) ? "on" : ""}" href="${url({ [key]: v || "", multi: "", page: "" })}"><span class="box"></span><span class="opt-l">${l}</span></a>`).join("")}</div></div>`;
    const active = ["q", "stock", "minshops", "multi", "save", "pmin", "pmax", ...FACETS.map((f) => f[1])].some((k) => p.get(k));

    const title = q ? `“${esc(q)}”` : c ? esc(catName(c)) : t("all");
    document.title = `${q || (c ? catName(c) : t("all"))} – CompAirsoft`;
    const subs = group && GROUPS[group][2].length > 1 ? `<nav class="subcats" aria-label="${esc(catName(group))}">
      <a href="${url({ cat: group, page: "" })}" class="${c === group ? "on" : ""}">${t("allOf")}</a>
      ${GROUPS[group][2].filter((s) => m.counts[s]).map((s) => `<a href="${url({ cat: s, page: "" })}" class="${c === s ? "on" : ""}">${esc(catName(s))} <b>${fmt(m.counts[s])}</b></a>`).join("")}</nav>` : "";
    const keep = (k) => p.get(k) ? `<input type="hidden" name="${k}" value="${esc(p.get(k))}">` : "";
    const open = innerWidth >= 900 ? "open" : "";
    app.innerHTML = `<div class="layout">
      <aside class="filters"><details class="filters-box" ${open}><summary>${icon("sliders-horizontal")} ${t("filters")}</summary>
        ${active ? `<a class="clear" href="${c ? url({}).split("?")[0] + "?cat=" + encodeURIComponent(c) : "/?all=1"}">${icon("x")} ${t("clear")}</a>` : ""}
        <form method="get" action="/" class="f-group">${["q", "cat", "sort", "stock", "minshops", "save", ...FACETS.map((f) => f[1])].map(keep).join("")}<input type="hidden" name="all" value="1">
          <div class="f-title">${t("price")} (${CUR === "CZK" ? "Kč" : CUR})</div><div class="range">
            <input type="number" name="pmin" value="${isNaN(pmin) ? "" : pmin}" min="0" inputmode="numeric" placeholder="${t("from")}" aria-label="${t("price")} ${t("from")}"><span>–</span>
            <input type="number" name="pmax" value="${isNaN(pmax) ? "" : pmax}" min="0" inputmode="numeric" placeholder="${t("to")}" aria-label="${t("price")} ${t("to")}">
            <button class="btn btn-small" type="submit" aria-label="OK">OK</button></div></form>
        <div class="f-group"><div class="f-title">${t("avail")}</div><div class="opts">
          <a class="opt ${stock ? "on" : ""}" href="${url({ stock: stock ? "" : "1", page: "" })}"><span class="box"></span><span class="opt-l">${t("inStockOnly")}</span></a></div></div>
        ${radio("minshops", minShops || "", [["", t("any")], [2, t("shopsPlus", { n: 2 })], [3, t("shopsPlus", { n: 3 })], [4, t("shopsPlus", { n: 4 })]], t("f.minshops"))}
        ${radio("save", minSave || "", [["", t("any")], [10, "10 %"], [20, "20 %"], [30, "30 %"]], t("f.save"))}
        ${FACETS.map(([n, k]) => facetBox(n, k)).join("")}
      </details></aside>
      <section class="results">
        <div class="results-head"><h1>${title}</h1><span class="muted">${nprod(total)}</span></div>
        ${subs}
        <nav class="sort-tabs">${["relevance", "price_asc", "price_desc", "savings", "name"].map((k) => `<a href="${url({ sort: k, page: "" })}" class="${sort === k ? "on" : ""}">${t("sort." + k)}</a>`).join("")}</nav>
        ${total ? `<div class="grid">${shown.map(card).join("")}</div>` : `<div class="empty">${t("nothing")}</div>`}
        ${pages > 1 ? `<nav class="pager">${page > 1 ? `<a href="${url({ page: page - 1 })}">${t("prev")}</a>` : ""}
          <span>${t("pageOf", { p: page, n: pages })}</span>${page < pages ? `<a href="${url({ page: page + 1 })}">${t("next")}</a>` : ""}</nav>` : ""}
      </section></div>`;
  }

  // ---------------------------------------------------------------- product
  const PALETTE = ["#4f9d69", "#d9822b", "#3a7bd5", "#c94f6d", "#8e6cc9", "#2aa7a0", "#b8a12d", "#7a7a7a"];
  function chart(hist) {
    const shops = Object.keys(hist);
    const pts = shops.flatMap((s) => hist[s]);
    const days = [...new Set(pts.map((x) => x[0]))].sort();
    if (days.length < 2) return "";
    const d0 = Date.parse(days[0]), d1 = Date.parse(days[days.length - 1]);
    let lo = Math.min(...pts.map((x) => x[1])), hi = Math.max(...pts.map((x) => x[1]));
    const pad = (hi - lo) * 0.1 || hi * 0.05 || 1; lo -= pad; hi += pad;
    const W = 1000, H = 280, L = 70, R = 12, Tp = 10, B = 26;
    const x = (d) => L + (W - L - R) * (Date.parse(d) - d0) / (d1 - d0), y = (v) => Tp + (H - Tp - B) * (1 - (v - lo) / (hi - lo));
    const lines = shops.map((s, n) => {
      const ser = hist[s]; let d = `M${x(ser[0][0]).toFixed(1)},${y(ser[0][1]).toFixed(1)}`;
      for (let i = 1; i < ser.length; i++) d += `H${x(ser[i][0]).toFixed(1)}V${y(ser[i][1]).toFixed(1)}`;
      const last = ser[ser.length - 1];
      return { s, color: PALETTE[n % PALETTE.length], d, cx: x(last[0]), cy: y(last[1]) };
    });
    const ticks = [0, 1, 2, 3].map((k) => lo + (hi - lo) * k / 3);
    return `<h2 class="sec-title">${t("priceHist")}</h2><div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${t("priceHist")}">
        ${ticks.map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" class="grid-line"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" class="axis">${money(v)}</text>`).join("")}
        <text x="${L}" y="${H - 6}" class="axis">${days[0]}</text><text x="${W - R}" y="${H - 6}" text-anchor="end" class="axis">${days[days.length - 1]}</text>
        ${lines.map((l) => `<path d="${l.d}" fill="none" stroke="${l.color}" stroke-width="2.5" stroke-linejoin="round"/><circle cx="${l.cx}" cy="${l.cy}" r="4" fill="${l.color}"/>`).join("")}
      </svg><div class="legend">${lines.map((l) => `<span><i style="background:${l.color}"></i>${esc(l.s)}</span>`).join("")}</div></div>`;
  }

  async function product() {
    const id = (location.pathname.match(/\/product\/([0-9a-f]+)/) || [])[1] || P().get("id") || "";
    const shard = id ? await json(`/data/p/${id.slice(0, 2)}.json`).catch(() => ({})) : {};
    const d = shard[id];
    if (!d) {
      app.innerHTML = `<div class="empty"><h1>${t("pnf.title")}</h1><p>${t("pnf.text")} <a href="/">${t("pnf.link")}</a>.</p></div>`;
      return;
    }
    const p = d.p, g = GROUP_OF[p.c] || "misc";
    markGroup(g);
    document.title = `${p.t} – ${t("priceCmp")} | CompAirsoft`;
    const live = d.o.filter((o) => o.a);
    const offers = d.o.map((o, i) => {
      const best = i === 0 && o.k !== 0 && o.a;
      const st = !o.a ? `<span class="stock no">${t("removed")}</span>` : o.k === 1 ? `<span class="stock yes">${t("inStock")}</span>`
        : o.k === 0 ? `<span class="stock no">${t("outOfStock")}</span>` : `<span class="stock">${t("unknown")}</span>`;
      const foreign = o.y && o.y !== CUR && o.r != null ? `<small>${o.r.toFixed(2)} ${esc(o.y)}</small>` : "";
      return `<div class="offer ${best ? "best" : ""} ${o.a ? "" : "gone"}">
        <div class="o-shop"><b>${esc(o.s)}</b>${best && d.o.length > 1 ? `<span class="tag">${t("cheapest")}</span>` : ""}<div class="o-title">${esc(o.t)}</div></div>
        <div class="o-stock">${st}</div><div class="o-price">${money(o.v)}${foreign}</div>
        <a class="btn btn-shop" href="${esc(o.u)}" target="_blank" rel="noopener noreferrer nofollow">${t("goShop")}</a></div>`;
    }).join("");
    app.innerHTML = `
      <nav class="crumbs"><a href="/">${t("home")}</a><span>›</span><a href="/?cat=${g}">${esc(catName(g))}</a>${GROUPS[g][2].length > 1 ? `<span>›</span><a href="/?cat=${p.c}">${esc(catName(p.c))}</a>` : ""}</nav>
      <section class="pd"><div class="pd-img">${groupIcon(p.c)}${p.i ? `<button type="button" class="zoom" data-orig="${esc(p.orig || p.i)}" aria-label="${t("zoom")}"><img src="${esc(p.i)}" alt="${esc(p.t)}" referrerpolicy="no-referrer"><span class="zoom-hint">${icon("search")}</span></button>` : ""}</div>
        <div class="pd-info"><h1>${esc(p.t)}</h1>
          <div class="pd-meta">${p.b ? `<span>${t("brand")}: <b>${esc(p.b)}</b></span>` : ""}<span>${t("category")}: <a href="/?cat=${p.c}">${esc(catName(p.c))}</a></span>${p.e ? `<span>EAN: ${esc(p.e)}</span>` : ""}</div>
          <div class="pd-buy"><div>
            <div class="pd-price">${p.s > 1 ? `<small>${t("fromP")}</small> ` : ""}${money(p.p)}</div>
            ${p.s > 1 && p.x > p.p ? `<div class="pd-range">${t("upTo", { v: money(p.x) })} · ${t("save")} <b>${money(p.x - p.p)}</b></div>` : ""}
            <div class="stock ${p.k ? "yes" : "no"}">${p.k ? t("inStockAt", { k: p.k, s: p.s }) : t("outEverywhere")}</div></div>
            <a class="btn btn-big" href="#offers">${live.length === 1 ? t("compareOffer") : t("compareOffers", { n: live.length })}</a></div></div></section>
      <h2 class="sec-title" id="offers">${t("priceCmp")}</h2><div class="offers">${offers}</div>
      ${chart(d.hist)}
      ${row(t("similar"), `/?cat=${p.c}`, d.sim)}`;
  }

  // ---------------------------------------------------------------- shops
  function shopsPage(m) {
    markGroup(null);
    document.title = `${t("shops.title")} – CompAirsoft`;
    app.innerHTML = `<div class="results-head"><h1>${t("shops.title")}</h1><span class="muted">${t("nshops", { n: m.shops.length })}</span></div>
      <div class="shop-grid">${m.shops.map((s) => `<div class="shop-card">
        <div class="sc-head"><a class="sc-name" href="/?shop=${s.id}&all=1">${esc(s.name)}</a>${
          s.status && s.status.startsWith("error") ? `<span class="pill bad">${t("failed")}</span>` : s.updated ? `<span class="pill good">${t("upToDate")}</span>` : `<span class="pill">${t("pending")}</span>`}</div>
        ${s.url ? `<a class="sc-url" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url.split("//").pop().replace(/\/$/, ""))}</a>` : ""}
        <div class="sc-stats"><div><b>${fmt(s.offers || 0)}</b><span>${t("offersLbl")}</span></div><div><b>${fmt(s.cheapest)}</b><span>${t("cheapestOn")}</span></div></div>
        <div class="sc-foot">${t("updatedLbl", { d: esc((s.updated || "–").replace("T", " ")) })} · ${s.type === "feed" ? t("feed") : t("crawled")}</div>
        <a class="btn btn-ghost" href="/?shop=${s.id}&all=1">${t("showProducts")}</a></div>`).join("")}</div>
      <p class="muted small">${t("cheapestNote")}</p>`;
  }


  // ---------------------------------------------------------------- privacy
  const PRIVACY = {
    en: ["Privacy", "Last updated: 26 November 2026",
      [["What we collect", "Nothing about you personally. CompAirsoft has no user accounts, uses no cookies and runs no analytics, advertising or tracking scripts."],
       ["Stored in your browser", "Your choice of language and dark/light mode is saved in your browser's local storage so the site remembers it. It never leaves your device; you can delete it by clearing the site data in your browser."],
       ["Hosting (Cloudflare)", "The site is delivered by Cloudflare, Inc. To deliver it and protect it against attacks, Cloudflare processes technical data of each request, such as your IP address, browser type and the page requested. Legal basis: legitimate interest in running a secure website (Art. 6(1)(f) GDPR). See Cloudflare's privacy policy: https://www.cloudflare.com/privacypolicy/"],
       ["Product photos and shop links", "Product photos are shown as small copies stored on this website's own hosting. Only when you click a photo to enlarge it is the original loaded from the shop's server; that shop then receives your IP address and browser details (we tell your browser not to send which page you were on). When you click “Go to shop”, the shop's own privacy policy applies."],
       ["Fonts and icons", "Fonts and icons are served from this website itself; nothing is loaded from Google or other font services."],
       ["Your rights", "Under the GDPR you may ask for access to, correction or deletion of personal data, object to processing, and complain to a data protection authority (in the Czech Republic: Úřad pro ochranu osobních údajů, www.uoou.cz). As we store no personal data ourselves, requests about request logs are best directed to Cloudflare."]],
      "Contact"],
    cs: ["Ochrana soukromí", "Poslední aktualizace: 26. listopadu 2026",
      [["Co shromažďujeme", "O vás osobně nic. CompAirsoft nemá uživatelské účty, nepoužívá cookies a nespouští žádné analytické, reklamní ani sledovací skripty."],
       ["Uloženo ve vašem prohlížeči", "Zvolený jazyk a tmavý/světlý režim se ukládají do místního úložiště vašeho prohlížeče, aby si je web pamatoval. Nikdy neopouštějí vaše zařízení; smažete je vymazáním dat webu v prohlížeči."],
       ["Hosting (Cloudflare)", "Web doručuje společnost Cloudflare, Inc. Aby ho mohla doručit a chránit před útoky, zpracovává technické údaje každého požadavku, např. vaši IP adresu, typ prohlížeče a požadovanou stránku. Právní základ: oprávněný zájem na provozu bezpečného webu (čl. 6 odst. 1 písm. f) GDPR). Zásady ochrany soukromí Cloudflare: https://www.cloudflare.com/privacypolicy/"],
       ["Fotografie produktů a odkazy do obchodů", "Fotografie produktů zobrazujeme jako zmenšené kopie uložené na hostingu tohoto webu. Teprve když fotku kliknutím zvětšíte, načte se originál ze serveru obchodu; ten pak obdrží vaši IP adresu a údaje o prohlížeči (prohlížeči zakazujeme posílat, na které stránce jste byli). Po kliknutí na „Do obchodu“ platí zásady ochrany soukromí daného obchodu."],
       ["Písma a ikony", "Písma a ikony poskytuje přímo tento web; nic se nenačítá od Googlu ani jiných služeb."],
       ["Vaše práva", "Podle GDPR můžete požádat o přístup k osobním údajům, jejich opravu či výmaz, vznést námitku proti zpracování a podat stížnost u dozorového úřadu (v ČR: Úřad pro ochranu osobních údajů, www.uoou.cz). Protože sami žádné osobní údaje neukládáme, žádosti týkající se záznamů o požadavcích směřujte na Cloudflare."]],
      "Kontakt"],
    sk: ["Ochrana súkromia", "Posledná aktualizácia: 26. novembra 2026",
      [["Čo zhromažďujeme", "O vás osobne nič. CompAirsoft nemá používateľské účty, nepoužíva cookies a nespúšťa žiadne analytické, reklamné ani sledovacie skripty."],
       ["Uložené vo vašom prehliadači", "Zvolený jazyk a tmavý/svetlý režim sa ukladajú do lokálneho úložiska vášho prehliadača, aby si ich web pamätal. Nikdy neopúšťajú vaše zariadenie; vymažete ich vymazaním údajov webu v prehliadači."],
       ["Hosting (Cloudflare)", "Web doručuje spoločnosť Cloudflare, Inc. Aby ho mohla doručiť a chrániť pred útokmi, spracúva technické údaje každej požiadavky, napr. vašu IP adresu, typ prehliadača a požadovanú stránku. Právny základ: oprávnený záujem na prevádzke bezpečného webu (čl. 6 ods. 1 písm. f) GDPR). Zásady ochrany súkromia Cloudflare: https://www.cloudflare.com/privacypolicy/"],
       ["Fotografie produktov a odkazy do obchodov", "Fotografie produktov zobrazujeme ako zmenšené kópie uložené na hostingu tohto webu. Až keď fotku kliknutím zväčšíte, načíta sa originál zo servera obchodu; ten potom dostane vašu IP adresu a údaje o prehliadači (prehliadaču zakazujeme posielať, na ktorej stránke ste boli). Po kliknutí na „Do obchodu“ platia zásady ochrany súkromia daného obchodu."],
       ["Písma a ikony", "Písma a ikony poskytuje priamo tento web; nič sa nenačítava od Googlu ani iných služieb."],
       ["Vaše práva", "Podľa GDPR môžete požiadať o prístup k osobným údajom, ich opravu či vymazanie, namietať proti spracúvaniu a podať sťažnosť dozornému orgánu (na Slovensku: Úrad na ochranu osobných údajov SR, v ČR: ÚOOÚ). Keďže sami žiadne osobné údaje neukladáme, žiadosti týkajúce sa záznamov o požiadavkách smerujte na Cloudflare."]],
      "Kontakt"],
    de: ["Datenschutz", "Stand: 26. November 2026",
      [["Was wir erheben", "Nichts über dich persönlich. CompAirsoft hat keine Benutzerkonten, verwendet keine Cookies und keine Analyse-, Werbe- oder Tracking-Skripte."],
       ["In deinem Browser gespeichert", "Deine Sprache und der Dunkel-/Hellmodus werden im lokalen Speicher deines Browsers gespeichert, damit die Seite sie sich merkt. Sie verlassen nie dein Gerät; du kannst sie löschen, indem du die Websitedaten im Browser löschst."],
       ["Hosting (Cloudflare)", "Die Seite wird von Cloudflare, Inc. ausgeliefert. Um sie auszuliefern und vor Angriffen zu schützen, verarbeitet Cloudflare technische Daten jeder Anfrage, z. B. deine IP-Adresse, den Browsertyp und die aufgerufene Seite. Rechtsgrundlage: berechtigtes Interesse am Betrieb einer sicheren Website (Art. 6 Abs. 1 lit. f DSGVO). Datenschutzerklärung von Cloudflare: https://www.cloudflare.com/privacypolicy/"],
       ["Produktfotos und Shop-Links", "Produktfotos zeigen wir als verkleinerte Kopien, die auf dem Hosting dieser Website liegen. Erst wenn du ein Foto zum Vergrößern anklickst, wird das Original vom Server des Shops geladen; dieser erhält dann deine IP-Adresse und Browserangaben (wir weisen deinen Browser an, nicht mitzuteilen, auf welcher Seite du warst). Nach einem Klick auf „Zum Shop“ gilt die Datenschutzerklärung des jeweiligen Shops."],
       ["Schriften und Icons", "Schriften und Icons werden von dieser Website selbst geladen; nichts wird von Google oder anderen Diensten geladen."],
       ["Deine Rechte", "Nach der DSGVO kannst du Auskunft, Berichtigung oder Löschung personenbezogener Daten verlangen, der Verarbeitung widersprechen und dich bei einer Datenschutzbehörde beschweren. Da wir selbst keine personenbezogenen Daten speichern, richte Anfragen zu Anfrageprotokollen am besten an Cloudflare."]],
      "Kontakt"],
  };
  function privacyPage() {
    const [title, updated, sections, contactLbl] = PRIVACY[lang] || PRIVACY.en;
    document.title = `${title} – CompAirsoft`;
    markGroup(null);
    const linkify = (text) => esc(text).replace(/https:\/\/[^\s)]+/g, (u) => `<a href="${u}" rel="noopener" target="_blank">${u}</a>`);
    const contact = SITE.contact ? `<h2>${esc(contactLbl)}</h2><p id="contact"><button type="button" class="btn btn-ghost" id="show-email">${t("showEmail")}</button></p>` : "";
    app.innerHTML = `<article class="prose"><h1>${esc(title)}</h1><p class="muted small">${esc(updated)}</p>
      ${sections.map(([h, txt]) => `<h2>${esc(h)}</h2><p>${linkify(txt)}</p>`).join("")}${contact}</article>`;
    const btn = document.getElementById("show-email");
    if (btn) btn.addEventListener("click", () => {
      const mail = atob(SITE.contact).split("").reverse().join("");
      document.getElementById("contact").innerHTML = `<a href="mailto:${esc(mail)}">${esc(mail)}</a>`;
    });
  }

  // ---------------------------------------------------------------- router
  const page = document.body.dataset.page;
  async function route() {
    if (page === "404") return;
    try {
      const m = await json("/data/meta.json");
      document.getElementById("updated").textContent = t("updated", { d: m.generated.replace("T", " ") });
      catbarFollow(null);
      if (page === "product") return await product();
      if (page === "shops") return shopsPage(m);
      if (page === "privacy") return privacyPage();
      const p = P();
      const filtered = ["q", "cat", "shop", "stock", "multi", "minshops", "save", "pmin", "pmax", "all", ...FACETS.map((f) => f[1])].some((k) => p.get(k))
        || (p.get("sort") || "relevance") !== "relevance" || +p.get("page") > 1;
      return filtered ? await listing(m) : home(m);
    } catch (e) {
      console.error(e);
      app.innerHTML = `<div class="empty">${t("loadError")}</div>`;
    }
  }
  // Filters, sorting and paging on the listing page update in place instead of reloading.
  if (page === "index") {
    document.addEventListener("click", (e) => {
      const more = e.target.closest("[data-more]");
      if (more) { const g = more.closest(".f-group"); g.classList.toggle("expanded"); more.textContent = g.classList.contains("expanded") ? t("showLess") : t("showMore"); return; }
      const a = e.target.closest("a[href]");
      if (!a || e.ctrlKey || e.metaKey || e.shiftKey || a.target) return;
      const href = a.getAttribute("href");
      if (!href.startsWith("/?") && href !== "/") return;
      e.preventDefault();
      history.pushState(null, "", href);
      const inList = a.closest(".results, .filters");
      route().then(() => { if (!inList || a.closest(".pager")) scrollTo(0, 0); });
    });
    document.addEventListener("submit", (e) => {
      const f = e.target;
      if (f.getAttribute("action") !== "/") return;
      e.preventDefault();
      const qs = new URLSearchParams([...new FormData(f)].filter(([, v]) => v !== ""));
      history.pushState(null, "", "/?" + qs.toString());
      route().then(() => { if (f.classList.contains("search")) scrollTo(0, 0); });
    });
    addEventListener("popstate", route);
  }
  // Full-size photo straight from the shop, only when the visitor asks for it.
  document.addEventListener("click", (e) => {
    const z = e.target.closest(".zoom");
    if (z) {
      const box = document.createElement("div");
      box.className = "lightbox";
      box.innerHTML = `<button type="button" class="lb-close" aria-label="×">${icon("x")}</button><img src="${esc(z.dataset.orig)}" alt="" referrerpolicy="no-referrer">`;
      const close = () => { box.remove(); document.removeEventListener("keydown", onKey); };
      const onKey = (ev) => { if (ev.key === "Escape") close(); };
      box.addEventListener("click", close);
      document.addEventListener("keydown", onKey);
      document.body.appendChild(box);
    }
  });
  document.addEventListener("error", (e) => { if (e.target.tagName === "IMG") e.target.remove(); }, true);
  applyShell();
  route();
})();
