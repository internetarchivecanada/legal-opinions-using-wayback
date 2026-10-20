"use strict";

const $ = (id) => document.getElementById(id);
const state = { year: "", court: "", phrase: "", place: "", claim: "", level: "", q: "" };
let opinions = [];

function readURL() {
  const p = new URLSearchParams(location.search);
  for (const k of Object.keys(state)) state[k] = p.get(k) || "";
}

function writeURL() {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(state)) if (v) p.set(k, v);
  const qs = p.toString();
  history.replaceState(null, "", qs ? "?" + qs : location.pathname);
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// CourtListener snippets arrive as HTML with <mark> highlights. Escape all of
// it, then put back only the highlight tags.
function snippet(s) {
  return esc(s).replace(/&lt;(\/?)mark&gt;/g, "<$1mark>");
}

const year = (o) => (o.date || "").slice(0, 4);

// `ignore` names the one filter a chart leaves out, so its own bars or tiles
// still show every option.
function matches(o, ignore) {
  if (ignore !== "year" && state.year && year(o) !== state.year) return false;
  if (ignore !== "place" && state.place && o.state !== state.place) return false;
  if (ignore !== "claim" && state.claim && o.claim !== state.claim) return false;
  if (ignore !== "level" && state.level && o.court_level !== state.level) return false;
  if (state.court && o.court_id !== state.court) return false;
  if (state.phrase && !o.phrases.includes(state.phrase)) return false;
  if (state.q) {
    const hay = (o.case + " " + o.snippets.join(" ") + " " + o.docket).toLowerCase();
    if (!hay.includes(state.q.toLowerCase())) return false;
  }
  return true;
}

function drawChart() {
  const years = opinions.map(year).filter(Boolean).sort();
  if (!years.length) return;
  const first = +years[0], last = +years[years.length - 1];
  const counts = {};
  for (const o of opinions) if (matches(o, "year")) counts[year(o)] = (counts[year(o)] || 0) + 1;
  const max = Math.max(1, ...Object.values(counts));
  const chart = $("chart");
  chart.innerHTML = "";
  for (let y = first; y <= last; y++) {
    const n = counts[y] || 0;
    const b = document.createElement("button");
    b.style.height = n ? Math.max(4, (n / max) * 100) + "%" : "1px";
    b.title = `${y}: ${n} opinion${n === 1 ? "" : "s"}`;
    b.setAttribute("aria-label", b.title);
    if (state.year === String(y)) b.className = "on";
    b.onclick = () => { state.year = state.year === String(y) ? "" : String(y); render(); };
    chart.appendChild(b);
  }
  $("axis").innerHTML = `<span>${first}</span><span>${last}</span>`;
}

// Tile grid: one square per state at [column, row], roughly where it sits on a map.
const TILES = {
  AK: [0, 0], ME: [10, 0], VT: [9, 1], NH: [10, 1],
  WA: [0, 2], ID: [1, 2], MT: [2, 2], ND: [3, 2], MN: [4, 2], IL: [5, 2], WI: [6, 2], MI: [7, 2], NY: [8, 2], RI: [9, 2], MA: [10, 2],
  OR: [0, 3], NV: [1, 3], WY: [2, 3], SD: [3, 3], IA: [4, 3], IN: [5, 3], OH: [6, 3], PA: [7, 3], NJ: [8, 3], CT: [9, 3],
  CA: [0, 4], UT: [1, 4], CO: [2, 4], NE: [3, 4], MO: [4, 4], KY: [5, 4], WV: [6, 4], VA: [7, 4], MD: [8, 4], DE: [9, 4],
  AZ: [1, 5], NM: [2, 5], KS: [3, 5], AR: [4, 5], TN: [5, 5], NC: [6, 5], SC: [7, 5], DC: [8, 5],
  OK: [3, 6], LA: [4, 6], MS: [5, 6], AL: [6, 6], GA: [7, 6],
  HI: [0, 7], TX: [3, 7], FL: [8, 7],
};
const STATE_NAMES = {
  AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California", CO: "Colorado", CT: "Connecticut",
  DE: "Delaware", DC: "District of Columbia", FL: "Florida", GA: "Georgia", HI: "Hawaii", ID: "Idaho", IL: "Illinois",
  IN: "Indiana", IA: "Iowa", KS: "Kansas", KY: "Kentucky", LA: "Louisiana", ME: "Maine", MD: "Maryland",
  MA: "Massachusetts", MI: "Michigan", MN: "Minnesota", MS: "Mississippi", MO: "Missouri", MT: "Montana",
  NE: "Nebraska", NV: "Nevada", NH: "New Hampshire", NJ: "New Jersey", NM: "New Mexico", NY: "New York",
  NC: "North Carolina", ND: "North Dakota", OH: "Ohio", OK: "Oklahoma", OR: "Oregon", PA: "Pennsylvania",
  RI: "Rhode Island", SC: "South Carolina", SD: "South Dakota", TN: "Tennessee", TX: "Texas", UT: "Utah",
  VT: "Vermont", VA: "Virginia", WA: "Washington", WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming",
};
const NATIONWIDE = "Nationwide/Other";
const placeName = (p) => p === NATIONWIDE ? "Federal appeals and nationwide courts" : STATE_NAMES[p] || p;

function placeButton(p, n, max) {
  const b = document.createElement("button");
  b.dataset.place = p;
  // Square-root scale, so a few large states don't wash out the rest.
  const pct = n ? Math.round(15 + 85 * Math.sqrt(n / max)) : 0;
  b.style.setProperty("--fill", pct + "%");
  // Light text only once the fill is dark enough to keep 4.5:1 contrast.
  if (pct > 75) b.classList.add("dark");
  if (state.place === p) b.classList.add("on");
  b.title = `${placeName(p)}: ${n} opinion${n === 1 ? "" : "s"}`;
  b.setAttribute("aria-label", b.title);
  b.setAttribute("aria-pressed", state.place === p);
  b.onclick = () => { state.place = state.place === p ? "" : p; render(); };
  return b;
}

function drawMap() {
  const counts = {};
  for (const o of opinions) if (matches(o, "place")) counts[o.state] = (counts[o.state] || 0) + 1;
  const max = Math.max(1, ...Object.keys(TILES).map((p) => counts[p] || 0));
  // Redrawing replaces the buttons, so put focus back on the one that had it.
  const focused = document.activeElement?.dataset?.place;
  const map = $("map");
  map.innerHTML = "";
  for (const [p, [col, row]] of Object.entries(TILES)) {
    const b = placeButton(p, counts[p] || 0, max);
    b.style.gridColumn = col + 1;
    b.style.gridRow = row + 1;
    b.innerHTML = `<span>${p}</span><span class="n">${counts[p] || ""}</span>`;
    map.appendChild(b);
  }
  // Shaded only when picked: its count is on another scale from the states.
  const nat = placeButton(NATIONWIDE, 0, max);
  nat.innerHTML = `<strong>${counts[NATIONWIDE] || 0}</strong> from ${placeName(NATIONWIDE).toLowerCase()}, with no single state`;
  $("nationwide").replaceChildren(nat);
  if (focused) document.querySelector(`[data-place="${CSS.escape(focused)}"]`)?.focus();
}

// A list of horizontal bars, one per value, that filters like the year chart:
// its counts leave out its own filter so every option stays visible.
function drawFacet(id, key, value) {
  const counts = {};
  for (const o of opinions) if (matches(o, key)) { const v = value(o) || "Unknown"; counts[v] = (counts[v] || 0) + 1; }
  const rows = Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const max = Math.max(1, ...rows.map((r) => r[1]));
  const focused = document.activeElement?.dataset?.facet === key ? document.activeElement.dataset.value : null;
  const el = $(id);
  el.innerHTML = "";
  for (const [v, n] of rows) {
    const b = document.createElement("button");
    b.dataset.facet = key;
    b.dataset.value = v;
    if (state[key] === v) b.classList.add("on");
    b.setAttribute("aria-pressed", state[key] === v);
    b.innerHTML = `<span class="lbl">${esc(v)}</span><span class="n">${n}</span><span class="bar" style="width:${(n / max) * 100}%"></span>`;
    b.onclick = () => { state[key] = state[key] === v ? "" : v; render(); };
    el.appendChild(b);
  }
  if (focused) el.querySelector(`[data-value="${CSS.escape(focused)}"]`)?.focus();
}

// RECAP filings per year, stacked by who filed them. A separate dataset from
// the opinions, so the filters above don't apply to it.
function drawFilings(f) {
  const max = Math.max(1, ...f.years.map((y) => y.party + y.court));
  const total = (k) => f.years.reduce((s, y) => s + y[k], 0);
  $("filings-chart").innerHTML = f.years.map((y) => {
    const n = y.party + y.court;
    const label = `${y.year}: ${y.party} party filings, ${y.court} court documents`;
    return `<div class="col" title="${label}" aria-label="${label}" role="img">` +
      `<span class="court" style="height:${(y.court / max) * 100}%"></span>` +
      `<span class="party" style="height:${(y.party / max) * 100}%"></span></div>`;
  }).join("");
  $("filings-axis").innerHTML = `<span>${f.years[0].year}</span><span>${f.years[f.years.length - 1].year} (to ${esc(f.as_of)})</span>`;
  $("filings-legend").innerHTML =
    `<span><i class="party"></i>${total("party").toLocaleString()} filed by parties or amici</span>` +
    `<span><i class="court"></i>${total("court").toLocaleString()} court orders and opinions</span>`;
}

function card(o) {
  const cites = o.citations.length ? " · " + esc(o.citations.join(", ")) : "";
  const pdf = o.pdfs.length ? ` · <a href="${esc(o.pdfs[0])}">court PDF</a>` : "";
  const tags = o.phrases.map((p) => `<span class="tag">${esc(p)}</span>`).join("");
  const snips = o.snippets.slice(0, 2).map((s) => `<p class="snip">…${snippet(s)}…</p>`).join("");
  return `<article>
    <h3><a href="${esc(o.url)}">${esc(o.case)}</a></h3>
    <div class="meta ui">${esc(o.court)} · ${esc(o.date)}${o.docket ? " · No. " + esc(o.docket) : ""}${cites}${pdf}</div>
    <div class="ui">${tags}</div>
    ${snips}
  </article>`;
}

function render() {
  writeURL();
  $("q").value = state.q;
  $("court").value = state.court;
  $("phrase").value = state.phrase;
  drawChart();
  drawMap();
  drawFacet("claims", "claim", (o) => o.claim);
  drawFacet("levels", "level", (o) => o.court_level);
  const shown = opinions.filter((o) => matches(o, "")).reverse();
  const filtered = Object.values(state).some(Boolean);
  $("status").innerHTML = `${shown.length} of ${opinions.length} opinions` +
    (filtered ? ' · <button id="clear">clear filters</button>' : "");
  if (filtered) $("clear").onclick = () => { for (const k in state) state[k] = ""; render(); };
  let html = "", current = null;
  for (const o of shown) {
    if (year(o) !== current) { current = year(o); html += `<h2 class="year">${esc(current || "Undated")}</h2>`; }
    html += card(o);
  }
  $("list").innerHTML = html || "<p>No opinions match.</p>";
}

function fillSelect(id, pairs) {
  const sel = $(id);
  for (const [value, label] of pairs) {
    const opt = document.createElement("option");
    opt.value = value; opt.textContent = label;
    sel.appendChild(opt);
  }
}

async function main() {
  const [ops, meta] = await Promise.all([
    fetch("data/opinions.json").then((r) => r.json()),
    fetch("data/harvest.json").then((r) => r.json()),
  ]);
  opinions = ops;
  fetch("data/filings_by_year.json").then((r) => r.json()).then(drawFilings)
    .catch(() => { $("filings").hidden = true; });
  const courts = {};
  for (const o of opinions) courts[o.court_id] = courts[o.court_id] || { name: o.court, n: 0 }, courts[o.court_id].n++;
  fillSelect("court", Object.entries(courts).sort((a, b) => a[1].name.localeCompare(b[1].name))
    .map(([id, c]) => [id, `${c.name} (${c.n})`]));
  fillSelect("phrase", [...new Set(opinions.flatMap((o) => o.phrases))].map((p) => [p, `"${p}"`]));
  $("about").innerHTML = `Harvested ${esc(meta.started.slice(0, 10))} from ${esc(meta.source)}, by exact phrase: ` +
    meta.searches.filter((s) => s.received !== null).map((s) => esc(s.query)).join(", ") +
    `. A floor, not a census: opinions that cite an archived page without one of these phrases are missed. ` +
    `<a href="https://github.com/internetarchivecanada/legal-opinions-using-wayback">Source and method</a>.`;

  readURL();
  let t;
  $("q").oninput = (e) => { clearTimeout(t); t = setTimeout(() => { state.q = e.target.value.trim(); render(); }, 150); };
  $("court").onchange = (e) => { state.court = e.target.value; render(); };
  $("phrase").onchange = (e) => { state.phrase = e.target.value; render(); };
  render();
}

main().catch((e) => { $("status").textContent = "Could not load the data: " + e.message; });
