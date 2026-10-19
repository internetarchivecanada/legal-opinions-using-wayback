"use strict";

const $ = (id) => document.getElementById(id);
const state = { year: "", court: "", phrase: "", q: "" };
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

function matches(o, ignoreYear) {
  if (!ignoreYear && state.year && year(o) !== state.year) return false;
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
  for (const o of opinions) if (matches(o, true)) counts[year(o)] = (counts[year(o)] || 0) + 1;
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
  const shown = opinions.filter((o) => matches(o, false)).reverse();
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
