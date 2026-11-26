"use strict";
(() => {
  const { cats: CATS, groups: GROUPS, groupOf: GROUP_OF, currency: CUR } = window.SITE;
  const V = document.documentElement.dataset.v;
  const app = document.getElementById("app");
  const PAGE_SIZE = 48;
  const SORTS = [["relevance", "Most compared"], ["price_asc", "Cheapest"], ["price_desc", "Most expensive"],
                 ["savings", "Biggest saving"], ["name", "Name"]];

  // Links and images come from shop data: allow only absolute http(s) URLs (no javascript:, data:…).
  const safeUrl = (u) => {
    try {
      const x = new URL(String(u ?? ""));
      return x.protocol === "http:" || x.protocol === "https:" ? x.href : "";
    } catch { return ""; }
  };
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const json = (u) => fetch(`${u}?v=${V}`).then((r) => { if (!r.ok) throw new Error(`${u}: ${r.status}`); return r.json(); });
  const fold = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const fmt = (n) => Math.round(n).toLocaleString("cs-CZ").replace(/\s/g, " ");
  const money = (v) => {
    if (v == null) return "–";
    const s = CUR === "CZK" ? fmt(v) : v.toLocaleString("cs-CZ", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return s + ({ CZK: " Kč", EUR: " €", PLN: " zł" }[CUR] || " " + CUR);
  };
  const cat = (slug) => CATS[slug] || CATS.other;
  const params = new URLSearchParams(location.search);
  const url = (over) => {
    const p = new URLSearchParams(location.search);
    for (const [k, v] of Object.entries(over)) (v === "" || v == null) ? p.delete(k) : p.set(k, v);
    const s = p.toString();
    return "/" + (s ? "?" + s : "");
  };
  let metaP;
  const meta = () => (metaP ||= json("/data/meta.json"));

  // ---------------------------------------------------------------- pieces
  function card(p) {
    const c = cat(p.c);
    const save = p.s > 1 && p.x > p.p ? `<span class="badge-save">−${Math.round((1 - p.p / p.x) * 100)} %</span>` : "";
    const stock = p.k
      ? `<div class="stock yes">In stock${p.s > 1 ? ` · ${p.k} of ${p.s} shops` : ""}</div>`
      : `<div class="stock no">Out of stock</div>`;
    return `<a class="card" href="/product/${p.id}">
      <div class="thumb">${safeUrl(p.i) ? `<img src="${esc(safeUrl(p.i))}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ""}
        <span class="ph">${c[1]}</span>${save}</div>
      <div class="card-body">
        <div class="name">${esc(p.t)}</div>${stock}
        <div class="price-row"><div class="price">${p.s > 1 ? "<small>from</small> " : ""}${money(p.p)}</div></div>
        <div class="cmp ${p.s > 1 ? "multi" : ""}">${p.s > 1 ? `Compare ${p.s} shops ›` : "1 shop"}</div>
      </div></a>`;
  }
  const row = (title, more, items) => items.length ? `
    <div class="sec-head"><h2 class="sec-title">${esc(title)}</h2>${more ? `<a href="${more}">Show all ›</a>` : ""}</div>
    <div class="row-one">${items.map(card).join("")}</div>` : "";

  function markGroup(g) {
    document.querySelectorAll(".catbar a").forEach((a) => a.classList.toggle("on", a.dataset.group === g));
  }

  // ---------------------------------------------------------------- home
  function home(m) {
    const tiles = Object.entries(GROUPS).map(([g, [label, icon, subs]]) => {
      const total = subs.reduce((n, s) => n + (m.counts[s] || 0), 0);
      if (!total) return "";
      const links = subs.length > 1 ? `<div class="tile-subs">${subs.filter((s) => m.counts[s])
        .map((s) => `<a href="/?cat=${s}">${esc(CATS[s][0])}</a>`).join("")}</div>` : "";
      return `<div class="tile"><a class="tile-main" href="/?cat=${g}"><span class="tile-ico">${icon}</span>
        <span class="tile-name">${esc(label)}</span><span class="tile-n">${fmt(total)} products</span></a>${links}</div>`;
    }).join("");
    app.innerHTML = `
      <section class="hero"><div><h1>Find the cheapest airsoft gear</h1>
        <p>We compare <b>${fmt(m.stats.offers)}</b> offers from <b>${m.stats.shops}</b> airsoft shops, so you don't have to open every one.</p></div>
        <div class="hero-stats"><div><b>${fmt(m.stats.products)}</b><span>products</span></div>
          <div><b>${fmt(m.stats.compared)}</b><span>compared across shops</span></div>
          <div><b>${m.stats.shops}</b><span>shops</span></div></div></section>
      <h2 class="sec-title">Categories</h2><section class="tiles">${tiles}</section>
      ${m.sections.map((s) => row(s.title, s.more, s.items)).join("")}
      <div class="center"><a class="btn btn-big" href="/?all=1">Browse all ${fmt(m.stats.products)} products</a></div>`;
  }

  // ---------------------------------------------------------------- listing
  function matcher(q, syn) {
    const words = fold(q).split(/[^a-z0-9.]+/).filter(Boolean);
    const alts = words.map((w) => [w, ...(syn[w] || [])]);
    return (p) => {
      const t = (p._f ||= fold(p.t));
      return alts.every((opts) => opts.some((o) => t.includes(o)));
    };
  }

  async function listing(m) {
    const q = params.get("q") || "", c = params.get("cat") || "", shop = +params.get("shop") || 0;
    const stock = params.has("stock"), multi = params.has("multi");
    const pmin = parseFloat(params.get("pmin")), pmax = parseFloat(params.get("pmax"));
    const sort = params.get("sort") || "relevance", page = Math.max(1, +params.get("page") || 1);
    const group = GROUPS[c] ? c : GROUP_OF[c];
    markGroup(group);
    document.querySelector(".search input").value = q;
    app.innerHTML = `<div class="loading">Loading products…</div>`;

    const files = group ? [group] : Object.keys(GROUPS);
    let items = (await Promise.all(files.map((g) => json(`/data/g/${g}.json`)))).flat();
    if (c && CATS[c]) items = items.filter((p) => p.c === c);
    if (q) items = items.filter(matcher(q, m.syn));
    if (shop) items = items.filter((p) => p.h.includes(shop));
    if (stock) items = items.filter((p) => p.k > 0);
    if (multi) items = items.filter((p) => p.s > 1);
    if (!isNaN(pmin)) items = items.filter((p) => p.p >= pmin);
    if (!isNaN(pmax)) items = items.filter((p) => p.p <= pmax);
    const by = {
      relevance: (a, b) => b.s - a.s || a.p - b.p, shops: (a, b) => b.s - a.s || a.p - b.p,
      price_asc: (a, b) => a.p - b.p, price_desc: (a, b) => b.p - a.p,
      savings: (a, b) => (b.x - b.p) - (a.x - a.p), name: (a, b) => a.t.localeCompare(b.t, "cs"),
    }[sort] || ((a, b) => b.s - a.s || a.p - b.p);
    items.sort(by);
    const total = items.length, pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const shown = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

    const title = q ? `“${esc(q)}”` : GROUPS[c] ? esc(GROUPS[c][0]) : CATS[c] ? esc(CATS[c][0]) : "All products";
    document.title = `${q || (GROUPS[c] || CATS[c] || ["All products"])[0]} – CompAirsoft`;
    const subs = group && GROUPS[group][2].length > 1 ? `<nav class="subcats" aria-label="Subcategories">
      <a href="${url({ cat: group, page: "" })}" class="${c === group ? "on" : ""}">All ${esc(GROUPS[group][0].toLowerCase())}</a>
      ${GROUPS[group][2].filter((s) => m.counts[s]).map((s) => `<a href="${url({ cat: s, page: "" })}" class="${c === s ? "on" : ""}">${CATS[s][1]} ${esc(CATS[s][0])} <b>${fmt(m.counts[s])}</b></a>`).join("")}
      </nav>` : "";
    const hidden = (k) => params.get(k) ? `<input type="hidden" name="${k}" value="${esc(params.get(k))}">` : "";
    app.innerHTML = `<div class="layout">
      <aside class="filters"><details class="filters-box" ${innerWidth >= 900 ? "open" : ""}><summary>Filters</summary>
        <form method="get" action="/">${hidden("q")}${hidden("cat")}${hidden("sort")}<input type="hidden" name="all" value="1">
          <div class="f-group"><div class="f-title">Price (${CUR === "CZK" ? "Kč" : CUR})</div><div class="range">
            <input type="number" name="pmin" value="${isNaN(pmin) ? "" : pmin}" min="0" inputmode="numeric" placeholder="from" aria-label="Minimum price"><span>–</span>
            <input type="number" name="pmax" value="${isNaN(pmax) ? "" : pmax}" min="0" inputmode="numeric" placeholder="to" aria-label="Maximum price"></div></div>
          <div class="f-group"><div class="f-title">Availability</div>
            <label class="check"><input type="checkbox" name="stock" value="1" ${stock ? "checked" : ""} data-autosubmit> In stock only</label>
            <label class="check"><input type="checkbox" name="multi" value="1" ${multi ? "checked" : ""} data-autosubmit> Sold in 2+ shops</label></div>
          <div class="f-group"><div class="f-title">Shop</div><select name="shop" data-autosubmit aria-label="Shop">
            <option value="">All shops</option>${m.shops.map((s) => `<option value="${s.id}" ${s.id === shop ? "selected" : ""}>${esc(s.name)}</option>`).join("")}
          </select></div>
          <button type="submit" class="btn">Show results</button></form></details></aside>
      <section class="results">
        <div class="results-head"><h1>${title}</h1><span class="muted">${fmt(total)} product${total === 1 ? "" : "s"}</span></div>
        ${subs}
        <nav class="sort-tabs" aria-label="Sort">${SORTS.map(([k, l]) => `<a href="${url({ sort: k, page: "" })}" class="${sort === k ? "on" : ""}">${l}</a>`).join("")}</nav>
        ${total ? `<div class="grid">${shown.map(card).join("")}</div>` : `<div class="empty">Nothing matches these filters.</div>`}
        ${pages > 1 ? `<nav class="pager">${page > 1 ? `<a href="${url({ page: page - 1 })}">‹ Previous</a>` : ""}
          <span>Page ${page} of ${pages}</span>${page < pages ? `<a href="${url({ page: page + 1 })}">Next ›</a>` : ""}</nav>` : ""}
      </section></div>`;
  }

  // ---------------------------------------------------------------- product
  const PALETTE = ["#4f9d69", "#d9822b", "#3a7bd5", "#c94f6d", "#8e6cc9", "#2aa7a0", "#b8a12d", "#7a7a7a"];
  function chart(hist) {
    const shops = Object.keys(hist);
    const pts = shops.flatMap((s) => hist[s]);
    const days = [...new Set(pts.map((p) => p[0]))].sort();
    if (days.length < 2) return "";
    const t = (d) => Date.parse(d), t0 = t(days[0]), t1 = t(days[days.length - 1]);
    let lo = Math.min(...pts.map((p) => p[1])), hi = Math.max(...pts.map((p) => p[1]));
    const pad = (hi - lo) * 0.1 || hi * 0.05 || 1; lo -= pad; hi += pad;
    const W = 1000, H = 280, L = 70, R = 12, T = 10, B = 26;
    const x = (d) => L + (W - L - R) * (t(d) - t0) / (t1 - t0), y = (v) => T + (H - T - B) * (1 - (v - lo) / (hi - lo));
    const lines = shops.map((s, n) => {
      const ser = hist[s]; let d = `M${x(ser[0][0]).toFixed(1)},${y(ser[0][1]).toFixed(1)}`;
      for (let i = 1; i < ser.length; i++) d += `H${x(ser[i][0]).toFixed(1)}V${y(ser[i][1]).toFixed(1)}`;
      const last = ser[ser.length - 1];
      return { s, color: PALETTE[n % PALETTE.length], d, cx: x(last[0]), cy: y(last[1]) };
    });
    const ticks = [0, 1, 2, 3].map((k) => lo + (hi - lo) * k / 3);
    return `<h2 class="sec-title">Price history</h2><div class="chart">
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Price history per shop">
        ${ticks.map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" class="grid-line"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" class="axis">${money(v)}</text>`).join("")}
        <text x="${L}" y="${H - 6}" class="axis">${days[0]}</text><text x="${W - R}" y="${H - 6}" text-anchor="end" class="axis">${days[days.length - 1]}</text>
        ${lines.map((l) => `<path d="${l.d}" fill="none" stroke="${l.color}" stroke-width="2.5" stroke-linejoin="round"/><circle cx="${l.cx}" cy="${l.cy}" r="4" fill="${l.color}"/>`).join("")}
      </svg><div class="legend">${lines.map((l) => `<span><svg class="sw" width="14" height="4" aria-hidden="true"><rect width="14" height="4" rx="2" fill="${l.color}"/></svg>${esc(l.s)}</span>`).join("")}</div></div>`;
  }

  async function product() {
    const id = (location.pathname.match(/\/product\/([0-9a-f]+)/) || [])[1] || params.get("id") || "";
    const shard = id ? await json(`/data/p/${id.slice(0, 2)}.json`).catch(() => ({})) : {};
    const d = shard[id];
    if (!d) {
      app.innerHTML = `<div class="empty"><h1>Product not found</h1><p>It may have been merged with another listing after the last update.
        <a href="/">Search for it on the homepage</a>.</p></div>`;
      return;
    }
    const p = d.p, c = cat(p.c), g = GROUP_OF[p.c] || "misc";
    markGroup(g);
    document.title = `${p.t} – price comparison | CompAirsoft`;
    const live = d.o.filter((o) => o.a);
    const offers = d.o.map((o, i) => {
      const best = i === 0 && o.k !== 0 && o.a;
      const st = !o.a ? `<span class="stock no">Removed</span>` : o.k === 1 ? `<span class="stock yes">In stock</span>`
        : o.k === 0 ? `<span class="stock no">Out of stock</span>` : `<span class="stock">Availability unknown</span>`;
      const foreign = o.y && o.y !== CUR ? `<small>${o.r.toFixed(2)} ${esc(o.y)}</small>` : "";
      const link = safeUrl(o.u);
      return `<div class="offer ${best ? "best" : ""} ${o.a ? "" : "gone"}">
        <div class="o-shop"><b>${esc(o.s)}</b>${best && d.o.length > 1 ? `<span class="tag">Cheapest</span>` : ""}<div class="o-title">${esc(o.t)}</div></div>
        <div class="o-stock">${st}</div><div class="o-price">${money(o.v)}${foreign}</div>
        <a class="btn btn-shop" href="${link ? esc(link) : "#"}" target="_blank" rel="noopener noreferrer nofollow">Go to shop</a></div>`;
    }).join("");
    app.innerHTML = `
      <nav class="crumbs"><a href="/">Home</a><span>›</span><a href="/?cat=${g}">${esc(GROUPS[g][0])}</a>${GROUPS[g][2].length > 1 ? `<span>›</span><a href="/?cat=${p.c}">${esc(c[0])}</a>` : ""}</nav>
      <section class="pd"><div class="pd-img">${safeUrl(p.i) ? `<img src="${esc(safeUrl(p.i))}" alt="${esc(p.t)}" referrerpolicy="no-referrer">` : ""}<span class="ph">${c[1]}</span></div>
        <div class="pd-info"><h1>${esc(p.t)}</h1>
          <div class="pd-meta">${p.b ? `<span>Brand: <b>${esc(p.b)}</b></span>` : ""}<span>Category: <a href="/?cat=${p.c}">${esc(c[0])}</a></span>${p.e ? `<span>EAN: ${esc(p.e)}</span>` : ""}</div>
          <div class="pd-buy"><div>
            <div class="pd-price">${p.s > 1 ? "<small>from</small> " : ""}${money(p.p)}</div>
            ${p.s > 1 && p.x > p.p ? `<div class="pd-range">up to ${money(p.x)} · save <b>${money(p.x - p.p)}</b></div>` : ""}
            <div class="stock ${p.k ? "yes" : "no"}">${p.k ? `In stock at ${p.k} of ${p.s} shop${p.s === 1 ? "" : "s"}` : "Out of stock everywhere"}</div></div>
            <a class="btn btn-big" href="#offers">Compare ${live.length} offer${live.length === 1 ? "" : "s"}</a></div></div></section>
      <h2 class="sec-title" id="offers">Price comparison</h2><div class="offers">${offers}</div>
      ${chart(d.hist)}
      ${row(`Similar ${c[0].toLowerCase()}`, `/?cat=${p.c}`, d.sim)}`;
  }

  // ---------------------------------------------------------------- shops
  function shopsPage(m) {
    document.title = "Shops – CompAirsoft";
    app.innerHTML = `<div class="results-head"><h1>Shops we compare</h1><span class="muted">${m.shops.length} shops</span></div>
      <div class="shop-grid">${m.shops.map((s) => `<div class="shop-card">
        <div class="sc-head"><a class="sc-name" href="/?shop=${s.id}&all=1">${esc(s.name)}</a>${
          s.status && s.status.startsWith("error") ? `<span class="pill bad">Update failed</span>` : s.updated ? `<span class="pill good">Up to date</span>` : `<span class="pill">Loading…</span>`}</div>
        ${safeUrl(s.url) ? `<a class="sc-url" href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer nofollow">${esc(s.url.split("//").pop().replace(/\/$/, ""))}</a>` : ""}
        <div class="sc-stats"><div><b>${fmt(s.offers || 0)}</b><span>offers</span></div><div><b>${fmt(s.cheapest)}</b><span>cheapest on</span></div></div>
        <div class="sc-foot">Updated ${esc((s.updated || "–").replace("T", " "))} · ${s.type === "feed" ? "feed" : "crawled"}</div>
        <a class="btn btn-ghost" href="/?shop=${s.id}&all=1">Show products</a></div>`).join("")}</div>
      <p class="muted small">“Cheapest on” counts products that this shop sells for the lowest price among the shops that carry it.</p>`;
  }

  // Event handlers live here, not in inline on…= attributes, which the CSP blocks.
  // Broken shop images disappear (the category icon behind them shows instead).
  document.addEventListener("error", (e) => { if (e.target.tagName === "IMG") e.target.remove(); }, true);
  // Filter checkboxes and the shop dropdown submit the form when changed.
  document.addEventListener("change", (e) => { if (e.target.matches("[data-autosubmit]")) e.target.form.submit(); });

  // ---------------------------------------------------------------- router
  async function main() {
    const page = document.body.dataset.page;
    if (page === "404") return;
    try {
      const m = await meta();
      document.getElementById("updated").textContent = `Prices last updated ${m.generated.replace("T", " ")}.`;
      if (page === "product") return await product();
      if (page === "shops") return shopsPage(m);
      const filtered = ["q", "cat", "shop", "stock", "multi", "pmin", "pmax", "all"].some((k) => params.get(k))
        || (params.get("sort") || "relevance") !== "relevance" || +params.get("page") > 1;
      return filtered ? await listing(m) : home(m);
    } catch (e) {
      console.error(e);
      app.innerHTML = `<div class="empty">Couldn't load the data. Please refresh the page.</div>`;
    }
  }
  main();
})();
