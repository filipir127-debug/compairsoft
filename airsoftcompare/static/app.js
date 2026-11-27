"use strict";
(() => {
  const SITE = JSON.parse(document.getElementById("site-config").textContent);
  const { groups: GROUPS, groupOf: GROUP_OF, icons: ICONS, currency: BASE, cats: CATS } = SITE;
  const V = document.documentElement.dataset.v;
  const app = document.getElementById("app");
  const PAGE_SIZE = 48;
  const LANGS = ["cs", "sk", "en", "de"];

  // ---------------------------------------------------------------- translations
  const T = {
    en: {
      "search.ph": "Search guns, magazines, red dots…", "search.btn": "Search", "nav.shops": "Shops", loading: "Loading…",
      "foot.about": "Tired of going to each individual site to check where prices are better? Now you don't have to! Everything at one place.", "foot.browse": "Browse", "foot.know": "Good to know",
      "foot.disclaimer": "Prices are read from each shop's public feed or product pages and may be out of date. Always check the shop before buying.",
      updated: "Prices last updated {d}.", all: "All products", "sec.most": "Compared in the most shops", "sec.diff": "Biggest price differences",
      "nf.title": "Page not found", "nf.home": "Back to the homepage", home: "Home",
      "hero.title": "Find the cheapest airsoft gear", "hero.text": "We compare <b>{offers}</b> offers from <b>{shops}</b> airsoft shops, so you don't have to open every one.", categories: "Categories",
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
      "pw.electric": "Electric (AEG)", "pw.gas": "Gas (GBB)", "pw.co2": "CO2", "pw.hpa": "HPA", "pw.spring": "Spring / manual", "allParams": "All parameters", "clearParams": "Clear selected parameters", "close": "Close", "showN": "Show {n}", "tile.electric": "AEG", "tile.gas": "GBB", "tile.co2": "CO₂", "tile.spring": "Spring", "tile.hpa": "HPA", "f.platform": "Platform", "pl.ak": "AK", "pl.m4": "M4 & M16", "pl.mp5": "MP5", "pl.ww2": "WWII", "pl.bullpup": "Bullpup", "pl.mg": "Machine guns", "ag.rifle": "Rifles", "ag.pistol": "Pistols", "ag.pellets": "Diabolos", "f.airgun": "Type", "f.caliber": "Calibre",
      "mt.metal": "Metal", "mt.plastic": "Plastic / ABS", "cap.low": "Low-cap", "cap.mid": "Mid-cap", "cap.hi": "Hi-cap", "cap.real": "Real-cap",
      "col.black": "Black", "col.green": "Green", "col.olive": "Olive", "col.tan": "Tan", "col.brown": "Brown", "col.grey": "Grey", "col.white": "White",
      "col.red": "Red", "col.blue": "Blue", "col.pink": "Pink", "col.orange": "Orange", "col.camo": "Camo",
      "theme": "Dark / light mode", lang: "Language", privacy: "Privacy", onlyDiscount: "Discounted 10 % or more", soldIn2: "Sold in 2+ shops", availAll: "All products", availStock: "In stock anywhere", moreN: "{n} more", lessBtn: "Show less", priceUpTo: "Up to {v}", removeAll: "Clear all", origName: "Original name", ratesNote: "Prices in {c} are converted from CZK at the Czech National Bank rate of {d}.", zoom: "Show the original photo", showEmail: "Show email address",
    },
    cs: {
      "search.ph": "Hledat zbraně, zásobníky, kolimátory…", "search.btn": "Hledat", "nav.shops": "Obchody", loading: "Načítání…",
      "foot.about": "Už vás nebaví procházet každý obchod zvlášť, abyste zjistili, kde je to levnější? Teď už nemusíte! Všechno na jednom místě.", "foot.browse": "Procházet", "foot.know": "Dobré vědět",
      "foot.disclaimer": "Ceny čteme z veřejných feedů a stránek obchodů a nemusí být aktuální. Před nákupem vždy ověřte cenu v obchodě.",
      updated: "Ceny naposledy aktualizovány {d}.", all: "Všechny produkty", "sec.most": "Porovnáno v nejvíce obchodech", "sec.diff": "Největší rozdíly v cenách",
      "nf.title": "Stránka nenalezena", "nf.home": "Zpět na úvod", home: "Úvod",
      "hero.title": "Najděte nejlevnější airsoftové vybavení", "hero.text": "Porovnáváme <b>{offers}</b> nabídek z <b>{shops}</b> airsoftových obchodů, abyste nemuseli procházet každý zvlášť.", categories: "Kategorie",
      nprod: "{n} produktů", nprod1: "1 produkt", nprod2: "{n} produkty", browseAll: "Zobrazit všech {n} produktů", showAll: "Zobrazit vše ›",
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
      "pw.electric": "Elektrický (AEG)", "pw.gas": "Plynový (GBB)", "pw.co2": "CO2", "pw.hpa": "HPA", "pw.spring": "Pružinový / manuální", "allParams": "Všechny parametry", "clearParams": "Zrušit vybrané parametry", "close": "Zavřít", "showN": "Zobrazit {n}", "tile.electric": "AEG", "tile.gas": "GBB", "tile.co2": "CO₂", "tile.spring": "Pružinové", "tile.hpa": "HPA", "f.platform": "Platforma", "pl.ak": "AK", "pl.m4": "M4 a M16", "pl.mp5": "MP5", "pl.ww2": "2. světová válka", "pl.bullpup": "Bullpup", "pl.mg": "Kulomety", "ag.rifle": "Pušky", "ag.pistol": "Pistole", "ag.pellets": "Diabolky", "f.airgun": "Typ", "f.caliber": "Ráže",
      "mt.metal": "Kov", "mt.plastic": "Plast / ABS", "cap.low": "Low-cap", "cap.mid": "Mid-cap", "cap.hi": "Hi-cap", "cap.real": "Real-cap",
      "col.black": "Černá", "col.green": "Zelená", "col.olive": "Olivová", "col.tan": "Písková", "col.brown": "Hnědá", "col.grey": "Šedá", "col.white": "Bílá",
      "col.red": "Červená", "col.blue": "Modrá", "col.pink": "Růžová", "col.orange": "Oranžová", "col.camo": "Maskáčová",
      "theme": "Tmavý / světlý režim", lang: "Jazyk", privacy: "Ochrana soukromí", onlyDiscount: "Se slevou 10 % a více", soldIn2: "Prodáváno ve 2+ obchodech", availAll: "Všechno zboží", availStock: "Skladem kdekoliv", moreN: "Dalších {n}", lessBtn: "Zobrazit méně", priceUpTo: "Do {v}", removeAll: "Zrušit vše", origName: "Původní název", ratesNote: "Ceny v {c} jsou přepočtené z Kč kurzem ČNB ze dne {d}.", zoom: "Zobrazit původní fotku", showEmail: "Zobrazit e-mail",
    },
    sk: {
      "search.ph": "Hľadať zbrane, zásobníky, kolimátory…", "search.btn": "Hľadať", "nav.shops": "Obchody", loading: "Načítava sa…",
      "foot.about": "Už vás nebaví prechádzať každý obchod zvlášť, aby ste zistili, kde je to lacnejšie? Teraz už nemusíte! Všetko na jednom mieste.", "foot.browse": "Prehliadať", "foot.know": "Dobré vedieť",
      "foot.disclaimer": "Ceny čítame z verejných feedov a stránok obchodov a nemusia byť aktuálne. Pred nákupom vždy overte cenu v obchode.",
      updated: "Ceny naposledy aktualizované {d}.", all: "Všetky produkty", "sec.most": "Porovnané v najviac obchodoch", "sec.diff": "Najväčšie rozdiely v cenách",
      "nf.title": "Stránka sa nenašla", "nf.home": "Späť na úvod", home: "Úvod",
      "hero.title": "Nájdite najlacnejšie airsoftové vybavenie", "hero.text": "Porovnávame <b>{offers}</b> ponúk z <b>{shops}</b> airsoftových obchodov, aby ste nemuseli prechádzať každý zvlášť.", categories: "Kategórie",
      nprod: "{n} produktov", nprod1: "1 produkt", nprod2: "{n} produkty", browseAll: "Zobraziť všetkých {n} produktov", showAll: "Zobraziť všetko ›",
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
      "pw.electric": "Elektrický (AEG)", "pw.gas": "Plynový (GBB)", "pw.co2": "CO2", "pw.hpa": "HPA", "pw.spring": "Pružinový / manuálny", "allParams": "Všetky parametre", "clearParams": "Zrušiť vybrané parametre", "close": "Zavrieť", "showN": "Zobraziť {n}", "tile.electric": "AEG", "tile.gas": "GBB", "tile.co2": "CO₂", "tile.spring": "Pružinové", "tile.hpa": "HPA", "f.platform": "Platforma", "pl.ak": "AK", "pl.m4": "M4 a M16", "pl.mp5": "MP5", "pl.ww2": "2. svetová vojna", "pl.bullpup": "Bullpup", "pl.mg": "Guľomety", "ag.rifle": "Pušky", "ag.pistol": "Pištole", "ag.pellets": "Diabolky", "f.airgun": "Typ", "f.caliber": "Kaliber",
      "mt.metal": "Kov", "mt.plastic": "Plast / ABS", "cap.low": "Low-cap", "cap.mid": "Mid-cap", "cap.hi": "Hi-cap", "cap.real": "Real-cap",
      "col.black": "Čierna", "col.green": "Zelená", "col.olive": "Olivová", "col.tan": "Piesková", "col.brown": "Hnedá", "col.grey": "Sivá", "col.white": "Biela",
      "col.red": "Červená", "col.blue": "Modrá", "col.pink": "Ružová", "col.orange": "Oranžová", "col.camo": "Maskáčová",
      "theme": "Tmavý / svetlý režim", lang: "Jazyk", privacy: "Ochrana súkromia", onlyDiscount: "So zľavou 10 % a viac", soldIn2: "Predávané v 2+ obchodoch", availAll: "Všetok tovar", availStock: "Skladom kdekoľvek", moreN: "Ďalších {n}", lessBtn: "Zobraziť menej", priceUpTo: "Do {v}", removeAll: "Zrušiť všetko", origName: "Pôvodný názov", ratesNote: "Ceny v {c} sú prepočítané z Kč kurzom ČNB zo dňa {d}.", zoom: "Zobraziť pôvodnú fotku", showEmail: "Zobraziť e-mail",
    },
    de: {
      "search.ph": "Waffen, Magazine, Red Dots suchen…", "search.btn": "Suchen", "nav.shops": "Shops", loading: "Wird geladen…",
      "foot.about": "Keine Lust mehr, jeden Shop einzeln zu besuchen, um zu sehen, wo es günstiger ist? Das musst du jetzt nicht mehr! Alles an einem Ort.", "foot.browse": "Stöbern", "foot.know": "Gut zu wissen",
      "foot.disclaimer": "Die Preise stammen aus öffentlichen Feeds und Produktseiten der Shops und können veraltet sein. Bitte vor dem Kauf im Shop prüfen.",
      updated: "Preise zuletzt aktualisiert am {d}.", all: "Alle Produkte", "sec.most": "In den meisten Shops verglichen", "sec.diff": "Größte Preisunterschiede",
      "nf.title": "Seite nicht gefunden", "nf.home": "Zur Startseite", home: "Start",
      "hero.title": "Finde die günstigste Airsoft-Ausrüstung", "hero.text": "Wir vergleichen <b>{offers}</b> Angebote aus <b>{shops}</b> Airsoft-Shops, damit du nicht jeden einzeln öffnen musst.", categories: "Kategorien",
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
      "pw.electric": "Elektrisch (AEG)", "pw.gas": "Gas (GBB)", "pw.co2": "CO2", "pw.hpa": "HPA", "pw.spring": "Feder / manuell", "allParams": "Alle Parameter", "clearParams": "Ausgewählte Parameter löschen", "close": "Schließen", "showN": "{n} anzeigen", "tile.electric": "AEG", "tile.gas": "GBB", "tile.co2": "CO₂", "tile.spring": "Federdruck", "tile.hpa": "HPA", "f.platform": "Plattform", "pl.ak": "AK", "pl.m4": "M4 & M16", "pl.mp5": "MP5", "pl.ww2": "Zweiter Weltkrieg", "pl.bullpup": "Bullpup", "pl.mg": "Maschinengewehre", "ag.rifle": "Gewehre", "ag.pistol": "Pistolen", "ag.pellets": "Diabolos", "f.airgun": "Typ", "f.caliber": "Kaliber",
      "mt.metal": "Metall", "mt.plastic": "Kunststoff / ABS", "cap.low": "Low-Cap", "cap.mid": "Mid-Cap", "cap.hi": "Hi-Cap", "cap.real": "Real-Cap",
      "col.black": "Schwarz", "col.green": "Grün", "col.olive": "Oliv", "col.tan": "Tan", "col.brown": "Braun", "col.grey": "Grau", "col.white": "Weiß",
      "col.red": "Rot", "col.blue": "Blau", "col.pink": "Rosa", "col.orange": "Orange", "col.camo": "Tarn",
      "theme": "Dunkel / hell", lang: "Sprache", privacy: "Datenschutz", onlyDiscount: "Mit Rabatt ab 10 %", soldIn2: "In 2+ Shops erhältlich", availAll: "Alle Artikel", availStock: "Irgendwo auf Lager", moreN: "{n} weitere", lessBtn: "Weniger anzeigen", priceUpTo: "Bis {v}", removeAll: "Alle entfernen", origName: "Originalname", ratesNote: "Preise in {c} sind aus CZK zum Kurs der Tschechischen Nationalbank vom {d} umgerechnet.", zoom: "Originalfoto anzeigen", showEmail: "E-Mail-Adresse anzeigen",
    },
  };
  const CAT_NAMES = {
    // order: en, cs, sk, de
    weapons: ["Guns", "Zbraně", "Zbrane", "Waffen"], ammo: ["Magazines, BBs & gas", "Zásobníky, kuličky a plyn", "Zásobníky, guličky a plyn", "Magazine, BBs & Gas"],
    sights: ["Optics & lights", "Optika a svítilny", "Optika a svietidlá", "Optik & Licht"], upgrades: ["Parts & accessories", "Díly a příslušenství", "Diely a príslušenstvo", "Teile & Zubehör"],
    gear: ["Tactical gear", "Taktická výstroj", "Taktická výstroj", "Taktische Ausrüstung"], protection: ["Protection", "Ochrana", "Ochrana", "Schutz"],
    apparel: ["Clothing & boots", "Oblečení a obuv", "Oblečenie a obuv", "Kleidung & Schuhe"], misc: ["Other", "Ostatní", "Ostatné", "Sonstiges"],
    radios: ["Radios & headsets", "Vysílačky a headsety", "Vysielačky a headsety", "Funk & Headsets"], food: ["Food", "Jídlo", "Jedlo", "Essen"],
    guns: ["Rifles", "Pušky", "Pušky", "Gewehre"], smgs: ["SMGs", "Samopaly", "Samopaly", "Maschinenpistolen"], pistols: ["Pistols", "Pistole", "Pištole", "Pistolen"],
    snipers: ["Snipers", "Odstřelovací pušky", "Odstreľovacie pušky", "Scharfschützengewehre"], shotguns: ["Shotguns", "Brokovnice", "Brokovnice", "Schrotflinten"],
    magazines: ["Magazines", "Zásobníky", "Zásobníky", "Magazine"], bbs: ["BBs", "Kuličky", "Guličky", "BBs"], gas: ["Gas & CO2", "Plyn a CO2", "Plyn a CO2", "Gas & CO2"],
    optics: ["Optics & red dots", "Optika a kolimátory", "Optika a kolimátory", "Optiken & Red Dots"], lights: ["Lights & lasers", "Svítilny a lasery", "Svietidlá a lasery", "Lampen & Laser"],
    parts: ["Parts & upgrades", "Díly a upgrady", "Diely a upgrady", "Teile & Tuning"], batteries: ["Batteries", "Baterie", "Batérie", "Akkus"], chargers: ["Chargers", "Nabíječky", "Nabíjačky", "Ladegeräte"],
    vests: ["Vests & plate carriers", "Vesty a nosiče plátů", "Vesty a nosiče plátov", "Westen & Plattenträger"], pouches: ["Pouches & bags", "Sumky a tašky", "Sumky a tašky", "Taschen & Rucksäcke"],
    holsters: ["Holsters", "Pouzdra", "Puzdrá", "Holster"], slings: ["Slings", "Popruhy", "Popruhy", "Tragegurte"],
    masks: ["Masks", "Masky", "Masky", "Masken"], eyewear: ["Goggles & glasses", "Brýle", "Okuliare", "Schutzbrillen"], helmets: ["Helmets", "Helmy", "Prilby", "Helme"], gloves: ["Gloves", "Rukavice", "Rukavice", "Handschuhe"],
    clothing: ["Clothing & boots", "Oblečení a obuv", "Oblečenie a obuv", "Kleidung & Schuhe"],
    comms: ["Radios & headsets", "Vysílačky a headsety", "Vysielačky a headsety", "Funk & Headsets"], grenades: ["Pyro & grenade launchers", "Pyro a granátomety", "Pyro a granátomety", "Pyro & Granatwerfer"],
    food: ["Food", "Jídlo", "Jedlo", "Essen"],
    airguns: ["Airguns", "Vzduchové zbraně", "Vzduchové zbrane", "Luftdruckwaffen"], melee: ["Melee", "Chladné zbraně", "Chladné zbrane", "Nahkampfwaffen"],
    bows: ["Bows & crossbows", "Luky a kuše", "Luky a kuše", "Bögen & Armbrüste"], targets: ["Targets", "Terče", "Terče", "Zielscheiben"],
    magnets: ["Magnets", "Magnetky", "Magnetky", "Magnete"], books: ["Books, journals & catalogues", "Knihy, časopisy a katalogy", "Knihy, časopisy a katalógy", "Bücher, Zeitschriften & Kataloge"],
    cables: ["Cables & adapters", "Kabely a redukce", "Káble a redukcie", "Kabel & Adapter"],
    other: ["Other", "Ostatní", "Ostatné", "Sonstiges"],
  };
  // Header slogans: the first one explains the name and is shown on a visitor's first visit;
  // after that a random one, never the same twice in a row. Keep each under ~36 characters.
  const SLOGANS = {
    en: ["Compare? Airsoft? Compairsoft.", "Every shop in your sights.", "Zero in on the best price.", "Lock on to the best deal.",
      "Don't blind-fire. Compare first.", "Your wallet takes no hits.", "Overpaying is friendly fire."],
    cs: ["Porovnat? Airsoft? Compairsoft.", "Všechny obchody na mušce.", "Zamiř na nejlepší cenu.", "Nestřílej naslepo. Porovnej.",
      "Peněženka bez zásahu.", "Přeplácení je friendly fire.", "Stejná zbraň, nižší cena."],
    sk: ["Porovnať? Airsoft? Compairsoft.", "Všetky obchody na muške.", "Zameraj sa na najlepšiu cenu.", "Nestrieľaj naslepo. Porovnaj.",
      "Peňaženka bez zásahu.", "Preplácanie je friendly fire.", "Rovnaká zbraň, nižšia cena."],
    de: ["Vergleichen? Airsoft? Compairsoft.", "Alle Shops im Visier.", "Den besten Preis im Fadenkreuz.", "Nicht blind feuern. Vergleichen.",
      "Kein Treffer für deinen Geldbeutel.", "Zu viel zahlen ist Friendly Fire.", "Gleiche Waffe, besserer Preis."],
  };
  const sloganIdx = (() => {
    let last = null;
    try { last = localStorage.getItem("slogan"); } catch (e) { /* private mode */ }
    let i = 0;
    if (last !== null) do i = Math.floor(Math.random() * SLOGANS.en.length); while (String(i) === last);
    try { localStorage.setItem("slogan", String(i)); } catch (e) { /* private mode */ }
    return i;
  })();
  function showSlogan() {
    const el = document.getElementById("slogan");
    if (!el) return;
    const text = (SLOGANS[lang] || SLOGANS.en)[sloganIdx];
    const [before, after] = text.split("Compairsoft");
    el.textContent = before;
    if (after !== undefined) {  // the name keeps the logo's two colours
      const name = document.createElement("i"), b = document.createElement("b");
      b.textContent = "airsoft"; name.append("Comp", b, after); el.append(name);
    }
  }
  let lang = LANGS.includes(document.documentElement.lang) ? document.documentElement.lang : "en";
  const t = (key, vars) => {
    let s = (T[lang] && T[lang][key]) ?? T.en[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v);
    return s;
  };
  const catName = (slug) => (CAT_NAMES[slug] || CAT_NAMES.other)[["en", "cs", "sk", "de"].indexOf(lang)];
  // Czech and Slovak: 1 produkt, 2–4 produkty, 5+ produktů / produktov
  const nprod = (n) => (n === 1 ? t("nprod1") : n >= 2 && n <= 4 && T[lang].nprod2 ? t("nprod2", { n: fmt(n) }) : t("nprod", { n: fmt(n) }));

  // ---------------------------------------------------------------- helpers
  // Links and images come from shop data: only absolute http(s) URLs (no javascript:, data:…).
  // The export checks them too; this second guard also covers JSON left over in caches.
  const safeUrl = (u) => {
    try {
      const x = new URL(String(u ?? ""));
      return x.protocol === "http:" || x.protocol === "https:" ? x.href : "";
    } catch { return ""; }
  };
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cache = {};
  const json = (u) => (cache[u] ||= fetch(`${u}?v=${V}`).then((r) => { if (!r.ok) throw new Error(`${u}: ${r.status}`); return r.json(); }));
  const fold = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  // Dates are always DD.MM.YYYY (with HH:MM when the value has a time), whatever the language.
  const fmtDate = (v) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}:\d{2}))?/.exec(v || "");
    return m ? `${m[3]}.${m[2]}.${m[1]}${m[4] ? " " + m[4] : ""}` : v;
  };
  const fmt = (n) => Math.round(n).toLocaleString("cs-CZ").replace(/\s/g, " ");
  // Prices are stored in the base currency (CZK) and converted for display at the ČNB daily rate.
  const LOCALES = { cs: "cs-CZ", sk: "sk-SK", en: "en-GB", de: "de-DE" };
  let RATES = { [BASE]: 1 };
  let cur = (() => { try { return localStorage.getItem("currency"); } catch (e) { return null; } })()
    || ({ sk: "EUR", de: "EUR" }[document.documentElement.lang] || BASE);
  const rate = () => RATES[cur] || 1;
  const toCur = (v) => v / rate();
  const fmtCur = (x) => (cur === "CZK" ? fmt(x) + " Kč"
    : x.toLocaleString(LOCALES[lang] || "en-GB", { style: "currency", currency: cur, maximumFractionDigits: x >= 1000 ? 0 : 2 }));
  const money = (v) => (v == null ? "–" : fmtCur(toCur(v)));
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
  const catHref = (c) => (knownCat(c) ? "/?cat=" + encodeURIComponent(c) : "/?all=1");
  const list = (p, k) => (p.get(k) || "").split(",").filter(Boolean);

  // ---------------------------------------------------------------- shell: language, theme
  function applyShell() {
    document.documentElement.lang = lang;
    showSlogan();
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
    document.querySelectorAll(".catbar [data-group] span").forEach((el) => { el.textContent = catName(el.parentElement.dataset.group); });
    const sel = document.getElementById("lang");
    sel.value = lang; sel.setAttribute("aria-label", t("lang"));
    document.getElementById("theme").setAttribute("aria-label", t("theme"));
  }
  const store = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } };
  document.getElementById("cur").addEventListener("change", (e) => {
    cur = e.target.value; store("currency", cur); route();
  });
  document.getElementById("lang").addEventListener("change", (e) => {
    lang = e.target.value; store("lang", lang); TR = {}; itemsCache.trKey = null; applyShell(); route();
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
      <div class="thumb">${groupIcon(p.c)}${safeUrl(p.i) ? `<img src="${esc(safeUrl(p.i))}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ""}${save}</div>
      <div class="card-body">
        ${p.b ? `<div class="card-brand">${esc(p.b)}</div>` : ""}<div class="name">${esc(nameOf(p))}</div>${stock}
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
  // Some category tiles have several pictures; one is picked at random per visit.
  const ILLU = {
    weapons: ["weapons", "weapons-ak", "weapons-smg", "weapons-pistol", "weapons-sniper", "weapons-shotgun"],
    protection: ["protection", "protection-goggles", "protection-glasses", "protection-mask", "protection-glove", "protection-headset"],
  };
  const ILLU_PICK = Object.fromEntries(Object.entries(ILLU).map(([g, l]) => [g, l[Math.floor(Math.random() * l.length)]]));
  function home(m) {
    markGroup(null);
    if (TR_LANGS.includes(lang) && m.tr) Object.assign(TR, m.tr[lang] || {});
    document.title = `CompAirsoft – ${t("hero.title")}`;
    const tiles = Object.entries(GROUPS).map(([g, [, , subs]]) => {
      const total = subs.reduce((n, s) => n + (m.counts[s] || 0), 0);
      if (!total) return "";

      const links = subs.length > 1 ? `<div class="tile-subs">${subs.filter((s) => m.counts[s]).map((s) => `<a href="/?cat=${s}">${esc(catName(s))}</a>`).join("")}</div>` : "";
      return `<div class="tile"><a class="tile-main" href="/?cat=${g}">
<span class="tile-img"><svg class="illu" viewBox="0 0 160 90" aria-hidden="true"><use href="#cat-${ILLU_PICK[g] || g}"/></svg></span>
          <span class="tile-text"><span class="tile-name">${esc(catName(g))}</span><span class="tile-n">${nprod(total)}</span></span></a>${links}</div>`;
    }).join("");
    const titles = { "Compared in the most shops": t("sec.most"), "Biggest price differences": t("sec.diff") };
    app.innerHTML = `
      <section class="hero"><div><h1>${t("hero.title")}</h1><p data-nosnippet>${t("hero.text", { offers: fmt(m.stats.offers), shops: m.stats.shops })}</p></div></section>
      <div class="hero-cats"><h2 class="sec-title">${t("categories")}</h2><section class="tiles">${tiles}</section></div>
      ${m.sections.map((s) => row(titles[s.title] || s.title, s.more, s.items)).join("")}
      <div class="center"><a class="btn btn-big" href="/?all=1">${t("browseAll", { n: fmt(m.stats.products) })}</a></div>`;
    catbarFollow(app.querySelector(".hero-cats"));
  }

  // ---------------------------------------------------------------- listing with facets
  function matcher(q, syn) {
    const words = fold(q).split(/[^a-z0-9.]+/).filter(Boolean);
    const alts = words.map((w) => [w, ...(syn[w] || [])]);
    return (p) => { const k = "_f" + lang, s = (p[k] ||= fold(p.t + " " + (TR[p.id] || "") + " " + (p.b || ""))); return alts.every((o) => o.some((x) => s.includes(x))); };
  }
  const tagVals = (prefix) => (p) => (p.a || []).filter((x) => x.startsWith(prefix)).map((x) => x.slice(prefix.length));
  // name, url param, values of a product, label of a value
  const DRILL_TYPES = ["pistols", "guns", "smgs", "shotguns", "snipers"];
  const DRILL_POWERS = ["electric", "gas", "co2", "spring"];
  const DRILL_PLATFORMS = ["ak", "m4", "mp5", "ww2", "bullpup", "mg"];
  const DRILL_VALUES = { power: DRILL_POWERS, platform: DRILL_PLATFORMS, airgun: ["rifle", "pistol", "pellets"],
    caliber: ["4.5", "5.0", "5.5", "6.35", "7.62", "9"] };
  // Filter parameters come from meta.json (airsoftcompare/params.py): definitions, tabs and which
  // category uses which. A facet is [id, url key, values of a product, label of a value, kind].
  let PARAMS = {}, PSECT = {}, CATP = {};
  const LI = () => Math.max(0, ["en", "cs", "sk", "de"].indexOf(lang));
  const pName = (id) => (PARAMS[id] ? PARAMS[id].l[LI()] : t("f." + id));
  const pUrl = (id) => (PARAMS[id] && PARAMS[id].u) || id;
  const pLabel = (id) => (v) => {
    const d = PARAMS[id] || {};
    if (d.v && d.v[v]) return d.v[v][LI()];
    if (d.vp && t(d.vp + v) !== d.vp + v) return t(d.vp + v);
    if (d.f === "g") return v.replace(".", ",") + " g";
    if (d.f === "mm") return (lang === "en" ? v : v.replace(".", ",") + " ") + "mm";
    return id === "color" ? v[0].toUpperCase() + v.slice(1) : v;
  };
  const facetOf = (id) => {
    const d = PARAMS[id];
    if (d.k === "range") return [id, pUrl(id), (p) => (p.n && p.n[id] != null ? [p.n[id]] : []), null, "range"];
    return [id, pUrl(id), tagVals((d.t || id) + ":"), d.k === "bool" ? () => pName(id) : pLabel(id), d.k];
  };
  const BRAND = ["brand", "brand", (p) => (p.b ? [p.b] : []), (v) => v, "enum"];
  const SHOP = ["shop", "shop", (p) => p.h.map(String), null, "enum"];
  function facetsFor(c) {
    const conf = CATP[c];
    const ids = (conf ? conf.a : Object.keys(PARAMS)).filter((id) => PARAMS[id]);
    return { facets: [BRAND, ...ids.map(facetOf), SHOP], basic: ["brand", ...(conf ? conf.b : [])] };
  }
  // every address key a filter can use (to tell a filtered listing from the homepage)
  const paramKeys = () => Object.keys(PARAMS).flatMap((id) => (PARAMS[id].k === "range" ? [pUrl(id) + "_min", pUrl(id) + "_max"] : [pUrl(id)]));
  let itemsCache = { key: null, items: [] };
  const TR_LANGS = ["en", "de", "sk"];
  let TR = {};  // product id -> name in the current language (machine translation)
  const nameOf = (p) => TR[p.id] || p.t;
  async function loadItems(group) {
    const key = group || "*";
    if (itemsCache.key !== key) {
      const files = group ? [group] : Object.keys(GROUPS);
      itemsCache = { key, items: (await Promise.all(files.map((g) => json(`/data/g/${g}.json`)))).flat() };
    }
    if (TR_LANGS.includes(lang) && itemsCache.trKey !== lang + key) {
      const files = group ? [group] : Object.keys(GROUPS);
      for (const m of await Promise.all(files.map((g) => json(`/data/g/${g}.${lang}.json`).catch(() => ({}))))) Object.assign(TR, m);
      itemsCache.trKey = lang + key;
    }
    return itemsCache.items;
  }

  // 1, 2, two pages either side of the current one, and the last page; 0 marks a gap ("…").
  const pageNumbers = (page, pages) => {
    const want = [...new Set([1, 2, page - 2, page - 1, page, page + 1, page + 2, pages])].filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
    return want.flatMap((n, i) => (i && n - want[i - 1] > 1 ? (n - want[i - 1] === 2 ? [n - 1, n] : [0, n]) : [n]));
  };
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
    const prices = base.map((x) => toCur(x.p)).filter((v) => v > 0);
    const lo = prices.length ? Math.floor(Math.min(...prices)) : 0, hi = prices.length ? Math.ceil(Math.max(...prices)) : 0;
    if (!isNaN(pmin)) base = base.filter((x) => toCur(x.p) >= pmin);
    if (!isNaN(pmax)) base = base.filter((x) => toCur(x.p) <= pmax);

    const { facets: FACETS, basic: BASIC } = facetsFor(c);
    const isRange = (n) => FACETS.find((f) => f[0] === n)[4] === "range";
    const current = {
      sets: Object.fromEntries(FACETS.filter((f) => f[4] !== "range").map(([n, k]) => [n, new Set(list(p, k))])),
      ranges: Object.fromEntries(FACETS.filter((f) => f[4] === "range").map(([n, k]) => [n, [parseFloat(p.get(k + "_min")), parseFloat(p.get(k + "_max"))]])),
    };
    const chosen = current.sets;
    // does a product pass the chosen parameters (all but one, to count that one's values)?
    const passesWith = (st) => (x, except) => FACETS.every(([n, , vals, , kind]) => {
      if (n === except) return true;
      if (kind === "range") {
        const [a, b] = st.ranges[n];
        if (isNaN(a) && isNaN(b)) return true;
        const v = x.n && x.n[n];
        return v != null && (isNaN(a) || v >= a) && (isNaN(b) || v <= b);
      }
      return !st.sets[n].size || vals(x).some((v) => st.sets[n].has(v));
    });
    const countsWith = (st) => {
      const ok = passesWith(st);
      return Object.fromEntries(FACETS.map(([n, , vals, , kind]) => {
        if (kind === "range") {
          let lo = Infinity, hi = -Infinity, cnt = 0;
          for (const x of base) { const v = x.n && x.n[n]; if (v != null && ok(x, n)) { lo = Math.min(lo, v); hi = Math.max(hi, v); cnt++; } }
          return [n, { lo, hi, cnt }];
        }
        const cnt = new Map();
        for (const x of base) if (ok(x, n)) for (const v of new Set(vals(x))) cnt.set(v, (cnt.get(v) || 0) + 1);
        return [n, cnt];
      }));
    };
    const passes = passesWith(current);
    const items = base.filter((x) => passes(x, null));
    const facetCounts = countsWith(current);
    const shown_ = (n, counts, st) => {  // worth showing: more than one choice, or something chosen
      const [, , , , kind] = FACETS.find((f) => f[0] === n), cnt = counts[n];
      if (kind === "range") { const [a, b] = st.ranges[n]; return (cnt.cnt >= 3 && cnt.hi > cnt.lo) || !isNaN(a) || !isNaN(b); }
      if (kind === "bool") return cnt.size > 0 || st.sets[n].size > 0;
      return cnt.size > 1 || st.sets[n].size > 0 || (n === "shop" && cnt.size > 0);
    };

    const by = {
      relevance: (a, b) => b.s - a.s || a.p - b.p, shops: (a, b) => b.s - a.s || a.p - b.p, price_asc: (a, b) => a.p - b.p, price_desc: (a, b) => b.p - a.p,
      savings: (a, b) => (b.x - b.p) - (a.x - a.p), name: (a, b) => a.t.localeCompare(b.t, lang),
    }[sort] || ((a, b) => b.s - a.s || a.p - b.p);
    items.sort(by);
    const total = items.length, pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const shown = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
    const shopName = Object.fromEntries(m.shops.map((s) => [String(s.id), s.name]));

    // ---- sidebar, in the style of alza.cz: plain sections, checkbox lists with counts, price slider
    const VISIBLE = 5;
    const collator = new Intl.Collator(LOCALES[lang] || "en-GB", { numeric: true, sensitivity: "base" });
    const unitOf = (n) => (PARAMS[n] && PARAMS[n].un) || "";
    const fmtNum = (v) => fmt(Math.round(v * 10) / 10);
    const rangeBox = (n, key, info, [a, b], cls = "") => {
      const lo = info.lo === Infinity ? (isNaN(a) ? 0 : a) : info.lo, hi = info.hi === -Infinity ? (isNaN(b) ? 0 : b) : info.hi;
      const st = stepFor(lo, hi), from = isNaN(a) ? lo : Math.max(lo, Math.min(hi, a)), to = isNaN(b) ? hi : Math.max(lo, Math.min(hi, b));
      return `<div class="f-sec range-filter ${cls}" data-facet="${n}" data-lo="${lo}" data-hi="${hi}" data-kmin="${key}_min" data-kmax="${key}_max">
        <h3>${esc(pName(n))}${unitOf(n) ? ` <span class="muted">(${esc(unitOf(n))})</span>` : ""}</h3>${dualSlider(lo, hi, st, from, to, pName(n))}</div>`;
    };
    const facetBox = (name) => {
      const [, key, , lbl0, kind] = FACETS.find((f) => f[0] === name);
      if (!shown_(name, facetCounts, current)) return "";
      if (kind === "range") return rangeBox(name, key, facetCounts[name], current.ranges[name]);
      if (kind === "bool") {
        const on = chosen[name].has("y");
        return `<div class="f-sec" data-facet="${name}"><div class="opts"><a class="opt ${on ? "on" : ""}" href="${url({ [key]: on ? "" : "y", page: "" })}">
          <span class="box"></span><span class="opt-l">${esc(pName(name))} <span class="opt-n">(${fmt(facetCounts[name].get("y") || 0)})</span></span></a></div></div>`;
      }
      const cnt = facetCounts[name], lbl = lbl0 || ((v) => shopName[v] || v);
      // A–Z by the shown label; numbers by value ("0,20 g" before "0,25 g", "2" before "10").
      const vals = [...cnt.entries()].sort((a, b) => collator.compare(lbl(a[0]), lbl(b[0])));
      const rows = vals.map(([v, n], i) => {
        const on = chosen[name].has(v);
        const next = new Set(chosen[name]); on ? next.delete(v) : next.add(v);
        return `<a class="opt ${on ? "on" : ""} ${i >= VISIBLE && !on ? "extra" : ""}" href="${url({ [key]: [...next].join(","), page: "" })}">
          <span class="box"></span><span class="opt-l">${esc(lbl(v))} <span class="opt-n">(${fmt(n)})</span></span></a>`;
      }).join("");
      const hidden = vals.filter(([v], i) => i >= VISIBLE && !chosen[name].has(v)).length;
      const more = hidden ? `<button type="button" class="more-btn" data-more data-less="${t("lessBtn")}">${t("moreN", { n: hidden })}</button>` : "";
      return `<div class="f-sec" data-facet="${name}"><h3>${esc(pName(name))}</h3><div class="opts">${rows}</div>${more}</div>`;
    };
    const isChosen = (n) => (isRange(n) ? current.ranges[n].some((v) => !isNaN(v)) : chosen[n].size > 0);
    const sideIds = [...BASIC.filter((n) => FACETS.some((f) => f[0] === n)), ...FACETS.map((f) => f[0]).filter((n) => !BASIC.includes(n) && n !== "shop" && isChosen(n))];
    const anyChosen = FACETS.some(([n]) => isChosen(n));
    const clearAll = Object.fromEntries([...FACETS.flatMap(([n, k]) => (isRange(n) ? [[k + "_min", ""], [k + "_max", ""]] : [[k, ""]])), ["page", ""]]);
    const moreCount = FACETS.filter(([n]) => !sideIds.includes(n) && shown_(n, facetCounts, current)).length;
    const paramsBtn = moreCount || anyChosen ? `<div class="f-sec f-all">${moreCount ? `<button type="button" class="btn all-params" data-params>${icon("sliders-horizontal")} ${t("allParams")}</button>` : ""}
      ${anyChosen ? `<a class="clear-params" href="${url(clearAll)}">${t("clearParams")}</a>` : ""}</div>` : "";
    // the "All parameters" window works on a copy of the choices and applies them in one go
    openParams = () => paramsDialog({ FACETS, current, countsWith, passesWith, base, shown_, rangeBox, collator, shopName, isRange });
    const check = (on, over, label) => `<a class="opt ${on ? "on" : ""}" href="${url(over)}"><span class="box"></span><span class="opt-l">${label}</span></a>`;
    const radio = (on, over, label) => `<a class="opt radio ${on ? "on" : ""}" href="${url(over)}"><span class="box"></span><span class="opt-l">${label}</span></a>`;
    const from = isNaN(pmin) ? lo : Math.max(lo, Math.min(hi, pmin)), to = isNaN(pmax) ? hi : Math.max(lo, Math.min(hi, pmax));
    const priceBox = hi > lo ? `<div class="f-sec price-filter range-filter" data-lo="${lo}" data-hi="${hi}" data-kmin="pmin" data-kmax="pmax">
        <h3>${t("price")} <span class="muted">(${cur === "CZK" ? "Kč" : cur})</span></h3>${dualSlider(lo, hi, stepFor(lo, hi), from, to, t("price"))}</div>` : "";

    // active filters as removable chips, like alza.cz
    const chips = [];
    if (q) chips.push([`“${esc(q)}”`, { q: "", page: "" }]);
    if (!isNaN(pmin) || !isNaN(pmax)) chips.push([`${t("price")}: ${isNaN(pmin) ? ((x) => x[0].toLowerCase() + x.slice(1))(t("priceUpTo", { v: fmtCur(pmax) }))
      : isNaN(pmax) ? `${t("fromP")} ${fmtCur(pmin)}` : `${fmtCur(pmin)} – ${fmtCur(pmax)}`}`, { pmin: "", pmax: "", page: "" }]);
    if (stock) chips.push([t("availStock"), { stock: "", page: "" }]);
    if (minSave) chips.push([t("onlyDiscount"), { save: "", page: "" }]);
    if (minShops) chips.push([t("soldIn2"), { minshops: "", multi: "", page: "" }]);
    for (const [n, k, , lb, kind] of FACETS) {
      if (kind === "range") {
        const [a, b] = current.ranges[n], u = unitOf(n) ? " " + unitOf(n) : "";
        if (!isNaN(a) || !isNaN(b)) chips.push([`${esc(pName(n))}: ${isNaN(a) ? "…" : fmtNum(a)} – ${isNaN(b) ? "…" : fmtNum(b)}${esc(u)}`, { [k + "_min"]: "", [k + "_max"]: "", page: "" }]);
        continue;
      }
      for (const v of chosen[n]) {
        const rest = [...chosen[n]].filter((x) => x !== v);
        chips.push([esc((lb || ((x) => shopName[x] || x))(v)), { [k]: rest.join(","), page: "" }]);
      }
    }

    // quick tiles above the results: subcategories with a photo, then price bands
    const nice = (x) => { const e = 10 ** Math.floor(Math.log10(Math.max(1, x))); return [1, 2, 2.5, 5, 10].map((k) => k * e).find((v) => v >= x); };
    const sorted = prices.slice().sort((a, b) => a - b), qv = (f) => sorted[Math.floor((sorted.length - 1) * f)] || 0;
    const bands = sorted.length > 20 ? [...new Set([0.25, 0.5, 0.75].map((f) => nice(qv(f))))] : [];
    const photoOf = (sub) => { const x = items.find((y) => y.c === sub && safeUrl(y.i)) || base.find((y) => y.c === sub && safeUrl(y.i)); return x ? safeUrl(x.i) : ""; };
    const qimg = (img) => `<span class="qimg">${img ? `<img src="${esc(safeUrl(img))}" alt="" loading="lazy" referrerpolicy="no-referrer">` : icon(ICONS[group], "ic")}</span>`;
    let subTiles = group && GROUPS[group][2].length > 1 ? GROUPS[group][2].filter((sub) => m.counts[sub]).map((sub) =>
      `<a class="qtile ${c === sub ? "on" : ""}" href="${url({ cat: c === sub ? group : sub, page: "" })}">${qimg(photoOf(sub))}${esc(catName(sub))}</a>`).join("") : "";
    // Guns go one step deeper per click: type > power (AEG, GBB, CO2, spring) > platform (AK, M4, …);
    // air guns: kind (rifles, pistols, diabolos) > calibre for diabolos.
    const one = (name) => (chosen[name].size === 1 ? [...chosen[name]][0] : "");
    const path = DRILL_TYPES.includes(c) ? ["power", "platform"] : c === "airguns" ? ["airgun", ...(one("airgun") === "pellets" ? ["caliber"] : [])] : [];
    const level = path.find((n) => !one(n)) || path[path.length - 1];
    if (level) {
      const [, key, , label] = FACETS.find((f) => f[0] === level);
      const tag = { power: "pw:", platform: "pl:", airgun: "ag:", caliber: "cal:" }[level];
      const shownLabel = level === "power" ? (v) => t("tile." + v) : label;
      const best = (v) => { let b = null; for (const y of base) if (passes(y, level) && (y.a || []).includes(tag + v) && safeUrl(y.i) && (!b || y.s > b.s)) b = y; return b ? safeUrl(b.i) : ""; };
      subTiles = DRILL_VALUES[level].filter((v) => facetCounts[level].get(v)).map((v) => {
        const on = one(level) === v;
        return `<a class="qtile ${on ? "on" : ""}" href="${url({ [key]: on ? "" : v, page: "" })}">${qimg(best(v))}${esc(shownLabel(v))}</a>`;
      }).join("");
    }
    const priceTiles = bands.map((v) => `<a class="qtile ${pmax === v && isNaN(pmin) ? "on" : ""}" href="${url({ pmin: "", pmax: v, page: "" })}">
        <span class="qimg qprice">${icon("layers", "ic")}</span>${t("priceUpTo", { v: fmtCur(v) })}</a>`).join("");

    const steps = [];
    if (c && c !== group) steps.push([catName(c), Object.fromEntries([...path.map((n) => [FACETS.find((f) => f[0] === n)[1], ""]), ["page", ""]])]);
    for (const [i, n] of path.entries()) {
      if (!one(n)) break;
      const [, , , label] = FACETS.find((f) => f[0] === n);
      const clear = Object.fromEntries([...path.slice(i + 1).map((m) => [FACETS.find((f) => f[0] === m)[1], ""]), ["page", ""]]);
      steps.push([n === "power" ? t("tile." + one(n)) : label(one(n)), clear]);
    }
    const named = c ? [catName(c), ...steps.slice(1).map(([l]) => l)].join(" · ") : t("all");
    const title = q ? `“${esc(q)}”` : esc(named);
    document.title = `${q || named} – CompAirsoft`;
    const open = innerWidth >= 900 ? "open" : "";
    const crumbs = steps.map(([l, h], i) => `<span>›</span>${i < steps.length - 1 ? `<a href="${url(h)}">${esc(l)}</a>` : `<span>${esc(l)}</span>`}`).join("");
    app.innerHTML = `${group ? `<nav class="crumbs"><a href="/">${t("home")}</a><span>›</span><a href="/?cat=${group}">${esc(catName(group))}</a>${crumbs}</nav>` : ""}
      <div class="layout">
      <aside class="filters"><details class="filters-box" ${open}><summary>${icon("sliders-horizontal")} ${t("filters")}</summary>
        ${priceBox}
        <div class="f-sec">${check(minSave >= 10, { save: minSave ? "" : 10, page: "" }, t("onlyDiscount"))}
          ${check(minShops >= 2, { minshops: minShops ? "" : 2, multi: "", page: "" }, t("soldIn2"))}</div>
        <div class="f-sec"><h3>${t("avail")}</h3><div class="opts">
          ${radio(!stock, { stock: "", page: "" }, t("availAll"))}${radio(stock, { stock: "1", page: "" }, t("availStock"))}</div></div>
        ${sideIds.map((n) => facetBox(n)).join("")}
        ${paramsBtn}
      </details></aside>
      <section class="results">
        <div class="results-head"><h1>${title}</h1></div>
        ${subTiles || priceTiles ? `<div class="qtiles">${subTiles}${priceTiles}</div>` : ""}
        ${chips.length ? `<div class="chips">${chips.map(([l, over]) => `<a class="chip" href="${url(over)}">${l} ${icon("x")}</a>`).join("")}<a class="chip-clear" href="${catHref(c)}">${t("removeAll")}</a></div>` : ""}
        <div class="count">${nprod(total)}</div>
        <nav class="sort-tabs">${["relevance", "price_asc", "price_desc", "savings", "name"].map((k) => `<a href="${url({ sort: k, page: "" })}" class="${sort === k ? "on" : ""}">${t("sort." + k)}</a>`).join("")}</nav>
        ${total ? `<div class="grid">${shown.map(card).join("")}</div>` : `<div class="empty">${t("nothing")}</div>`}
        ${pages > 1 ? `<nav class="pager" aria-label="${t("pageOf", { p: page, n: pages })}">${page > 1 ? `<a class="pg-step" href="${url({ page: page - 1 })}">${t("prev")}</a>` : ""}
          ${pageNumbers(page, pages).map((n) => n === 0 ? `<span class="pg-gap">…</span>` : n === page ? `<span class="pg on" aria-current="page">${n}</span>`
            : `<a class="pg" href="${url({ page: n === 1 ? "" : n })}">${n}</a>`).join("")}
          ${page < pages ? `<a class="pg-step" href="${url({ page: page + 1 })}">${t("next")}</a>` : ""}</nav>` : ""}
      </section></div>`;
    rangeSliders(app);
  }

  const stepFor = (lo, hi) => {
    const r = Math.max(hi - lo, 0.1) / 200, e = 10 ** Math.floor(Math.log10(r));
    return [1, 2, 5, 10].map((k) => k * e).find((x) => x >= r) || 1;
  };
  const roundTo = (v, st) => (st < 1 ? Math.round(v * 10) / 10 : Math.round(v));
  const dualSlider = (lo, hi, st, from, to, label) => `<div class="dual"><div class="dual-track"><span class="dual-fill"></span></div>
      <input type="range" class="r-min" min="${lo}" max="${hi}" step="${st}" value="${from}" aria-label="${esc(label)} ${t("from")}">
      <input type="range" class="r-max" min="${lo}" max="${hi}" step="${st}" value="${to}" aria-label="${esc(label)} ${t("to")}"></div>
    <div class="price-inputs"><input type="number" class="n-min" value="${roundTo(from, st)}" min="${lo}" max="${hi}" step="${st < 1 ? 0.1 : 1}" aria-label="${esc(label)} ${t("from")}">
      <span>–</span><input type="number" class="n-max" value="${roundTo(to, st)}" min="${lo}" max="${hi}" step="${st < 1 ? 0.1 : 1}" aria-label="${esc(label)} ${t("to")}"></div>`;

  // Range sliders (price and number parameters): dragging updates the boxes live; releasing, or
  // editing a box, applies the filter - in the sidebar through the address, in the window through onSet.
  function rangeSliders(root, onSet) {
    for (const box of root.querySelectorAll(".range-filter")) {
      const [rMin, rMax, nMin, nMax] = [".r-min", ".r-max", ".n-min", ".n-max"].map((sel) => box.querySelector(sel));
      const lo = +box.dataset.lo, hi = +box.dataset.hi, st = +rMin.step;
      const paint = () => {
        const a = hi > lo ? (+rMin.value - lo) / (hi - lo) * 100 : 0, b = hi > lo ? (+rMax.value - lo) / (hi - lo) * 100 : 100;
        box.querySelector(".dual-fill").style.cssText = `left:${a}%;right:${100 - b}%`;
      };
      const apply = () => {
        let a = +nMin.value, b = +nMax.value;
        if (a > b) [a, b] = [b, a];
        const vals = { [box.dataset.kmin]: a > lo ? roundTo(a, st) : "", [box.dataset.kmax]: b < hi ? roundTo(b, st) : "" };
        if (onSet) return onSet(box.dataset.facet, vals);
        history.pushState(null, "", url({ ...vals, page: "" })); route();
      };
      rMin.addEventListener("input", () => { if (+rMin.value > +rMax.value) rMin.value = rMax.value; nMin.value = roundTo(+rMin.value, st); paint(); });
      rMax.addEventListener("input", () => { if (+rMax.value < +rMin.value) rMax.value = rMin.value; nMax.value = roundTo(+rMax.value, st); paint(); });
      for (const el of [rMin, rMax, nMin, nMax]) el.addEventListener("change", apply);
      paint();
    }
  }

  // "All parameters": every parameter of the category in tabs, like alza.cz. Choices are made on a
  // copy and counted live; "Show N products" applies them all at once.
  let openParams = null;
  function paramsDialog(ctx) {
    const { FACETS, current, countsWith, passesWith, base, shown_, rangeBox, collator, shopName, isRange } = ctx;
    const draft = { sets: Object.fromEntries(Object.entries(current.sets).map(([n, s]) => [n, new Set(s)])),
      ranges: Object.fromEntries(Object.entries(current.ranges).map(([n, r]) => [n, [...r]])) };
    const secOf = (n) => (n === "brand" ? "basic" : n === "shop" ? "shops" : (PARAMS[n] && PARAMS[n].s) || "basic");
    const order = Object.keys(PSECT);
    let tab = null;
    const dlg = document.createElement("dialog");
    dlg.className = "pdlg";
    dlg.setAttribute("aria-labelledby", "pdlg-h");
    document.body.appendChild(dlg);
    const render = () => {
      const counts = countsWith(draft), ok = passesWith(draft);
      const total = base.filter((x) => ok(x, null)).length;
      const visible = FACETS.filter(([n]) => shown_(n, counts, draft));
      const tabs = order.filter((s) => visible.some(([n]) => secOf(n) === s));
      if (!tabs.includes(tab)) tab = tabs[0];
      const chosenIn = (s) => visible.some(([n]) => secOf(n) === s && (isRange(n) ? draft.ranges[n].some((v) => !isNaN(v)) : draft.sets[n].size));
      const inTab = visible.filter(([n]) => secOf(n) === tab);
      const tile = (n, v, label, cnt) => `<button type="button" class="ptile ${draft.sets[n].has(v) ? "on" : ""}" data-f="${esc(n)}" data-v="${esc(v)}" ${cnt ? "" : "disabled"}>
          <span class="box"></span><span class="ptile-l">${esc(label)} <span class="opt-n">(${fmt(cnt)})</span></span></button>`;
      const bools = inTab.filter((f) => f[4] === "bool");
      const blocks = inTab.filter((f) => f[4] !== "bool").map(([n, key, , lbl, kind]) => {
        if (kind === "range") return rangeBox(n, key, counts[n], draft.ranges[n], "p-range");
        const label = lbl || ((v) => shopName[v] || v);
        const vals = [...counts[n].entries(), ...[...draft.sets[n]].filter((v) => !counts[n].has(v)).map((v) => [v, 0])]
          .sort((a, b) => collator.compare(label(a[0]), label(b[0])));
        return `<div class="p-block"><h3>${esc(pName(n))}</h3><div class="ptiles">${vals.map(([v, cnt]) => tile(n, v, label(v), cnt)).join("")}</div></div>`;
      });
      if (bools.length) blocks.push(`<div class="p-block"><h3>${esc(PSECT.features ? PSECT.features[LI()] : "")}</h3><div class="ptiles">${bools.map(([n]) => tile(n, "y", pName(n), counts[n].get("y") || 0)).join("")}</div></div>`);
      dlg.innerHTML = `<div class="pdlg-head"><h2 id="pdlg-h">${t("allParams")}</h2><button type="button" class="pdlg-x" data-close aria-label="${t("close")}">${icon("x")}</button></div>
        <div class="pdlg-body"><nav class="pdlg-tabs">${tabs.map((s) => `<button type="button" class="${s === tab ? "on" : ""} ${chosenIn(s) ? "has" : ""}" data-tab="${s}">${esc(PSECT[s][LI()])}</button>`).join("")}</nav>
          <div class="pdlg-panel">${blocks.join("") || `<p class="muted">${t("nothing")}</p>`}</div></div>
        <div class="pdlg-foot"><button type="button" class="linkish" data-clear>${t("clearParams")}</button>
          <span class="sp"></span><button type="button" class="btn btn-ghost" data-close>${t("close")}</button>
          <button type="button" class="btn" data-apply ${total ? "" : "disabled"}>${t("showN", { n: nprod(total) })}</button></div>`;
      rangeSliders(dlg, (n, vals) => {
        const k = FACETS.find((f) => f[0] === n)[1];
        draft.ranges[n] = [parseFloat(vals[k + "_min"]), parseFloat(vals[k + "_max"])];
        const y = dlg.querySelector(".pdlg-panel").scrollTop; render(); dlg.querySelector(".pdlg-panel").scrollTop = y;
      });
    };
    const close = () => { dlg.close(); dlg.remove(); };
    dlg.addEventListener("click", (e) => {
      if (e.target === dlg || e.target.closest("[data-close]")) return close();
      const tb = e.target.closest("[data-tab]");
      if (tb) { tab = tb.dataset.tab; render(); dlg.querySelector(".pdlg-panel").scrollTop = 0; return; }
      const pt = e.target.closest(".ptile");
      if (pt && !pt.disabled) {
        const s = draft.sets[pt.dataset.f], v = pt.dataset.v;
        s.has(v) ? s.delete(v) : s.add(v);
        const y = dlg.querySelector(".pdlg-panel").scrollTop; render(); dlg.querySelector(".pdlg-panel").scrollTop = y;
        return;
      }
      if (e.target.closest("[data-clear]")) {
        for (const s of Object.values(draft.sets)) s.clear();
        for (const n of Object.keys(draft.ranges)) draft.ranges[n] = [NaN, NaN];
        return render();
      }
      if (e.target.closest("[data-apply]")) {
        const over = { page: "" };
        for (const [n, k, , , kind] of FACETS) {
          if (kind === "range") { const [a, b] = draft.ranges[n]; over[k + "_min"] = isNaN(a) ? "" : a; over[k + "_max"] = isNaN(b) ? "" : b; }
          else over[k] = [...draft.sets[n]].join(",");
        }
        close();
        history.pushState(null, "", url(over));
        route();
      }
    });
    dlg.addEventListener("close", () => dlg.remove());
    render();
    dlg.showModal();
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
        <text x="${L}" y="${H - 6}" class="axis">${fmtDate(days[0])}</text><text x="${W - R}" y="${H - 6}" text-anchor="end" class="axis">${fmtDate(days[days.length - 1])}</text>
        ${lines.map((l) => `<path d="${l.d}" fill="none" stroke="${l.color}" stroke-width="2.5" stroke-linejoin="round"/><circle cx="${l.cx}" cy="${l.cy}" r="4" fill="${l.color}"/>`).join("")}
      </svg><div class="legend">${lines.map((l) => `<span><svg class="sw" width="14" height="4" aria-hidden="true"><rect width="14" height="4" rx="2" fill="${l.color}"/></svg>${esc(l.s)}</span>`).join("")}</div></div>`;
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
    const tr = (TR_LANGS.includes(lang) && d.tr && d.tr[lang]) || null;
    if (tr) d.sim.forEach((q, i) => { if (tr.sim[i]) TR[q.id] = tr.sim[i]; });
    const title = (tr && tr.t) || p.t;
    markGroup(g);
    document.title = `${title} – ${t("priceCmp")} | CompAirsoft`;
    const live = d.o.filter((o) => o.a);
    const offers = d.o.map((o, i) => {
      const best = i === 0 && o.k !== 0 && o.a;
      const st = !o.a ? `<span class="stock no">${t("removed")}</span>` : o.k === 1 ? `<span class="stock yes">${t("inStock")}</span>`
        : o.k === 0 ? `<span class="stock no">${t("outOfStock")}</span>` : `<span class="stock">${t("unknown")}</span>`;
      const foreign = o.y && o.y !== cur && o.y !== BASE && o.r != null ? `<small>${o.r.toFixed(2)} ${esc(o.y)}</small>` : "";
      return `<div class="offer ${best ? "best" : ""} ${o.a ? "" : "gone"}">
        <div class="o-shop"><b>${esc(o.s)}</b>${best && d.o.length > 1 ? `<span class="tag">${t("cheapest")}</span>` : ""}<div class="o-title" title="${esc(o.t)}">${esc((tr && tr.o[i]) || o.t)}</div></div>
        <div class="o-stock">${st}</div><div class="o-price">${money(o.v)}${foreign}</div>
        <a class="btn btn-shop" href="${esc(safeUrl(o.u) || "#")}" target="_blank" rel="noopener noreferrer nofollow">${t("goShop")}</a></div>`;
    }).join("");
    app.innerHTML = `
      <nav class="crumbs"><a href="/">${t("home")}</a><span>›</span><a href="/?cat=${g}">${esc(catName(g))}</a>${GROUPS[g][2].length > 1 ? `<span>›</span><a href="/?cat=${p.c}">${esc(catName(p.c))}</a>` : ""}</nav>
      <section class="pd"><div class="pd-img">${groupIcon(p.c)}${safeUrl(p.i) ? `<button type="button" class="zoom" data-orig="${esc(safeUrl(p.orig) || safeUrl(p.i))}" aria-label="${t("zoom")}"><img src="${esc(safeUrl(p.i))}" alt="${esc(p.t)}" referrerpolicy="no-referrer"><span class="zoom-hint">${icon("search")}</span></button>` : ""}</div>
        <div class="pd-info"><h1>${esc(title)}</h1>${title !== p.t ? `<div class="orig-name">${t("origName")}: ${esc(p.t)}</div>` : ""}
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
        ${safeUrl(s.url) ? `<a class="sc-url" href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer nofollow">${esc(s.url.split("//").pop().replace(/\/$/, ""))}</a>` : ""}
        <div class="sc-stats"><div><b>${fmt(s.offers || 0)}</b><span>${t("offersLbl")}</span></div><div><b>${fmt(s.cheapest)}</b><span>${t("cheapestOn")}</span></div></div>
        <div class="sc-foot">${t("updatedLbl", { d: esc(s.updated ? fmtDate(s.updated) : "–") })} · ${s.type === "feed" ? t("feed") : t("crawled")}</div>
        <a class="btn btn-ghost" href="/?shop=${s.id}&all=1">${t("showProducts")}</a></div>`).join("")}</div>
      <p class="muted small">${t("cheapestNote")}</p>`;
  }


  // ---------------------------------------------------------------- privacy
  const PRIVACY = {
    en: ["Privacy", "Last updated: 26.11.2026",
      [["What we collect", "Nothing about you personally. CompAirsoft has no user accounts, uses no cookies and runs no analytics, advertising or tracking scripts."],
       ["Stored in your browser", "Your choice of language and dark/light mode is saved in your browser's local storage so the site remembers it. It never leaves your device; you can delete it by clearing the site data in your browser."],
       ["Hosting (Cloudflare)", "The site is delivered by Cloudflare, Inc. To deliver it and protect it against attacks, Cloudflare processes technical data of each request, such as your IP address, browser type and the page requested. Legal basis: legitimate interest in running a secure website (Art. 6(1)(f) GDPR). See Cloudflare's privacy policy: https://www.cloudflare.com/privacypolicy/"],
       ["Product photos and shop links", "Product photos are shown as small copies stored on this website's own hosting. Only when you click a photo to enlarge it is the original loaded from the shop's server; that shop then receives your IP address and browser details (we tell your browser not to send which page you were on). When you click “Go to shop”, the shop's own privacy policy applies."],
       ["Fonts and icons", "Fonts and icons are served from this website itself; nothing is loaded from Google or other font services."],
       ["Your rights", "Under the GDPR you may ask for access to, correction or deletion of personal data, object to processing, and complain to a data protection authority (in the Czech Republic: Úřad pro ochranu osobních údajů, www.uoou.cz). As we store no personal data ourselves, requests about request logs are best directed to Cloudflare."]],
      "Contact"],
    cs: ["Ochrana soukromí", "Poslední aktualizace: 26.11.2026",
      [["Co shromažďujeme", "O vás osobně nic. CompAirsoft nemá uživatelské účty, nepoužívá cookies a nespouští žádné analytické, reklamní ani sledovací skripty."],
       ["Uloženo ve vašem prohlížeči", "Zvolený jazyk a tmavý/světlý režim se ukládají do místního úložiště vašeho prohlížeče, aby si je web pamatoval. Nikdy neopouštějí vaše zařízení; smažete je vymazáním dat webu v prohlížeči."],
       ["Hosting (Cloudflare)", "Web doručuje společnost Cloudflare, Inc. Aby ho mohla doručit a chránit před útoky, zpracovává technické údaje každého požadavku, např. vaši IP adresu, typ prohlížeče a požadovanou stránku. Právní základ: oprávněný zájem na provozu bezpečného webu (čl. 6 odst. 1 písm. f) GDPR). Zásady ochrany soukromí Cloudflare: https://www.cloudflare.com/privacypolicy/"],
       ["Fotografie produktů a odkazy do obchodů", "Fotografie produktů zobrazujeme jako zmenšené kopie uložené na hostingu tohoto webu. Teprve když fotku kliknutím zvětšíte, načte se originál ze serveru obchodu; ten pak obdrží vaši IP adresu a údaje o prohlížeči (prohlížeči zakazujeme posílat, na které stránce jste byli). Po kliknutí na „Do obchodu“ platí zásady ochrany soukromí daného obchodu."],
       ["Písma a ikony", "Písma a ikony poskytuje přímo tento web; nic se nenačítá od Googlu ani jiných služeb."],
       ["Vaše práva", "Podle GDPR můžete požádat o přístup k osobním údajům, jejich opravu či výmaz, vznést námitku proti zpracování a podat stížnost u dozorového úřadu (v ČR: Úřad pro ochranu osobních údajů, www.uoou.cz). Protože sami žádné osobní údaje neukládáme, žádosti týkající se záznamů o požadavcích směřujte na Cloudflare."]],
      "Kontakt"],
    sk: ["Ochrana súkromia", "Posledná aktualizácia: 26.11.2026",
      [["Čo zhromažďujeme", "O vás osobne nič. CompAirsoft nemá používateľské účty, nepoužíva cookies a nespúšťa žiadne analytické, reklamné ani sledovacie skripty."],
       ["Uložené vo vašom prehliadači", "Zvolený jazyk a tmavý/svetlý režim sa ukladajú do lokálneho úložiska vášho prehliadača, aby si ich web pamätal. Nikdy neopúšťajú vaše zariadenie; vymažete ich vymazaním údajov webu v prehliadači."],
       ["Hosting (Cloudflare)", "Web doručuje spoločnosť Cloudflare, Inc. Aby ho mohla doručiť a chrániť pred útokmi, spracúva technické údaje každej požiadavky, napr. vašu IP adresu, typ prehliadača a požadovanú stránku. Právny základ: oprávnený záujem na prevádzke bezpečného webu (čl. 6 ods. 1 písm. f) GDPR). Zásady ochrany súkromia Cloudflare: https://www.cloudflare.com/privacypolicy/"],
       ["Fotografie produktov a odkazy do obchodov", "Fotografie produktov zobrazujeme ako zmenšené kópie uložené na hostingu tohto webu. Až keď fotku kliknutím zväčšíte, načíta sa originál zo servera obchodu; ten potom dostane vašu IP adresu a údaje o prehliadači (prehliadaču zakazujeme posielať, na ktorej stránke ste boli). Po kliknutí na „Do obchodu“ platia zásady ochrany súkromia daného obchodu."],
       ["Písma a ikony", "Písma a ikony poskytuje priamo tento web; nič sa nenačítava od Googlu ani iných služieb."],
       ["Vaše práva", "Podľa GDPR môžete požiadať o prístup k osobným údajom, ich opravu či vymazanie, namietať proti spracúvaniu a podať sťažnosť dozornému orgánu (na Slovensku: Úrad na ochranu osobných údajov SR, v ČR: ÚOOÚ). Keďže sami žiadne osobné údaje neukladáme, žiadosti týkajúce sa záznamov o požiadavkách smerujte na Cloudflare."]],
      "Kontakt"],
    de: ["Datenschutz", "Stand: 26.11.2026",
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
    const linkify = (text) => esc(text).replace(/https:\/\/[^\s)]+/g, (u) => `<a href="${esc(safeUrl(u.replaceAll("&amp;", "&")))}" rel="noopener noreferrer" target="_blank">${u}</a>`);
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
      PARAMS = m.params || {}; PSECT = m.paramSections || {}; CATP = m.catParams || {};
      RATES = { [BASE]: 1, ...(m.rates || {}) };
      if (!RATES[cur]) cur = BASE;
      document.getElementById("cur").value = cur;
      document.getElementById("updated").textContent = t("updated", { d: fmtDate(m.generated) })
        + (cur !== BASE && m.rates_date ? " " + t("ratesNote", { c: cur, d: fmtDate(m.rates_date) }) : "");
      catbarFollow(null);
      if (page === "product") return await product();
      if (page === "shops") return shopsPage(m);
      if (page === "privacy") return privacyPage();
      const p = P();
      const filtered = ["q", "cat", "shop", "stock", "multi", "minshops", "save", "pmin", "pmax", "all", "brand", ...paramKeys()].some((k) => p.get(k))
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
      if (e.target.closest("[data-params]") && openParams) return openParams();
      const more = e.target.closest("[data-more]");
      if (more) {
        const g = more.closest(".f-sec, .f-group"); g.classList.toggle("expanded");
        if (!more.dataset.more2) more.dataset.more2 = more.textContent;
        more.textContent = g.classList.contains("expanded") ? (more.dataset.less || t("showLess")) : more.dataset.more2;
        return;
      }
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
      box.innerHTML = `<button type="button" class="lb-close" aria-label="×">${icon("x")}</button><img src="${esc(safeUrl(z.dataset.orig))}" alt="" referrerpolicy="no-referrer">`;
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
