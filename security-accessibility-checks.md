# Security and accessibility checks

**Status: not passing.** 2 of 3 checks have open items. Each one below has a recommended fix. Make the fixes, then re-run the explorer-checks skill. This file is replaced on every run.

| | |
|---|---|
| Explorer | https://github.com/internetarchivecanada/legal-opinions-using-wayback |
| Commit | `3c4b6efc9d` on `explorer-checks` |
| Date | 2026-11-05 |
| Pages checked | `./`, `./?year=2021`, `filings.html`, `filings.html?year=2020` |
| Served from | repository root, served locally |
| Live site (headers) | https://internetarchivecanada.github.io/legal-opinions-using-wayback/ |
| Standard | WCAG 2.2 Level AA |
| Security references | OWASP Top 10:2025 and ASVS 5.0.0 |
| Tools | axe-core 4.14.0, html5lib, ruff, bandit, pip-audit, headless Chromium |
| Reviewed by | Claude (claude-opus-5-5) via the explorer-checks skill |
| Skill version | 2026.11.05.8 |

## Summary

| Check | Result | Must fix | Needs review | Advisory |
|---|---|---:|---:|---:|
| Code validity | Pass | 0 | 0 | 1 |
| Code security | **Not passing** | 4 | 0 | 6 |
| Accessibility (WCAG 2.2 AA) | **Not passing** | 6 | 0 | 0 |

## What a pass means

Each check combines automated tools with a review of the code and pages against a written checklist. A pass means neither found anything open on the date and commit above. The standards are met as far as those checks can establish: it is a self-assessment, not third-party certification. Automated testing finds a minority of accessibility barriers. Testing with people who use assistive technology is still worth doing, and a change to the explorer needs a re-run.

## Code validity

No open items.

## Code security

### `S-383608` Links built from data do not check the URL scheme

- **Must fix** · found by review · OWASP A05:2025 · ASVS V1
- **Where:** `app.js:267,275,281,298,307; filings.js:208`

```text
o.url, o.pdfs[0], and each coverage and Wikipedia link go into href through esc(), which does not stop a `javascript:` URL. Nothing in the build checks them either: data/coverage.json and data/filings_coverage.json are curated by hand. All current values are http(s).
```

**Recommended fix:** Add to both scripts `const safeUrl = (u) => /^https?:\/\//i.test(u || "") ? u : "#";` and use `esc(safeUrl(x))` at each href listed. Add a test to tests/test_build.py that every `url` in data/coverage.json, data/filings_coverage.json and data/opinions.json (and every entry in `pdfs`) starts with http:// or https://.

### `S-9c46b9` Wayback timestamp reaches the page unescaped and unchecked

- **Must fix** · found by review · OWASP A05:2025 · ASVS V1
- **Where:** `app.js:268-270; build/wayback_opinions.py:83`

```text
via() writes `${ts.slice(0, 4)}-${ts.slice(4, 6)}-${ts.slice(6, 8)}` into innerHTML without esc(). The timestamp is copied from the CDX response (row[0]) with no check. Every committed timestamp is 14 digits, so this is not exploitable today.
```

**Recommended fix:** In app.js:268 change `const ts = wb.timestamp;` to `const ts = esc(wb.timestamp);`. In build/wayback_opinions.py:82 keep a row only when `re.fullmatch(r"\d{14}", row[0])` and `row[1].startswith(("http://", "https://"))`, so a bad CDX row is dropped at build time.

### `S-100ef3` String rendered as markup or code (innerHTML)

- **Must fix** · found by explorer-checks · OWASP A05:2025 · ASVS V1
- **Where:** `app.js:334`

```text
$("list").innerHTML = html || "<p>No opinions match.</p>";

Review: card() escapes nearly every field, and snippet() escapes the CourtListener snippet before restoring only <mark>. But via() (app.js:270) slices `wb.timestamp` into the markup without esc(), and build/wayback_opinions.py:83 copies that timestamp from the CDX response without checking it. All 118 timestamps in the committed data are 14 digits today, so nothing is exploitable now. Links from data are escaped but their scheme is not checked; see the review findings.
```

**Recommended fix:** Trace what reaches this sink. If any part comes from data (archive.org metadata, captured page text, the URL, user input), escape it or build nodes with textContent. Clear it only if every part is a literal or already escaped, and name the escaping function.

### `S-910db1` Every visit is reported to Google Fonts

- **Must fix** · found by review · OWASP ASVS V3
- **Where:** `index.html:8-10; filings.html:8-10`

```text
Both pages load CSS from fonts.googleapis.com and fonts from fonts.gstatic.com. Google learns who visited which page. Neither the page nor the README says so.
```

**Recommended fix:** Serve the two fonts from the explorer: put the woff2 files for Libre Caslon Text (regular, italic) and Special Elite, both under the SIL Open Font License, in fonts/ with the licence. Add @font-face rules with `font-display: swap` to site.css and remove the three <link> lines at index.html:8-10 and filings.html:8-10.

<details><summary>Manual checklist (6 pass, 4 fail, 10 n/a)</summary>

| Item | Result | Note |
|---|---|---|
| No secrets | pass | No secret findings; the CourtListener token is read from COURTLISTENER_TOKEN (build/courtlistener.py:38); .env is gitignored; `git log --all -p` shows no token-shaped strings. |
| Untrusted data is escaped | fail | All 27 innerHTML sinks traced. 26 cleared: esc() (escapes & first, then <>"') or numbers/literals. One fails: wb.timestamp in via(), app.js:270. |
| URLs from data are safe | fail | Wayback and archive.org links use fixed https prefixes and CourtListener paths are checked at build (build_filings.py:56-59), but coverage, Wikipedia, opinion and PDF links are only HTML-escaped, with no scheme check. |
| Harvested data is validated | fail | Partly: build_filings.py checks CourtListener URLs, ia_recap.py matches docket paths with a regex, the harvest checks result counts, and 15 tests pass. wayback_opinions.py writes the CDX timestamp and original unchecked, and the hand-curated coverage files have no check. |
| Third-party code is pinned | pass | No third-party scripts. The only external resource is Google Fonts CSS. |
| No mixed content | pass | Everything loads over https or from the same origin. One coverage link is http, but it is a link, not a load. |
| Dependencies are pinned and maintained | pass | Build is standard-library Python only; no requirements file, package.json or workflows. |
| Dependencies have no known vulnerabilities | pass | No dependencies to audit; no vendored JavaScript. |
| Third parties a visitor's browser contacts | fail | fonts.googleapis.com and fonts.gstatic.com on both pages, not named anywhere. Self-host the fonts. |
| What Pages publishes | pass | Public repository; Pages serves the root, which also publishes build/, tests/, data/sources/ (the workbook CSVs and saved CourtListener responses) and .claude/launch.json. Nothing there is sensitive. |
| Server input is validated | n/a | Static site, no server. |
| Configuration is safe to serve | n/a | Static site. |
| Errors are handled and do not leak | n/a | Static site. The opinions page catches a load failure and says so in #status. |
| Commands built from data | n/a | No subprocess calls. |
| Who can write | n/a | No contributions or uploads. |
| Fetches of submitted URLs | n/a | No submitted URLs. |
| Scope of writes | n/a | No uploads. |
| Limits | n/a | No public queue. |
| Model output is untrusted | n/a | No AI components at runtime. |
| Models are pinned | n/a | No models. |

</details>

<details><summary>Cleared on review (30)</summary>

| Id | Item | Where | Why cleared |
|---|---|---|---|
| `S-8706ef` | String rendered as markup or code (innerHTML) | `app.js:65` | Assigns the empty literal "" to clear the chart before buttons are built with createElement. |
| `S-49e2a5` | String rendered as markup or code (innerHTML) | `app.js:77` | `first` and `last` are numbers (`+years[0]`, `+years[years.length - 1]`); nothing else is interpolated. |
| `S-6291c2` | String rendered as markup or code (innerHTML) | `app.js:89` | drawScale() builds only from numbers: `(v / max) * 100` and `label(v)`, which returns the number or an Intl.NumberFormat string of it. |
| `S-2ed829` | String rendered as markup or code (innerHTML) | `app.js:136` | Empty literal "". |
| `S-cedf54` | String rendered as markup or code (innerHTML) | `app.js:141` | `p` is a key of the literal TILES table (two-letter state codes) and `counts[p]` is a number. |
| `S-c85d42` | String rendered as markup or code (innerHTML) | `app.js:146` | `counts[NATIONWIDE]` is a number and placeName(NATIONWIDE) returns a fixed string. |
| `S-7a3e17` | String rendered as markup or code (innerHTML) | `app.js:160` | Empty literal "". |
| `S-51e943` | String rendered as markup or code (innerHTML) | `app.js:167` | The facet value goes through esc() (app.js:19, replaces & first, then <>"'); `n` and the bar width are numbers. |
| `S-a63475` | String rendered as markup or code (innerHTML) | `app.js:179` | Every interpolated value is an integer from data/filings_by_year.json, which build/merge_sources.py:252 writes as `int(y)` and counts it increments itself; heights are arithmetic on those. Wrapping them in esc() or Number() anyway would keep this safe if the file's source changes. |
| `S-f5bebc` | String rendered as markup or code (innerHTML) | `app.js:186` | Years are integers written by build/merge_sources.py:252; `f.as_of` goes through esc(). |
| `S-2821b7` | String rendered as markup or code (innerHTML) | `app.js:188` | total() sums integer counts from data/filings_by_year.json (merge_sources.py:252) and the rest is literal. |
| `S-86c013` | String rendered as markup or code (innerHTML) | `app.js:222` | `y`, `first`, `last` and `avg` are numbers (`+state.year` coerces the URL value; a non-number gives NaN and the view stays hidden); counts are lengths; type names and month names are literals; square() runs case, court, date and id through esc(). The `focused` value read back is one of the fixed dat |
| `S-fd8619` | String rendered as markup or code (innerHTML) | `app.js:259` | case, court and date each go through esc(). |
| `S-8ab224` | String rendered as markup or code (innerHTML) | `app.js:326` | Two counts (array lengths) and a literal button. |
| `S-442390` | String rendered as markup or code (innerHTML) | `app.js:364` | meta.started, meta.source and each search query go through esc(); the rest is literal. |
| `S-ffd404` | String rendered as markup or code (innerHTML) | `filings.js:87` | Same drawScale() as app.js: numbers only. |
| `S-0e3f6b` | String rendered as markup or code (innerHTML) | `filings.js:101` | Empty literals. |
| `S-5f4397` | String rendered as markup or code (innerHTML) | `filings.js:105` | Empty literal "". |
| `S-cc9444` | String rendered as markup or code (innerHTML) | `filings.js:116` | Heights are arithmetic on counts the page computes itself. |
| `S-97d6a9` | String rendered as markup or code (innerHTML) | `filings.js:122` | `first` and `last` are numbers (`+years[0]`). |
| `S-989984` | String rendered as markup or code (innerHTML) | `filings.js:123` | Literal legend markup. |
| `S-b80216` | String rendered as markup or code (innerHTML) | `filings.js:140` | Empty literal "". |
| `S-3842a5` | String rendered as markup or code (innerHTML) | `filings.js:145` | The facet value goes through esc() (filings.js:29); `n` and the width are numbers. |
| `S-ca52ba` | String rendered as markup or code (innerHTML) | `filings.js:228` | Counts through toLocaleString() on numbers, and a literal button. |
| `S-6929fa` | String rendered as markup or code (innerHTML) | `filings.js:235` | card() and filingRow() run every data field through esc(): case, court, docket, claim, nature, filed, type, description, filer, date, entry. Archive.org links are `${IA}/download/${ia.item}/...` with the fixed https://archive.org prefix, and the committed items and document numbers all match [A-Za-z |
| `S-ac1a56` | String rendered as markup or code (innerHTML) | `filings.js:264` | Counts are numbers (integers in data/filings_ia.json, which build/ia_recap.py computes), `ia.built` goes through esc(), IA is a constant, and the rest is literal. |
| `S-3d8735` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/courtlistener.py:43` | urlopen gets the SEARCH constant (https://www.courtlistener.com/api/rest/v4/search/, courtlistener.py:22) or the API's own `next` link. Suggested hardening, not required: check that `next` starts with SITE before following it, since get() adds the COURTLISTENER_TOKEN header to every request. |
| `S-c397f8` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/ia_recap.py:47` | Every caller builds the URL from the SEARCH constant https://archive.org/advancedsearch.php (ia_recap.py:39). |
| `S-8e3d80` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/recap_text.py:33` | The URL is `ia_text`, which build/recap_harvest.py:68 builds as f"{IA}/{item}/{name}_djvu.txt" from the https://archive.org constant. |
| `S-133762` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/wayback_opinions.py:58` | The URL is the CDX constant https://web.archive.org/cdx/search/cdx (wayback_opinions.py:28) with urlencoded parameters. |

</details>

## Accessibility (WCAG 2.2 AA)

### `A-49888d` Page scrolls sideways at 320 px wide

- **Must fix** · found by explorer-checks · WCAG 1.4.10
- **Where:** `/`

```text
32px wider than the viewport

Review: Confirmed in the browser at 320 px: the overflow is the RECAP filings chart (#filings-chart), whose columns are `flex: 1 0 10px` with nothing to contain them. The fix: in index.html add `overflow-x: auto;` to the #filings-chart rule, as #chart already has.
```

**Recommended fix:** Let content wrap at narrow widths: max-width:100% on media and tables in a scrolling container, no fixed widths over 320px. Data tables may scroll inside their own container.

### `A-17ab2d` Elements must have their visible text as part of their accessible name

- **Must fix** · found by axe-core 4.14.0 · WCAG 2.5.3
- **Where:** `/ label-content-name-mismatch`

```text
52 element(s): button[data-place="AK"]; button[data-place="ME"]; button[data-place="VT"]; button[data-place="NH"]; button[data-place="WA"]
Fix any of the following:
  Text inside the element is not included in the accessible name

Review: Confirmed. A tile shows "AK" and its count but is named "Alaska: 3 opinions" (app.js:122-123), so a speech-input user saying "click AK" gets nothing. The fix: start the name with what is shown, e.g. aria-label `AK 3, Alaska: 3 opinions` built from `${p} ${n || ""}` + the current label. For the Nationwide button, drop its aria-label (its visible text, app.js:146, already says what it is). Then re-run axe.
```

**Recommended fix:** Ensure that elements labelled through their content must have their visible text as part of their accessible name See https://dequeuniversity.com/rules/axe/4.14/label-content-name-mismatch?application=axeAPI

### `A-c52fb3` All touch targets must be 24px large, or leave sufficient space

- **Must fix** · found by axe-core 4.14.0 · WCAG 2.5.8
- **Where:** `/ target-size`

```text
9 element(s): button[data-id="10698385"]; button[data-id="4876765"]; button[data-id="5299393"]; button[data-id="10818694"]; button[data-id="10818693"]
Fix any of the following:
  Target has insufficient size (14px by 14px, should be at least 24px by 24px)
  Target has insufficient space to its closest neighbors. Safe clickable space has a diameter of 8px instead of at least 24px.

Review: Confirmed. The year view's squares are 14 px with 2 px gaps (index.html .sq and #months div), and 10 px below 480 px. The fix: in index.html set `#months div { gap: 10px; }` so square centres are 24 px apart, and remove the `.sq { width: 10px; height: 10px; }` override in the max-width:480px rule.
```

**Recommended fix:** Ensure touch targets have sufficient size and space See https://dequeuniversity.com/rules/axe/4.14/target-size?application=axeAPI

### `A-752c97` Keyboard focus is lost to the top of the page after picking a year or a filings filter

- **Must fix** · found by review · WCAG 2.4.3
- **Where:** `app.js:65-76; filings.js:105-121, 140-149, 228-232`

```text
Checked in the browser: pressing Enter on a year bar (opinions page) or a Circuit button (filings page) rebuilds the buttons, and focus goes to <body>, so the next Tab starts again at the top of the page. "Clear filters" does the same. The map and the opinions page's facets already put focus back (app.js:134, 148, 158, 171).
```

**Recommended fix:** Do what drawFacet() in app.js does. In each drawChart(), set `b.dataset.year = y` and, before clearing, read `const focused = document.activeElement?.dataset?.year`; after the loop, `if (focused) chart.querySelector(`[data-year="${focused}"]`)?.focus()`. In filings.js drawFacet(), set `b.dataset.facet = field; b.dataset.value = v` and restore focus as app.js:158 and 171 do. After "clear filters", call `$("q").focus()`.

### `A-176c0d` In the year view, court type is shown by colour alone

- **Must fix** · found by review · WCAG 1.4.1
- **Where:** `index.html (.sq, #yearview .federal/.state/.tribunal); app.js:216-218`

```text
Each square is blue, orange or grey for federal, state or tribunal, with no other visual cue, and its accessible name gives the court but not the type. The key gives counts only.
```

**Recommended fix:** Add a shape cue in index.html: `#yearview .sq.state, #yearview .key i.state { border-radius: 50%; }` and `#yearview .sq.tribunal, #yearview .key i.tribunal { border-radius: 0; transform: rotate(45deg) scale(.8); }`. In app.js:217 add the type to the name: `esc(`${o.case}, ${o.court} (${COURT_TYPES[courtType(o)]}), ${o.date}`)`.

### `A-a0fb70` A selected filter button looks the same with and without focus

- **Must fix** · found by review · WCAG 2.4.7
- **Where:** `site.css:71; index.html (#map button.on, #nationwide button.on)`

```text
Checked in the browser by tabbing to the selected California tile: `#map button.on` and `.facet button.on` set a 2px ink outline that is more specific than `:focus-visible` (site.css:55), so the focus ring never shows on a pressed button. The computed outline is identical focused and unfocused.
```

**Recommended fix:** In site.css after line 71 add `.facet button.on:focus-visible, #map button.on:focus-visible, #nationwide button.on:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }`.

<details><summary>Manual checklist (17 pass, 4 fail, 1 n/a)</summary>

| Item | Result | Note |
|---|---|---|
| 1.1.1 Non-text content | pass | The portrait has descriptive alt text. Each chart bar is a button or role=img element named with its year and counts; map tiles and year-view squares are named. The ▶ marker in filings summaries is read aloud as text; aria-hidden="true" on .turn would be tidier. |
| 1.3.1 Info and relationships | pass | One h1, h2 per section and year, h3 per card, h4 for press. Filter groups are role=group with aria-label or aria-labelledby to a heading. Lists are lists. |
| 1.3.2 Meaningful sequence | pass | DOM order matches reading order; the grid map is laid out with grid-row/column but read in TILES order, which is fine for a set of buttons. |
| 1.4.1 Use of color | fail | Year-view squares distinguish court type by colour only. Selected filters have an outline as well as colour, and the stacked filings bars differ in lightness (about 3.4:1) and are labelled. |
| 1.4.11 Non-text contrast | pass | Bars 3.29:1 (--bar) and 11.2:1 (--bar-on) on the pad; year squares 3.56 to 5.67:1; focus ring 7.23:1; search box border 6.8:1. Select borders (--line) are only 1.59:1, but the native arrow and text identify them. |
| 1.4.4 Resize text / 1.4.12 Text spacing | pass | Both pages at 640 px wide (200% of 1280) with the WCAG text-spacing overrides applied: no clipped text and no sideways scroll. The 320 px overflow is recorded under reflow (A-49888d). |
| 2.4.4 Link purpose | pass | "court PDF", "CourtListener", "Wayback Machine" and "document on archive.org" sit inside a card headed by the case name, which gives their purpose in context. |
| 2.4.6 Headings and labels | pass | Headings name their sections; selects are named "Court", "Phrase matched" and "Who filed it". |
| 3.1.1 Language of page | pass | lang="en" on both pages; content is English. |
| 2.1.1 Keyboard | pass | Every control is a native button, link, select, input or summary. Year-view hover text also appears on focus (focusin). |
| 2.1.2 No keyboard trap | pass | No modals or embedded players; focus moves freely. |
| 2.4.1 Bypass blocks | pass | No skip link, but main and nav landmarks are present. The footer sits inside main, so it is not a contentinfo landmark; moving it out would be tidier. |
| 2.4.3 Focus order | fail | Focus goes to <body> after activating a year bar (both pages), a filings-page facet, or "clear filters". |
| 2.4.7 Focus visible | fail | The global :focus-visible ring is clear (2px accent), but selected (aria-pressed) facet and map buttons show the same outline focused and unfocused. |
| 2.4.11 Focus not obscured | pass | Nothing sticky or fixed. |
| 2.5.8 Target size | fail | Year-view squares are 14 px (10 px on narrow screens) with 2 px gaps (A-c52fb3). The year bars are 10 px wide at 320 px but 140 px tall and scroll in their own container. |
| 2.2.2 Pause, stop, hide | pass | Nothing moves except a 1.5 s highlight on a card. |
| 3.2.2 On input | pass | Changing a select or typing filters the list in place; the URL is updated with replaceState, not navigation. |
| 3.3.2 Labels or instructions | pass | The search box has a visible <label>. The selects have no visible label, but each shows its purpose in its first option ("All courts", "Any phrase", "Filed by anyone"); a visible label would be clearer, especially once a phrase is selected. |
| 4.1.2 Name, role, value | pass | Toggle buttons expose aria-pressed in step with .on; filings dockets use native details/summary. |
| 4.1.3 Status messages | pass | #status and #searchcount are aria-live="polite" on both pages and announce result counts without moving focus. |
| 1.2.2 Captions | n/a | No audio or video. |

</details>

<details><summary>Cleared on review (5)</summary>

| Id | Item | Where | Why cleared |
|---|---|---|---|
| `A-6c64c1` | Elements must meet minimum color contrast ratio thresholds | `/ color-contrast` | The "gradient" is the pad's 1px rule lines (--rule #c3d6e4) every 32px over --bg #fcf3b8. Computed against both: ink 13.06:1 and 9.85:1, muted 6.16:1 and 4.64:1, accent 7.23:1 and 5.45:1. All at least 4.5:1. |
| `A-b78730` | Elements must have their visible text as part of their accessible name | `/ label-content-name-mismatch` | The year view's close button shows only "×", a symbol rather than text, and is named "Close 2021". 2.5.3 does not apply to symbolic characters. |
| `A-cae34d` | Elements must meet minimum color contrast ratio thresholds (dark mode) | `/ color-contrast (dark mode)` | Dark mode changes only the desk colours (--desk, --lamp, --binding, site.css:19-22); the pad keeps --bg and --rule, so the ratios are the same as in light mode: muted text 4.64:1 at worst. |
| `A-0d4c3c` | Elements must meet minimum color contrast ratio thresholds | `/filings.html color-contrast` | Same pad background and palette as the opinions page (site.css): muted text 4.64:1 at worst against the rule lines. |
| `A-66e24a` | Elements must meet minimum color contrast ratio thresholds (dark mode) | `/filings.html color-contrast (dark mode)` | Dark mode changes only the desk; the pad and its text colours are unchanged. |

</details>

## Advisory (7)

Optional. These items never block a pass.

| Id | Check | Item | Where | Reference | Suggestion |
|---|---|---|---|---|---|
| `V-667718` | validity | Do not assign a `lambda` expression, use a `def` | `build/merge_sources.py:210` |  | Rewrite `count` as a `def` |
| `S-46b447` | security | No content-security-policy header | `https://internetarchivecanada.github.io/legal-opinions-using-wayback/` | A02:2025 · ASVS V3 | Set it; it limits the damage of any XSS that gets through; a <meta http-equiv> CSP works on static hosts. |
| `S-09212f` | security | No x-content-type-options header | `https://internetarchivecanada.github.io/legal-opinions-using-wayback/` | A02:2025 · ASVS V3 | Set it; it stops browsers guessing content types. It has no <meta> form, so on a host that cannot set headers (GitHub Pages) it stays open; the explorer's owners decide whether that matters enough to change host. |
| `S-36c938` | security | Page contacts a third party: fonts.googleapis.com | `/` | ASVS V3 | Every visitor's IP address and the page they are on go to this host. Serve the file from the explorer itself (fonts and libraries can be vendored), or keep it and say so in the review. |
| `S-21f485` | security | Page contacts a third party: fonts.gstatic.com | `/` | ASVS V3 | Every visitor's IP address and the page they are on go to this host. Serve the file from the explorer itself (fonts and libraries can be vendored), or keep it and say so in the review. |
| `S-aee3d4` | security | Page contacts a third party: fonts.googleapis.com | `/filings.html` | ASVS V3 | Every visitor's IP address and the page they are on go to this host. Serve the file from the explorer itself (fonts and libraries can be vendored), or keep it and say so in the review. |
| `S-e3e83c` | security | Page contacts a third party: fonts.gstatic.com | `/filings.html` | ASVS V3 | Every visitor's IP address and the page they are on go to this host. Serve the file from the explorer itself (fonts and libraries can be vendored), or keep it and say so in the review. |

<!-- explorer-checks:state {"passing": false, "date": "2026-11-05", "commit": "3c4b6efc9d12e830d24cc4bd3ef7bd74791fb34c", "open": ["A-176c0d", "A-17ab2d", "A-49888d", "A-752c97", "A-a0fb70", "A-c52fb3", "S-100ef3", "S-383608", "S-910db1", "S-9c46b9"], "titles": {"S-100ef3": "String rendered as markup or code (innerHTML)", "A-17ab2d": "Elements must have their visible text as part of their accessible name", "A-c52fb3": "All touch targets must be 24px large, or leave sufficient space", "A-49888d": "Page scrolls sideways at 320 px wide", "S-9c46b9": "Wayback timestamp reaches the page unescaped and unchecked", "S-383608": "Links built from data do not check the URL scheme", "S-910db1": "Every visit is reported to Google Fonts", "A-752c97": "Keyboard focus is lost to the top of the page after picking a year or a filings filter", "A-a0fb70": "A selected filter button looks the same with and without focus", "A-176c0d": "In the year view, court type is shown by colour alone"}} -->
