// Copyright (c) 2026 Internet Archive
//
// Author: Derek Fukumori
// Generated with assistance from Claude Opus 5 (claude-opus-5)
"use strict";

const $ = (id) => document.getElementById(id);
const state = { year: "", circuit: "", claim: "", type: "", court: "", by: "", q: "" };
const CL = "https://www.courtlistener.com";
const IA = "https://archive.org";
const PAGE = 100;
let dockets = [];
let coverage = {};
let held = {};  // docket id → {item, documents: {filing id: "<doc>.<att>"}}, from data/filings_ia.json
let shownCount = PAGE;

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

const year = (f) => (f.date || "").slice(0, 4);

// Everything the search box looks through, built once per docket: the docket's
// own fields plus every filing's description and filer.
const hay = new WeakMap();
function haystack(d) {
  if (!hay.has(d)) {
    hay.set(d, [d.case, d.docket, d.court, d.state, d.circuit, d.claim, d.nature,
      ...d.filings.map((f) => `${f.type} ${f.filer} ${f.description}`)]
      .filter(Boolean).join(" \u0001 ").toLowerCase());
  }
  return hay.get(d);
}

// Two levels of filter: some narrow the docket, some narrow the filings on it.
// A docket is shown when it passes its own filters and keeps at least one
// filing; only the filings that passed are listed under it.
function docketPasses(d, ignore) {
  if (ignore !== "circuit" && state.circuit && d.circuit !== state.circuit) return false;
  if (ignore !== "claim" && state.claim && d.claim !== state.claim) return false;
  if (state.court && d.court !== state.court) return false;
  if (state.q && !state.q.toLowerCase().split(/\s+/).every((w) => haystack(d).includes(w))) return false;
  return true;
}

function filingPasses(f, ignore) {
  if (ignore !== "year" && state.year && year(f) !== state.year) return false;
  if (ignore !== "type" && state.type && f.type !== state.type) return false;
  if (state.by && f.by !== state.by) return false;
  return true;
}

function kept(d, ignore) {
  return d.filings.filter((f) => filingPasses(f, ignore));
}

function shown(ignore) {
  const out = [];
  for (const d of dockets) {
    if (!docketPasses(d, ignore)) continue;
    const fs = kept(d, ignore);
    if (fs.length) out.push([d, fs]);
  }
  return out;
}

// Gridlines for a bar chart whose tallest bar is `max`: 0, then whole-number
// steps of 1, 2 or 5 × 10^n, at most five of them. As on the opinions page.
function drawScale(id, max) {
  const pow = 10 ** Math.floor(Math.log10(max / 5));
  const step = Math.max(1, [1, 2, 5, 10].map((m) => m * pow).find((s) => s >= max / 5));
  const label = (v) => v >= 1000 ? new Intl.NumberFormat("en", { notation: "compact" }).format(v) : v;
  let html = '<div class="zero" style="bottom:0"><span>0</span></div>';
  for (let v = step; v <= max; v += step) html += `<div style="bottom:${(v / max) * 100}%"><span>${label(v)}</span></div>`;
  $(id).innerHTML = html;
}

function drawChart() {
  const counts = {};
  for (const [, fs] of shown("year")) {
    for (const f of fs) {
      const y = year(f);
      if (!y) continue;
      counts[y] = counts[y] || { party: 0, court: 0 };
      counts[y][f.by]++;
    }
  }
  const years = Object.keys(counts).sort();
  if (!years.length) { $("chart").innerHTML = ""; $("axis").innerHTML = ""; return; }
  const first = +years[0], last = +years[years.length - 1];
  const max = Math.max(1, ...Object.values(counts).map((c) => c.party + c.court));
  const chart = $("chart");
  chart.innerHTML = "";
  for (let y = first; y <= last; y++) {
    const c = counts[y] || { party: 0, court: 0 };
    const total = c.party + c.court;
    const b = document.createElement("button");
    b.className = "col" + (state.year === String(y) ? " on" : "");
    b.title = `${y}: ${total} filing${total === 1 ? "" : "s"}` +
      (c.court ? ` (${c.court} by the court)` : "");
    b.setAttribute("aria-label", b.title);
    b.setAttribute("aria-pressed", state.year === String(y));
    // Court-authored sits on top, so the darker band reads against the baseline.
    b.innerHTML =
      `<span class="court" style="height:${(c.court / max) * 100}%"></span>` +
      `<span class="party" style="height:${(c.party / max) * 100}%"></span>`;
    b.onclick = () => { state.year = state.year === String(y) ? "" : String(y); shownCount = PAGE; render(); };
    chart.appendChild(b);
  }
  $("axis").innerHTML = `<span>${first}</span><span>${last}</span>`;
  $("legend").innerHTML =
    '<span><i class="party"></i>Filed by a party or amicus</span>' +
    '<span><i class="court"></i>Written by the court</span>';
  drawScale("chart-ticks", max);
}

// `key` reads the value off a docket; `level` says whether the facet counts
// dockets or the filings on them.
function drawFacet(id, field, level) {
  const counts = {};
  for (const [d, fs] of shown(field)) {
    if (level === "filing") for (const f of fs) counts[f.type] = (counts[f.type] || 0) + 1;
    else counts[d[field]] = (counts[d[field]] || 0) + 1;
  }
  const entries = Object.entries(counts).filter(([v]) => v).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map(([, n]) => n));
  const el = $(id);
  el.innerHTML = "";
  for (const [v, n] of entries) {
    const b = document.createElement("button");
    if (state[field] === v) b.className = "on";
    b.setAttribute("aria-pressed", state[field] === v);
    b.innerHTML = `<span class="lbl">${esc(v)}</span><span class="n">${n}</span>` +
      `<span class="bar" style="width:${(n / max) * 100}%"></span>`;
    b.onclick = () => { state[field] = state[field] === v ? "" : v; shownCount = PAGE; render(); };
    el.appendChild(b);
  }
}

// A filing links to its PDF in archive.org's RECAP collection when the item for
// its docket holds that exact document, and to CourtListener otherwise.
function filingRow(f, ia) {
  const bits = [];
  if (f.date) bits.push(esc(f.date));
  if (f.filer) bits.push(esc(f.filer));
  const doc = ia?.documents[f.id];
  const link = doc
    ? `<a href="${esc(`${IA}/download/${ia.item}/${ia.item}.${doc}.pdf`)}">document on archive.org</a>`
    : f.url
    ? `<a href="${esc(CL + f.url)}">document on CourtListener</a>`
    : `<span class="unavailable">no link recorded</span>`;
  const avail = f.available ? "" : `<span class="unavailable">not fetched from PACER</span>`;
  return `<div class="filing">
    <div class="entry">${f.entry ? "No. " + esc(f.entry) : "&mdash;"}</div>
    <div>
      <p class="what">${esc(f.type)}${f.by === "court" ? '<span class="byline">by the court</span>' : ""}</p>
      ${f.description ? `<p class="desc">${esc(f.description)}</p>` : ""}
      <p class="sub">${link}${bits.length ? " &middot; " + bits.join(" &middot; ") : ""}${avail}</p>
    </div>
  </div>`;
}

// The archive.org item holds the documents but not the docket sheet, so a held
// docket links to both: archive.org first, CourtListener for the full entry list.
function docketLinks(d, ia) {
  const links = [];
  if (ia) links.push(`<a href="${esc(`${IA}/details/${ia.item}`)}">Documents on archive.org</a>`);
  if (d.url) links.push(`<a href="${esc(CL + d.url)}">Full docket on CourtListener</a>`);
  return links.length ? `<p class="sub ui" style="margin:8px 0 0">${links.join(" &middot; ")}</p>` : "";
}

function card(d, fs) {
  const ia = held[d.id];
  const meta = [esc(d.court), d.docket ? "No. " + esc(d.docket) : "", esc(d.claim),
    d.nature ? esc(d.nature) : "", d.filed ? "filed " + esc(d.filed) : ""].filter(Boolean).join(" &middot; ");
  const all = fs.length === d.filings.length
    ? `${fs.length} filing${fs.length === 1 ? "" : "s"}`
    : `${fs.length} of ${d.filings.length} filings`;
  return `<article><details>
    <summary>
      <span class="turn">&#9654;</span><h3>${esc(d.case)}</h3>
      <p class="docket-meta ui">${meta} &middot; ${all}</p>
      <p class="via ui">via ${ia ? "RECAP at Internet Archive" : "CourtListener"}</p>
    </summary>
    <div class="filings">${fs.map((f) => filingRow(f, ia)).join("")}</div>
    ${docketLinks(d, ia)}
    ${wikipedia(coverage[d.id] || [])}
  </details></article>`;
}

// Wikipedia articles about the lawsuit, from data/filings_coverage.json, in a
// "Wikipedia" section as on the opinion cards. Each was read and checked to be
// about this case before it was added.
function wikipedia(links) {
  if (!links.length) return "";
  const items = links.map((c) => `<li><a href="${esc(c.url)}">${esc(c.title)}</a></li>`).join("");
  return `<div class="press ui"><h4>Wikipedia</h4><ul>${items}</ul></div>`;
}

function render() {
  writeURL();
  $("q").value = state.q;
  $("court").value = state.court;
  $("by").value = state.by;
  drawChart();
  drawFacet("circuits", "circuit", "docket");
  drawFacet("claims", "claim", "docket");
  drawFacet("types", "type", "filing");

  const rows = shown("");
  const nFilings = rows.reduce((n, [, fs]) => n + fs.length, 0);
  const total = dockets.reduce((n, d) => n + d.filings.length, 0);
  const filtered = Object.values(state).some(Boolean);
  $("searchcount").textContent = state.q
    ? `${rows.length} of ${dockets.length} dockets match “${state.q}”` : "";
  $("status").innerHTML =
    `${rows.length.toLocaleString()} of ${dockets.length.toLocaleString()} dockets · ` +
    `${nFilings.toLocaleString()} of ${total.toLocaleString()} filings` +
    (filtered ? ' · <button id="clear">clear filters</button>' : "");
  if (filtered) $("clear").onclick = () => { for (const k in state) state[k] = ""; shownCount = PAGE; render(); };

  const slice = rows.slice(0, shownCount);
  $("list").innerHTML = slice.map(([d, fs]) => card(d, fs)).join("") || "<p>No filings match.</p>";
  const rest = rows.length - slice.length;
  $("more").hidden = rest <= 0;
  $("more").textContent = rest > 0 ? `Show ${Math.min(rest, PAGE)} more of ${rest.toLocaleString()} remaining` : "";
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
  dockets = await fetch("data/filings.json").then((r) => r.json());
  const fc = await fetch("data/filings_coverage.json").then((r) => r.ok ? r.json() : {}).catch(() => ({}));
  for (const [id, v] of Object.entries(fc.dockets || {})) coverage[id] = v.links;
  const ia = await fetch("data/filings_ia.json").then((r) => r.ok ? r.json() : {}).catch(() => ({}));
  held = ia.dockets || {};

  const courts = {};
  for (const d of dockets) courts[d.court] = (courts[d.court] || 0) + 1;
  fillSelect("court", Object.entries(courts).sort((a, b) => a[0].localeCompare(b[0]))
    .map(([name, n]) => [name, `${name} (${n})`]));

  const filings = dockets.reduce((n, d) => n + d.filings.length, 0);
  const byCourt = dockets.reduce((n, d) => n + d.filings.filter((f) => f.by === "court").length, 0);
  $("about").innerHTML =
    `${filings.toLocaleString()} filings on ${dockets.length.toLocaleString()} federal dockets, ` +
    `${byCourt} of them written by the court, from the <i>Wayback Machine in U.S. Courts</i> workbook ` +
    `(as of 2026-09-18), which searched CourtListener's RECAP index for the exact phrase ` +
    `“Wayback Machine”. Matters where the Internet Archive is itself a party are left out. ` +
    `A floor, not a census: RECAP holds only what someone bought from PACER, state-court briefs are ` +
    `largely absent, and a filing that cites an archived page another way is missed. Case type is the ` +
    `workbook's rules-based label. These filings show the archive in evidentiary use; they do not show ` +
    `that any capture was admitted, authenticated or judicially noticed. ` +
    (ia.filings_held ? `Documents link to archive.org's <a href="${IA}/details/usfederalcourts">RECAP collection</a>, ` +
      `part of Democracy's Library, wherever it holds them: ${ia.filings_held.toLocaleString()} of the ` +
      `${ia.filings_checked.toLocaleString()} filings and ${ia.dockets_held.toLocaleString()} of the ` +
      `${ia.dockets_checked.toLocaleString()} dockets as of ${esc(ia.built)}; the rest link to CourtListener. ` : "") +
    `<a href="https://github.com/internetarchivecanada/legal-opinions-using-wayback">Source and method</a>.`;

  readURL();
  let t;
  $("q").oninput = (e) => { clearTimeout(t); t = setTimeout(() => { state.q = e.target.value.trim(); shownCount = PAGE; render(); }, 150); };
  $("court").onchange = (e) => { state.court = e.target.value; shownCount = PAGE; render(); };
  $("by").onchange = (e) => { state.by = e.target.value; shownCount = PAGE; render(); };
  $("more").onclick = () => { shownCount += PAGE; render(); };
  render();
}

main();
